from __future__ import annotations
from copy import copy
from pprint import pprint
import time
import cupy as cp
from queue import Queue
import numpy as np
import torch
from torch import Tensor
from typing import TYPE_CHECKING

from nn_inference.model_mgr import ModelManager
from nn_inference.pytorch.inpaint_inference import perform_inpaint_inference
from nn_inference.pytorch.temporal_inference import perform_temporal_inference
from nn_inference.resource_mgr import NnFrame
from nn_inference.threads.t_decoder import DecoderThread
from nn_inference.threads.t_encoder import EncoderThread
from nn_inference.threads.t_helpers import patch_next_step_no_
from nn_inference.toolbox.filtering import apply_cuda_filters_
from utils.p_print import *
from pynnlib import (
    NnModelSession,
    NnModel
)
if TYPE_CHECKING:
    from ..threads.t_inference import InferenceThread



def perform_torch_inference(self: InferenceThread, verbose: bool = False) -> None:
    print(blue(f"[V][I][TORCH] PyTorch InferenceThread"))
    in_queue: Queue = self.in_queue
    channels_last: bool = False
    verbose = False
    # if channels_last:
    #     model = model.to(memory_format=torch.channels_last)

    model_manager = self.model_manager
    infer_stream = model_manager.torch_infer_stream
    d_thread: DecoderThread = self.config.d_thread
    e_thread: EncoderThread = self.config.e_thread

    # copy before seems to be slower than waiting
    do_copy: bool = False
    # try:

    with torch.inference_mode():
        with torch.cuda.stream(infer_stream):
            while not self._stop_event.is_set():
                if verbose:
                    print(blue("[V][I][TORCH] waiting"))
                input = in_queue.get(block=True)
                if input is None or self._stop_event.is_set():
                    print(yellow("input is none or stop required"))
                    break
                frame: NnFrame = input

                # Get model
                model_key: str = frame.sequence[frame.step_no]
                if verbose:
                    verbose_prefix: str = f"[V][I][TORCH][{frame.step_no}]"
                    print(blue(f"{verbose_prefix} model: {model_key}"))

                if frame.tensor is not None:
                    if do_copy:
                        in_tensor: Tensor = frame.tensor.clone()
                        # self.producer.set_produce_flag()
                    else:
                        in_tensor = frame.tensor

                    if verbose:
                        print(blue(f"[V][I][TORCH] inference: {in_tensor.shape}, {in_tensor.dtype}"))
                    if channels_last:
                        in_tensor = in_tensor.to(memory_format=torch.channels_last)

                    if verbose:
                        print(f"[V][I][TORCH] {model_manager.model(model_key).filepath}")

                    # Convert to correct datatype
                    session: NnModelSession = model_manager.session(model_key)
                    in_tensor = in_tensor.to(dtype=session.dtype)

                else:
                    in_tensor = None

                # Perform inference
                model: NnModel = model_manager.model(model_key)
                module = model.module
                action: str = 'none'
                out_torch_tensor: Tensor
                if model.arch.infer_type.type == 'simple':
                    # Perform inference
                    out_torch_tensor = module(in_tensor)

                elif model.arch.infer_type.type == 'inpaint':
                    out_torch_tensor = perform_inpaint_inference(
                        frame,
                        in_tensor,
                        model_manager,
                    )

                elif model.arch.infer_type.type == 'temporal':
                    out_f_no, out_torch_tensor, action = perform_temporal_inference(
                        frame,
                        in_tensor,
                        model_manager,
                    )

                    if action == 'request':
                        # Waiting for an additional frame to do the inference
                        if d_thread is not None and d_thread.is_alive():
                            d_thread.set_produce_flag()
                        continue

                    elif action == 'last':
                        # Put the same frame except the tensor
                        # so that the inference will generate a new frame
                        saved_step_no = frame.step_no

                    if out_torch_tensor is None:
                        continue

                    frame.f_no = out_f_no


                if channels_last:
                    out_torch_tensor = out_torch_tensor.to(
                        memory_format=torch.contiguous_format
                    )

                time.sleep(0.0001)
                infer_stream.synchronize()

                # From torch to CuPy format
                # if verbose:
                #     print(blue(f"{verbose_prefix} out tensor: {out_tensor.data_ptr()}, {out_tensor.shape}, {out_tensor.dtype}, {out_tensor.nbytes}"))
                frame.tensor = out_torch_tensor
                frame.step_no += 1
                verbose_prefix: str = f"[V][I][TORCH][{frame.step_no}]"

                # Apply cuda filters until next inference or decoder
                with torch.inference_mode():
                    torch_cuda_stream = torch.cuda.Stream()
                    with torch.cuda.stream(torch_cuda_stream):
                        apply_cuda_filters_(
                            frame,
                            cuda_stream=torch_cuda_stream,
                            verbose=verbose
                        )
                        time.sleep(0.0001)
                        torch_cuda_stream.synchronize()

                # No more operation with input tensor
                # TODO: study if it can be done before.
                verbose_prefix: str = f"[V][I][TORCH][{frame.step_no}]"
                if frame.step_no >= frame.encoder_step_no:
                    if verbose:
                        print(blue(f"{verbose_prefix} ask decoder to produce after cuda filters"))
                    if d_thread is not None and d_thread.is_alive():
                        d_thread.set_produce_flag()

                # Skip following model if inpainting and dsr
                # patch_next_step_no_(frame=frame, model_manager=model_manager)

                # Next filter: encoder or nn
                if frame.step_no >= frame.encoder_step_no:
                    if verbose:
                        print(blue(f"[V][I][TORCH] send to encoder"))
                    consumer = e_thread
                else:
                    xprovider: str = model_manager.xprovider(frame.sequence[frame.step_no])
                    if verbose:
                        print(blue(f"[V][I][TORCH] send to inference thread: {xprovider}"))
                    consumer = self.i_threads[xprovider]

                self.consumer = consumer

                if consumer is not None and consumer.is_alive():
                    consumer.put_frame(frame)
                else:
                    print(blue(f"[V][I][TORCH] {consumer.name} is not alive anymore"))
                    break

                if action == 'last':
                    # Put the same frame except the tensor
                    # so that the inference will generate a new frame
                    frame = NnFrame(
                        f_no=out_f_no,
                        tensor=None,
                        channel_last=frame.channel_last,
                        sequence=copy(frame.sequence),
                        step_no=saved_step_no,
                        encoder_step_no=frame.encoder_step_no,
                        scene=frame.scene,
                        src_scene=frame.src_scene,
                        last=True,
                    )
                    self.put_frame(frame)

    print(blue(f"[V][I][TORCH] Ended"))
    # except Exception as e:
    #     print(f"[E] Failed to add a frame to the inference: {type(e)}", flush=True)

