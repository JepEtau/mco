from collections import deque
from dataclasses import dataclass
from typing import Any
from nn_inference.img_dim import get_image_shape
from nn_inference.threads.common import Frame
from pynnlib import (
    NnModelSession,
    NnModel,
)


@dataclass
class ImageReaderParams:
    size: tuple[int, int] | None = None
    resize_algo: str = ''



class UpscalePipeline(object):
    def __init__(
        self,
        frames: list[Frame],
        device: str,
        fp16: bool,
        max_in_size: tuple[int, int] | None = None,
        debug: bool = False
    ) -> None:

        # Decoder
        # ImageReaderParams
        max_nbytes: int = 0
        max_shape: tuple[int] = (0,0,0)
        for f in frames:
            shape, nbytes = get_image_shape(f.in_img_fp)
            if nbytes > max_nbytes:
                max_nbytes = nbytes
                max_shape = shape
        print(f"{max_nbytes} bytes, with shape: {max_shape}")
