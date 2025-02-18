from __future__ import annotations
from dataclasses import dataclass
import queue
from queue import Queue
from threading import Event
import time
from typing import Literal

import cv2
import numpy as np
from utils.p_print import *

from nn_inference.resource_mgr import NnFrame, RlgThread
from nn_inference.threads.t_cpu_decoder import CpuDecoderThread
from nn_inference.threads.t_cpu_encoder import CpuEncoderThread



@dataclass
class CpuInferenceThreadConfig:
    d_thread: CpuDecoderThread
    e_thread: CpuEncoderThread
    resize_scale: int = 2



class CpuInferenceThread(RlgThread):
    def __init__(
        self,
        config: CpuInferenceThreadConfig
    ) -> None:
        super().__init__()
        self._stop_event = Event()
        self._stop_event.clear()
        self.in_queue: Queue = Queue(1)
        self.config: CpuInferenceThreadConfig = config
        self.i_threads: dict[str, CpuInferenceThreadConfig] = None


    def set_inference_threads(self, i_threads: dict[str, CpuInferenceThreadConfig]):
        self.i_threads = i_threads

    def run(self):
        verbose: bool = False
        in_queue: Queue = self.in_queue

        d_thread: CpuDecoderThread = self.config.d_thread
        e_thread: CpuEncoderThread = self.config.e_thread

        while not self._stop_event.is_set():
            if verbose:
                print(blue("[V][I][CPU] waiting"))
            input = in_queue.get(block=True)
            if input is None or self._stop_event.is_set():
                reason = (
                    "no frame anymore"
                    if input is None
                    else "asked to stop"
                )
                print(blue(f"[V][I][CPU] end of inference (reason: {reason})"))
                break
            frame: NnFrame = input

            # Get model
            model_key: str = frame.sequence[frame.step_no]
            if verbose:
                verbose_prefix: str = f"[V][I][CPU][{frame.step_no}]"
                print(blue(f"{verbose_prefix} model: {model_key}"))

            # Simulate inference
            in_img: np.ndarray = frame.tensor
            h, w = in_img.shape[:2]
            out_img: np.ndarray = cv2.resize(in_img, (w*2, h*2))

            frame.tensor = out_img

            # Force to encoder
            frame.step_no = frame.encoder_step_no
            verbose_prefix: str = f"[V][I][CPU][{frame.step_no}]"

            time.sleep(0.0001)

            # No more operation with input tensor
            # TODO: study if it can be done before.
            verbose_prefix: str = f"[V][I][CPU][{frame.step_no}]"
            if frame.step_no >= frame.encoder_step_no:
                if verbose:
                    print(blue(f"{verbose_prefix} ask decoder to produce after cuda filters"))
                d_thread.set_produce_flag()

            # Next filter: encoder
            if frame.step_no >= frame.encoder_step_no:
                if verbose:
                    print(blue(f"[V][I][CPU] send to encoder {frame.f_no}"))
                consumer = e_thread

            self.consumer = consumer
            consumer.put_frame(frame)

        print(blue(f"[V][I][CPU] ended"))
        while not self.in_queue.empty():
            self.in_queue.get_nowait()


    def stop(self, force: bool=False) -> None:
        if force:
            while not self.in_queue.empty():
                self.in_queue.get_nowait()
        self.put_frame(None)
        self._stop_event.set()


    def put_frame(self, frame: NnFrame) -> bool:
        try:
            self.in_queue.put(frame)
            return True
        except queue.Full:
            print(red(f"[V][I] failed adding {type(frame)}"))
            pass
        return False


    def ended(self) -> bool:
        return self.in_queue.empty()
