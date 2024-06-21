from collections import deque
from dataclasses import dataclass
from typing import Any
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
        img_queue: deque,
        device: str,
        fp16: bool,
        max_in_size: tuple[int, int] | None = None,
        debug: bool = False
    ) -> None:

        # Decoder
        ImageReaderParams

