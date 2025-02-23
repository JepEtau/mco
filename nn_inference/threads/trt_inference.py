from __future__ import annotations
import time
from queue import Queue
import torch
from typing import TYPE_CHECKING

from nn_inference.resource_mgr import NnFrame
from nn_inference.threads.t_decoder import DecoderThread
from nn_inference.threads.t_encoder import EncoderThread
from nn_inference.threads.t_helpers import patch_next_step_no_
from nn_inference.toolbox.filtering import apply_cuda_filters_
from pynnlib import is_tensorrt_available
if is_tensorrt_available():
    from pynnlib.nn_tensor_rt.inference.session import TensorRtSession
    import tensorrt as trt
from utils.p_print import *
if TYPE_CHECKING:
    from .t_inference import InferenceThread


@torch.inference_mode()
def perform_tensorrt_inference(self: InferenceThread, verbose: bool = False):
    print(cyan(f"[V][I][TRT] TensorRT InferenceThread"))
    in_queue: Queue = self.in_queue
    cuda_stream = self.model_manager.trt_cuda_stream
    scale: int = 1

    d_thread: DecoderThread = self.config.d_thread
    e_thread: EncoderThread = self.config.e_thread

    with torch.cuda.stream(cuda_stream):
        while not self._stop_event.is_set():
            if verbose:
                print(cyan("[V][I][TRT] waiting"))
            input = in_queue.get(block=True)
            if input is None or self._stop_event.is_set():
                break
            frame: NnFrame = input

            # Get model and session
            model_key: str = frame.sequence[frame.step_no]
            session: TensorRtSession = self.model_manager.session(model_key)
            context, engine = session.context, session.engine
            session_dtype: torch.dtype = session.dtype
            if session_dtype == torch.bfloat16:
                session_dtype = torch.float32

            if verbose:
                verbose_prefix: str = f"[V][I][TRT][{frame.step_no}]"
                print(blue(f"{verbose_prefix} model: {model_key}, dtype:{session_dtype}"))


            # Input tensor
            in_tensor = frame.tensor
            n, c, in_h, in_w = in_tensor.shape
            in_tensor = in_tensor.to(dtype=session_dtype)
            in_tensor = torch.ravel(in_tensor)
            if verbose:
                print(blue(f"{verbose_prefix} in tensor dtype:{in_tensor.dtype}"))

            # Prepare output tensor in same device
            scale = session.model.scale
            out_tensor_shape = (n, c, in_h * scale, in_w * scale)
            out_tensor: torch.Tensor = torch.empty(
                out_tensor_shape,
                dtype=session_dtype,
                device=in_tensor.device
            )

            # Perform simple inference
            bindings = [in_tensor.data_ptr(), out_tensor.data_ptr()]
            for i in range(engine.num_io_tensors):
                context.set_tensor_address(engine.get_tensor_name(i), bindings[i])
            context.execute_async_v3(stream_handle=cuda_stream.cuda_stream)

            frame.tensor = torch.clamp(out_tensor, 0., 1.)

            # if verbose:
            #     print(cyan(f"{verbose_prefix} out tensor: {out_tensor.data_ptr()}, {out_tensor.shape}, {out_tensor.dtype}, {out_tensor.nbytes}"))
            frame.step_no += 1

            time.sleep(0.0001)
            cuda_stream.synchronize()

            # Apply cuda filters until next inference or decoder
            # torch_cuda_stream = torch.cuda.Stream()
            # with torch.cuda.stream(torch_cuda_stream):
            apply_cuda_filters_(
                frame, verbose=verbose, cuda_stream=cuda_stream
            )

            # No more operation with input tensor
            # TODO: study if it can be done before.
            verbose_prefix: str = f"[V][I][TRT][{frame.step_no}]"
            if frame.step_no >= frame.encoder_step_no:
                if verbose:
                    print(blue(f"{verbose_prefix} ask decoder to produce after cuda filters"))
                d_thread.set_produce_flag()

            # Skip following model if inpainting and dsr
            # patch_next_step_no_(frame=frame, model_manager=model_manager)

            # Next filter: encoder or nn
            if frame.step_no >= frame.encoder_step_no:
                if verbose:
                    print(
                        cyan(f"{verbose_prefix} send to encoder"),
                        f"{type(frame.tensor)}{frame.tensor.data_ptr()}, {frame.tensor.shape}, {frame.tensor.dtype}"
                    )
                consumer = e_thread

            else:
                xprovider: str = self.model_manager.xprovider(frame.sequence[frame.step_no])
                if verbose:
                    print(cyan(f"{verbose_prefix} send to inference thread: {xprovider}"))
                consumer = self.i_threads[xprovider]

            self.consumer = consumer
            consumer.put_frame(frame)

    print(cyan(f"[V][I][TRT] Ended"))

