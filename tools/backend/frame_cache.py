from __future__ import annotations
from dataclasses import dataclass
import math
import subprocess

import numpy as np
from import_parsers import *

from collections import Counter, OrderedDict, UserDict
from pprint import pprint
from typing import Any

from tools.backend.replace_database import ReplaceDatabase
from utils.mco_types import Scene
from utils.media import VideoInfo, extract_media_info
from utils.path_utils import path_split
from utils.tools import ffmpeg_exe
from utils.time_conversions import (
    FrameRate,
    frame_to_s,
    frame_to_sexagesimal,
)
from parsers import (
    db,
    get_fps,
)

@dataclass(slots=True)
class Frame:
    key: str
    i: int
    no: int
    by: int
    img: np.ndarray


class FrameCache:

    def __init__(
        self,
        replace_db: ReplaceDatabase | None = None,
        verbose: bool = False
    ):
        super().__init__()
        # self.occurences: Counter = Counter()
        # self.exceptions: set = set()
        self.verbose: bool = verbose

        self.scenes: OrderedDict[str, list[Frame]] = {}
        self.frame_count: int = 0

        self.video_infos: dict[str, VideoInfo] = {}
        self.replace_db: ReplaceDatabase | None = replace_db

    @staticmethod
    def _key(scene: Scene) -> str:
        return f"{scene['dst']['k_ep']}:{scene['dst']['k_ch']}:{scene['no']}"


    def get(self, scene: Scene) -> list:
        # Extract frames from input video and strore them here
        key = self._key(scene)

        if key not in self.scenes:
            self.scenes[key] = []

            frame_rate: float = get_fps(db)

            total_count = scene['src'].frame_count()
            for src_scene in scene['src'].scenes():
                print(f"extract {total_count} frames from: {src_scene['k_ed_ep_ch_no']}")
                start = src_scene['start']
                count = src_scene['count']
                in_video_fp: str = src_scene['scene']['inputs']['progressive']['filepath']
                directory, basename, extension = path_split(in_video_fp)
                in_video_fp = os.path.join(directory, f"{basename}_h264{extension}")
                print(f"  segment: {in_video_fp}, {start}, {count}")

                if in_video_fp not in self.video_infos:
                    self.video_infos[in_video_fp] = extract_media_info(
                        src_scene['scene']['inputs']['progressive']['filepath']
                    )['video']
                vi: VideoInfo = self.video_infos[in_video_fp]

                xtract_command: list[str] = [
                    ffmpeg_exe,
                    "-hide_banner",
                    "-loglevel", "warning",
                    "-nostats",
                    "-ss",
                    str(frame_to_sexagesimal(no=start,frame_rate=frame_rate)),
                    "-i", in_video_fp,
                    "-t", str(frame_to_s(no=count, frame_rate=frame_rate)),
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
                pipe_img_nbytes: int = math.prod(vi['shape'])
                shape = vi['shape']
                in_dtype = np.uint8
                src_scene_key: str = f"{':'.join(src_scene['k_ed_ep_ch_no'][:-1])}:{src_scene['k_ed_ep_ch_no'][-1]:03}"
                for i in range(count):
                    img: np.ndarray = np.frombuffer(
                        self.sub_process.stdout.read(pipe_img_nbytes),
                        dtype=in_dtype,
                    ).reshape(shape)
                    f_no = start + i
                    self.scenes[key].append(
                        Frame(
                            i=i,
                            key=src_scene_key,
                            no=f_no,
                            img=img,
                            by=(
                                self.replace_db.get(src_scene=src_scene, f_no=f_no)
                                if self.replace_db is not None
                                else -1
                            )
                        )
                    )
                # pprint(self.sub_process.stderr.read())


        return self.scenes[key]

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
