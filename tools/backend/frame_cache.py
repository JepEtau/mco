from __future__ import annotations
import os
import subprocess
import sys
import numpy as np

from collections import OrderedDict
from pprint import pprint

from .dsr_database import DsrDatabase
from .replace_database import ReplaceDatabase
from .warp_database import WarpDatabase
from utils.mco_types import Scene
from utils.media import VideoInfo, extract_media_info_mco, frame_rate_dec
from utils.p_print import lightcyan, red, yellow
from utils.path_utils import path_split
from utils.tools import ffmpeg_exe
from utils.time_conversions import (
    frame_to_s,
    frame_to_sexagesimal,
)
from parsers import (
    db,
    get_frame_rate,
    VideoSettings,
)
from ._types import Frame
from PySide6.QtWidgets import QApplication


class FrameCache:

    def __init__(
        self,
        replace_db: ReplaceDatabase | None = None,
        dsr_db: DsrDatabase | None = None,
        warp_db: WarpDatabase | None = None,
    ):
        super().__init__()
        self.scenes: OrderedDict[str, list[Frame]] = {}
        self.frame_count: int = 0
        self.scene_keys: list[str] = []

        self.video_infos: dict[str, VideoInfo] = {}
        self.replace_db: ReplaceDatabase | None = replace_db
        self.dsr_db: DsrDatabase | None = dsr_db
        self.warp_db: DsrDatabase | None = warp_db


    @staticmethod
    def _key(scene: Scene) -> str:
        k_ep_dst: str = scene['dst']['k_ep']
        return f"{k_ep_dst if k_ep_dst else 'ep00'}:{scene['dst']['k_ch']}:{scene['no']:03}"


    def get(self, scene: Scene) -> list[Frame] | None:
        # Extract frames from input video and strore them here
        scene_key: str = self._key(scene)
        task_name: str = scene['task'].name

        if scene_key not in self.scenes:
            while self.frame_count > 800:
                k = self.scene_keys.pop(0)
                self.frame_count -= len(self.scenes[k])
                del self.scenes[k]

            self.scenes[scene_key] = []

            frame_rate: float = get_frame_rate()

            total_count = scene['src'].frame_count()
            for src_scene in scene['src'].scenes():
                print(lightcyan(f"extract {total_count} frames from: {src_scene['k_ed_ep_ch_no']}"))
                src_start: int = src_scene.start - src_scene.in_scene['inputs'].progressive().start
                start: int = 0
                in_video_fp: str = scene['task'].in_video_file
                in_video_fp = (
                    src_scene.in_scene['inputs'].progressive().filepath
                    if not in_video_fp
                    else in_video_fp
                )

                if task_name in ('initial', 'lr'):
                    # Do not use FFv1 because slow to decode
                    in_video_fp = src_scene.in_scene['inputs'].progressive().filepath
                    directory, basename, extension = path_split(in_video_fp)
                    in_video_fp = os.path.join(directory, f"{basename}{extension}")
                    start = src_start

                if task_name in ('upscale', 'hr', 'tf'):
                    in_video_fp: str = scene['task'].video_file

                if not os.path.exists(in_video_fp):
                    if task_name == 'st':
                        in_video_fp = scene['task'].fallback_in_video_files['hr']
                    print(yellow(f"{in_video_fp} does not exist, fallback to"), in_video_fp)

                print(f"  segment: {in_video_fp}, {start}, {src_scene.count}")
                if not os.path.exists(in_video_fp):
                    raise ValueError(red(f"frame cache: missing {in_video_fp}"))

                if in_video_fp not in self.video_infos:
                    # fp = src_scene['scene']['inputs'].progressive().filepath
                    # specific to lr task: use a h264 video rather than the deinterlaced one
                    # if scene['task'].name == 'lr':

                    self.video_infos[in_video_fp] = extract_media_info_mco(in_video_fp)['video']
                vi: VideoInfo = self.video_infos[in_video_fp]
                frame_rate: float = frame_rate_dec(vi['frame_rate_r'])
                # pprint(vi)
                # print(red(frame_rate))
                # raise
                filter_complex: list[str] = []
                in_h, in_w, in_c = vi['shape']

                print(red("TODO: use task_name \'dsr\' in frame cache"))
                hr_vsettings: VideoSettings = db['vsettings']['hr']
                pad: int = hr_vsettings.pad

                # Use screen dimension to fit to screen
                screen_size = QApplication.screens()[0].size()
                screen_height, screen_width = screen_size.height(), screen_size.width()

                if task_name in ('lr', 'initial') and self.replace_db is not None:
                    if screen_height < 1440:
                        # screen is too small, resize to fit
                        in_w, in_h = 1280, 960
                        # in_w, in_h = 1152, 864

                    else:
                        # in_w, in_h = 1440, 1080
                        in_w, in_h = 1536, 1152
                    # in_h, in_w = 1152, 1536
                    filter_complex = [
                        "-filter_complex",
                        f"[0:v]scale={in_w}:{in_h}:sws_flags=lanczos+accurate_rnd+bitexact+full_chroma_int[outv]",
                        "-map", "[outv]"
                    ]

                if task_name in ('hr', 'tf'):
                    in_h, in_w = int(in_h - 2 * pad), int(in_w - 2 * pad)
                    filters: list[str] = [f"crop={in_w}:{in_h}:{pad}:{pad}"]

                    if screen_height < 1440:
                        # screen is too small, resize to fit
                        in_w, in_h = 1152, 864
                        print(yellow(f"FrameCache: screen is too small, resize to {in_w}x{in_h}"))
                        filters.append(
                            f"scale={in_w}:{in_h}:sws_flags=lanczos+accurate_rnd+bitexact+full_chroma_int"
                        )

                    else:
                        if in_h != 1080 or in_w != 1440:
                            print(yellow(f"FrameCache: rescale {in_w}x{in_h} to 1440, 1080"))
                            in_w, in_h = 1440, 1080
                            filters.append(
                                f"scale={in_w}:{in_h}:sws_flags=lanczos+accurate_rnd+bitexact+full_chroma_int"
                            )
                    filter_complex = [
                        "-filter_complex",
                        f"[0:v]{','.join(filters)}[outv]",
                        "-map", "[outv]"
                    ]

                # elif in_h < 1080:
                #     # raise ValueError(" < 1080p")
                #     # # pprint( db['vsettings'])
                #     # # sys.exit()
                #     pad: int = db['vsettings']['hr'].pad
                #     pad_filter: str = f"pad=w=iw+{2*pad}:h={2*pad}+ih:x={pad}:y={pad}:color=black"
                #     filter_complex = [
                #         "-filter_complex",
                #         clean_ffmpeg_filter(
                #             f"""[0:v]
                #                 scale={2*in_w}:{2*in_h}:sws_flags=lanczos+accurate_rnd+bitexact+full_chroma_int,
                #                 {pad_filter}
                #             [outv]
                #             """
                #         ),
                #         "-map", "[outv]"
                #     ]
                #     in_h, in_w = 2 * (in_h + pad), 2 * (in_w + pad)

                scene_count = src_scene.count
                if scene['dst']['k_ch'] == 'g_asuivre':
                    scene_count = scene['dst']['count']

                xtract_command: list[str] = [
                    ffmpeg_exe,
                    "-hide_banner",
                    "-loglevel", "warning",
                    "-nostats",
                    "-ss",
                    str(frame_to_sexagesimal(no=start,frame_rate=frame_rate)),
                    "-i", in_video_fp,
                    "-t", str(frame_to_s(no=scene_count, frame_rate=frame_rate)),
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
                pipe_in_shape = (in_h, in_w, in_c)
                in_dtype = np.uint8
                src_scene_key: str = f"{':'.join(src_scene['k_ed_ep_ch_no'][:-1])}:{src_scene['k_ed_ep_ch_no'][-1]:03}"
                for i in range(scene_count):
                    img: np.ndarray = np.frombuffer(
                        self.sub_process.stdout.read(pipe_img_nbytes),
                        dtype=in_dtype,
                    ).reshape(pipe_in_shape)
                    f_no = src_start + src_scene.in_scene['inputs'].progressive().start + i
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
                            ),
                            dsr=(
                                self.dsr_db.get(src_scene=src_scene, f_no=f_no)
                                if self.dsr_db is not None
                                else None
                            ),
                        )
                    )
                # Convert the 1st image of the scene to fasten the display
                np_img: np.ndarray = self.scenes[scene_key][0].img
                self.scenes[scene_key][0].img = np_img

                self.frame_count += scene_count
                self.scene_keys.append(scene_key)
                print(f"Number of frames in cache: {self.frame_count}")

        return self.scenes[scene_key]


    def flush(self) -> None:
        """Flush all frames to force extraction, used to update the cache with latest
        upscaled frames
        """
