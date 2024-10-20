from __future__ import annotations
import os
import subprocess
import sys
import numpy as np

from collections import OrderedDict
from pprint import pprint

from tools.backend.replace_database import ReplaceDatabase
from utils.mco_types import Scene
from utils.media import VideoInfo, extract_media_info
from utils.p_print import lightcyan, red, yellow
from utils.path_utils import path_split
from utils.tools import ffmpeg_exe
from utils.time_conversions import (
    frame_to_s,
    frame_to_sexagesimal,
)
from parsers import (
    db,
    get_fps,
    VideoSettings,
    clean_ffmpeg_filter,
)
from ._types import Frame



class FrameCache:

    def __init__(
        self,
        replace_db: ReplaceDatabase | None = None,
    ):
        super().__init__()
        self.scenes: OrderedDict[str, list[Frame]] = {}
        self.frame_count: int = 0

        self.video_infos: dict[str, VideoInfo] = {}
        self.replace_db: ReplaceDatabase | None = replace_db


    @staticmethod
    def _key(scene: Scene) -> str:
        k_ep_dst: str = scene['dst']['k_ep']
        return f"{k_ep_dst if k_ep_dst else 'ep00'}:{scene['dst']['k_ch']}:{scene['no']:03}"


    def get(self, scene: Scene) -> list[Frame] | None:
        # Extract frames from input video and strore them here
        scene_key: str = self._key(scene)
        task_name: str = scene['task'].name

        if scene_key not in self.scenes:
            self.scenes[scene_key] = []

            frame_rate: float = get_fps(db)

            total_count = scene['src'].frame_count()
            for src_scene in scene['src'].scenes():
                print(lightcyan(f"extract {total_count} frames from: {src_scene['k_ed_ep_ch_no']}"))
                count = src_scene['count']
                src_start: int = src_scene['start'] - src_scene['scene']['inputs']['progressive']['start']
                start: int = 0
                in_video_fp: str = scene['task'].video_file

                if task_name == 'lr':
                    # Do not use FFv1 because slow to decode
                    in_video_fp = src_scene['scene']['inputs']['progressive']['filepath']
                    directory, basename, extension = path_split(in_video_fp)
                    in_video_fp = os.path.join(directory, f"{basename}_h264{extension}")
                    start = src_start

                if not os.path.exists(in_video_fp):
                    print(yellow(f"{in_video_fp} does not exist, fallback..."))
                    if task_name == 'st':
                        in_video_fp = scene['task'].fallback_in_video_files['hr']
                if not os.path.exists(in_video_fp):
                    sys.exit(red(f"missing {in_video_fp}"))


                print(f"  segment: {in_video_fp}, {start}, {count}")

                if in_video_fp not in self.video_infos:
                    # fp = src_scene['scene']['inputs']['progressive']['filepath']
                    # specific to lr task: use a h264 video rather than the deinterlaced one
                    # if scene['task'].name == 'lr':

                    self.video_infos[in_video_fp] = extract_media_info(in_video_fp)['video']
                vi: VideoInfo = self.video_infos[in_video_fp]
                # print(red(fp))
                # pprint(vi)
                # sys.exit()
                filter_complex: list[str] = []
                in_h, in_w, in_c = vi['shape']
                if task_name == 'lr' and self.replace_db is not None:
                    print("low resolution, resize to 4:3")
                    if in_h != 576 or in_w != 768:
                        in_h, in_w = (576, 768)
                        filter_complex = [
                            "-filter_complex",
                            f"[0:v]scale={in_w}:{in_h}:sws_flags=lanczos+accurate_rnd+bitexact+full_chroma_int[outv]",
                            "-map", "[outv]"
                        ]
                elif in_h < 1080:
                    # pprint( db['common']['video_format'])
                    # sys.exit()
                    video_settings: VideoSettings = db['common']['video_format']['hr']
                    pad: int = video_settings.pad
                    pad_filter: str = f"pad=w=iw+{2*pad}:h={2*pad}+ih:x={pad}:y={pad}:color=black"
                    filter_complex = [
                        "-filter_complex",
                        clean_ffmpeg_filter(
                            f"""[0:v]
                                scale={2*in_w}:{2*in_h}:sws_flags=lanczos+accurate_rnd+bitexact+full_chroma_int,
                                {pad_filter}
                            [outv]
                            """
                        ),
                        "-map", "[outv]"
                    ]
                    in_h, in_w = 2 * (in_h + pad), 2 * (in_w + pad)

                xtract_command: list[str] = [
                    ffmpeg_exe,
                    "-hide_banner",
                    "-loglevel", "warning",
                    "-nostats",
                    "-ss",
                    str(frame_to_sexagesimal(no=start,frame_rate=frame_rate)),
                    "-i", in_video_fp,
                    "-t", str(frame_to_s(no=count, frame_rate=frame_rate)),
                    *filter_complex,
                    "-f", "image2pipe",
                    "-pix_fmt", 'bgr24',
                    "-vcodec", "rawvideo",
                    "-"
                ]

                print(' '.join(xtract_command))

                # Open subprocess
                self.sub_process = None
                try:
                    self.sub_process = subprocess.Popen(
                        xtract_command,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                except Exception as e:
                    print(f"[E] Unexpected error: {type(e)}", flush=True)

                # won't work except 8bit videos
                pipe_img_nbytes: int = in_w * in_h * in_c
                shape = (in_h, in_w, in_c)
                in_dtype = np.uint8
                src_scene_key: str = f"{':'.join(src_scene['k_ed_ep_ch_no'][:-1])}:{src_scene['k_ed_ep_ch_no'][-1]:03}"
                for i in range(count):
                    img: np.ndarray = np.frombuffer(
                        self.sub_process.stdout.read(pipe_img_nbytes),
                        dtype=in_dtype,
                    ).reshape(shape)
                    f_no = src_start + src_scene['scene']['inputs']['progressive']['start'] + i
                    self.scenes[scene_key].append(
                        Frame(
                            i=i,
                            src_scene_key=src_scene_key,
                            scene_key=scene_key,
                            no=f_no,
                            img=img,
                            by=(
                                self.replace_db.get(src_scene=src_scene, f_no=f_no)
                                if self.replace_db is not None
                                else -1
                            )
                        )
                    )
                # Convert the 1st image of the scene to fasten the display
                np_img: np.ndarray = self.scenes[scene_key][0].img
                h, w, c = np_img.shape
                # self.scenes[scene_key][0].pixmap = QPixmap().fromImage(
                #     QImage(np_img, w, h, w * c, QImage.Format.Format_BGR888)
                # )
                self.scenes[scene_key][0].img = np_img

        return self.scenes[scene_key]

    # def __getitem__(self, key: Any) -> Any:
    #     if self.verbose:
    #         print(f"ImageCache: GET {key}")
    #     item = super().__getitem__(key)
    #     if item is not None:
    #         if self.verbose:
    #             print(f"try removing {key}: {self.occurences[key]}")
    #         self.occurences[key] -= 1
    #         if self.occurences[key] <= 0:
    #             del self.occurences[key]
    #             del self.data[key]
    #             if self.verbose:
    #                 print("\tDelete item from cache")
    #     elif self.verbose:
    #         print(f"ImageCache: not in cache")
    #     return item


    # def __setitem__(self, key: Any, item: Any) -> None:
    #     if self.verbose:
    #         print(f"ImageCache: SET {key}")
    #     if key in self.exceptions:
    #         if self.verbose:
    #             print("\tnot cacheable, discard")
    #         return
    #     if key not in self.occurences:
    #         if self.verbose:
    #             print(f"set occurence of {key}")
    #         self.occurences[key] = 1
    #     else:
    #         self.occurences[key] += 1
    #         if self.verbose:
    #             print(f"add occurence of {key} -> {self.occurences[key]}")
    #     return super().__setitem__(key, item)


    # def set_occurences(self, occurences: Counter)  -> None:
    #     self.occurences = occurences
    #     if self.verbose:
    #         pprint(self.occurences)


    # def set_exceptions(self, exceptions: set | list) -> None:
    #     """Do not cache some items"""
    #     if isinstance(exceptions, set):
    #         self.exceptions = exceptions
    #     else:
    #         self.exceptions = set(exceptions)


    # def add(self, key: Any, item: Any, set_occurence: bool = True) -> None:
    #     """Add an item to the cache.
    #         if set_occurence is False, the nb of occurences
    #         is not modified.
    #         This boolen is used by the ReplaceNode to not count
    #         an additionnal occurence if an item is put in cache while
    #         used
    #     """
    #     self.__setitem__(key, item)
    #     if not set_occurence:
    #         self.occurences[key] -= 1
