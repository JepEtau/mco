from __future__ import annotations
from dataclasses import dataclass
import queue
from queue import Queue
from threading import Event
from typing import Literal
from utils.p_print import *

from nn_inference.model_mgr import ModelManager
from nn_inference.pytorch.inference import perform_torch_inference
from nn_inference.resource_mgr import NnFrame, BaseThread
from nn_inference.threads.t_decoder import DecoderThread
from nn_inference.threads.t_encoder import EncoderThread
from pynnlib import (
    is_cuda_available,
    is_tensorrt_available,
)



@dataclass
class InferenceThreadConfig:
    execution_provider: Literal['cuda', 'trt']
    d_thread: DecoderThread
    e_thread: EncoderThread
    model_manager: ModelManager
    channels_last: bool = False



class InferenceThread(BaseThread):
    def __init__(
        self,
        config: InferenceThreadConfig
    ) -> None:
        super().__init__()
        self._stop_event = Event()
        self._stop_event.clear()
        self.in_queue: Queue = Queue(2)
        self.config: InferenceThreadConfig = config
        self.i_threads: dict[str, InferenceThread] = None
        self.model_manager: ModelManager = config.model_manager


    def set_inference_threads(self, i_threads: dict[str, InferenceThread]):
        self.i_threads = i_threads


    def run(self):
        verbose: bool = False
        if self.config.execution_provider == 'cuda':
            if is_cuda_available():
                perform_torch_inference(self, verbose)
            else:
                raise NotImplementedError("A cuda device is mandatory")

        elif self.config.execution_provider == 'trt':
            if is_tensorrt_available():
                from nn_inference.tensorrt.inference import perform_tensorrt_inference
                perform_tensorrt_inference(self, verbose)

        else:
            print(f"[E][I] {self.config.execution_provider} is not supported")

        while not self.in_queue.empty():
            self.in_queue.get_nowait()


    def stop(self, force: bool=False) -> None:
        self._stop_event.set()
        if force:
            while not self.in_queue.empty():
                self.in_queue.get_nowait()
        self.put_frame(None)


    def put_frame(self, frame: NnFrame) -> bool:
        try:
            self.in_queue.put(frame)
            return True
        except queue.Full:
            print("[V][I] no place")
            pass
        return False


    def ended(self) -> bool:
        return self.in_queue.empty()
