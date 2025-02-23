from dataclasses import dataclass
import numpy as np
from pprint import pprint
from queue import Queue
from threading import Event
import torch
from torch import Tensor
from nn_inference.resource_mgr import NnFrame, BaseThread
from nn_inference.toolbox.dh_transfers import dtoh_transfer
from utils.images_io import write_image
from typing import Callable
from utils.p_print import *
from nn_inference.model_mgr import ModelManager
from pynnlib import (
    tensor_to_img,
)

@dataclass(slots=True)
class ImgWriterThreadConfig:
    model_manager: ModelManager



class ImgWriterThread(BaseThread):
    def __init__(
        self,
        config: ImgWriterThreadConfig,
    ) -> None:
        super().__init__()
        self._stop_event: Event = Event()

        self.in_queue: Queue = Queue(4)
        self.config = config
        self._written: int = 0
        self.callback: Callable = None
        print(purple("[V][W] Init ImgWriterThread"))
        pprint(config['dtoh_mem'])
        self.model_manager = config.model_manager



    def run(self) -> None:
        verbose: bool = False
        cuda_stream = self.model_manager.dtoh_cuda_stream
        htod_mem: Tensor = self.model_manager.dtoh_host_mem


        in_queue: Queue = self.in_queue

        # Default settings
        img_dtype: np.dtype = np.uint8
        flip_r_b: bool = True

        if verbose:
            print(purple("[V][E] Image writer, config:"))

        self._written: int = 0
        with torch.cuda.stream(cuda_stream):
            while not self._stop_event.is_set():
                # Wait for a frame or a poison pill
                input = in_queue.get(block=True)
                if input is None or self._stop_event.is_set():
                    if verbose:
                        print(purple("[V][E] Received Null tensor"))
                    break

                frame: NnFrame = input
                d_img: torch.tensor = tensor_to_img(
                    tensor=frame.tensor,
                    img_dtype=img_dtype,
                    flip_r_b=flip_r_b,
                )
                out_img: np.ndarray = dtoh_transfer(
                    host_mem=htod_mem,
                    d_img=d_img,
                    cuda_stream=cuda_stream,
                )

                del frame.tensor
                write_image(f"out_{frame.f_no:05}.png", out_img)

                if self.progress_thread is not None:
                    self.progress_thread.put(1)
                self._written += 0


    def stop(self, force: bool=False) -> None:
        self._stop_event.set()
        if force:
            while not self.in_queue.empty():
                self.in_queue.get_nowait()
        self.put_frame(None)
        self._processing = False


    def put_frame(self, frame: NnFrame) -> bool:
        if self._processing:
            self.in_queue.put(frame)
        return True


    @property
    def encoded(self) -> int:
        return self._written


    def set_progress_callback(self, function: Callable) -> None:
        self.callback = function
