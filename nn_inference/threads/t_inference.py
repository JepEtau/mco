from __future__ import annotations
from dataclasses import dataclass
import queue
from queue import Queue
from threading import Event
from typing import Literal
from utils.p_print import *

from nn_inference.model_mgr import ModelManager
from nn_inference.threads.torch_inference import perform_torch_inference
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
        self.in_queue: Queue = Queue(1)
        self.config: InferenceThreadConfig = config
        self.i_threads: dict[str, InferenceThread] = None
        self.model_manager: ModelManager = config.model_manager


    def set_inference_threads(self, i_threads: dict[str, InferenceThread]):
        self.i_threads = i_threads


    def run(self):
        if self.config.execution_provider == 'cuda':
            if is_cuda_available():
                perform_torch_inference(self)
            else:
                raise NotImplementedError("A cuda device is mandatory")

        elif self.config.execution_provider == 'trt':
            if is_tensorrt_available():
                from .trt_inference import perform_tensorrt_inference
                perform_tensorrt_inference(self)

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


# class InferenceThread(Thread):
#     def __init__(self, execution_provider, config) -> None:
#         super().__init__()
#         self.execution_provider = execution_provider
#         self.config = config

#     def run(self):
#         try:
#             inference_function = self.get_inference_function()
#             inference_function(self)
#         except NotImplementedError as e:
#             print(f"[E][I] {str(e)}")

#     def get_inference_function(self):
#         inference_functions = {
#             'cuda': perform_torch_inference,
#             'trt': perform_tensorrt_inference,
#         }
        
#         if self.execution_provider in inference_functions:
#             return inference_functions[self.execution_provider]
#         else:
#             raise NotImplementedError(f"{self.execution_provider} is not supported")



# from threading import Thread

# # Assuming these are your original functions
# from .trt_inference import perform_tensorrt_inference
# from .torch_inference import perform_torch_inference

# class InferenceThread(Thread):
#     def __init__(self, execution_provider, config) -> None:
#         super().__init__()
#         self.execution_provider = execution_provider
#         self.config = config

#     def run(self):
#         try:
#             inference_provider = self.get_inference_provider()
#             inference_provider.run_inference(self)
#         except NotImplementedError as e:
#             print(f"[E][I] {str(e)}")

#     def get_inference_provider(self):
#         """
#         Return the appropriate inference provider subclass based on the execution provider.
#         """
#         if self.execution_provider == 'cuda':
#             return CudaInference(self)
#         elif self.execution_provider == 'trt':
#             return TrtInference(self)
#         else:
#             raise NotImplementedError(f"{self.execution_provider} is not supported")


# class InferenceProvider:
#     def __init__(self, thread: InferenceThread):
#         self.thread = thread

#     def run_inference(self):
#         raise NotImplementedError("Subclasses should implement this method.")


# class CudaInference(InferenceProvider):
#     def run_inference(self):
#         # Perform CUDA-based inference (original `perform_torch_inference` logic here)
#         perform_torch_inference(self.thread)


# class TrtInference(InferenceProvider):
#     def run_inference(self):
#         # Perform TensorRT-based inference (original `perform_tensorrt_inference` logic here)
#         perform_tensorrt_inference(self.thread)

# from threading import Thread

# # Assuming these are your original functions
# from .torch_inference import perform_torch_inference

# class InferenceThread(Thread):
#     def __init__(self, execution_provider, config) -> None:
#         super().__init__()
#         self.execution_provider = execution_provider
#         self.config = config

#     def run(self):
#         try:
#             inference_provider = self.get_inference_provider()
#             inference_provider.run_inference(self)
#         except NotImplementedError as e:
#             print(f"[E][I] {str(e)}")
#         except ImportError as e:
#             print(f"[E][I] Required library for {self.execution_provider} inference is missing: {str(e)}")

#     def get_inference_provider(self):
#         """
#         Return the appropriate inference provider subclass based on the execution provider.
#         """
#         if self.execution_provider == 'cuda':
#             return CudaInference(self)
#         elif self.execution_provider == 'trt':
#             # Try importing the TRT inference logic
#             try:
#                 from .trt_inference import perform_tensorrt_inference
#                 return TrtInference(self, perform_tensorrt_inference)
#             except ImportError as e:
#                 raise ImportError("TensorRT is not supported on this machine or missing dependencies.") from e
#         else:
#             raise NotImplementedError(f"{self.execution_provider} is not supported")


# class InferenceProvider:
#     def __init__(self, thread: InferenceThread):
#         self.thread = thread

#     def run_inference(self):
#         raise NotImplementedError("Subclasses should implement this method.")


# class CudaInference(InferenceProvider):
#     def run_inference(self):
#         # Perform CUDA-based inference (original `perform_torch_inference` logic here)
#         perform_torch_inference(self.thread)


# class TrtInference(InferenceProvider):
#     def __init__(self, thread: InferenceThread, perform_tensorrt_inference):
#         super().__init__(thread)
#         self.perform_tensorrt_inference = perform_tensorrt_inference  # Store the actual function for later use

#     def run_inference(self):
#         # Perform TensorRT-based inference (original `perform_tensorrt_inference` logic here)
#         self.perform_tensorrt_inference(self.thread)

