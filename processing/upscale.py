from collections import deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import multiprocessing
import os
from pprint import pprint
import sys
import time
from typing import Any
import cupy as cp
import numpy as np
from nn_inference.progress import ProgressThread
from nn_inference.cupy import HostDeviceMemory, allocate_memory

from nn_inference.pytorch.session_stub import PyTorchStubSession
from nn_inference.resource_mgr import ResourceManager
from nn_inference.threads.t_encoder import EncoderThread, EncoderThreadConfig
from nn_inference.threads.t_inference import InferenceParams, InferenceThread, InferenceThreadConfig
from pynnlib import (
    nnlib,
    is_cuda_available,
    NnModelSession,
    NnModel,
    NnFrameworkType,
    set_cuda_device,
    is_tensorrt_available,
)
import torch
from nn_inference.img_dim import get_image_shape
from nn_inference.resource_mgr import Frame
from nn_inference.threads.t_img_reader import ImgReaderThread, ImgReaderThreadConfig
from utils.p_print import *
from utils.path_utils import absolute_path
from utils.tools import ffmpeg_exe, ml_model_dir
if is_tensorrt_available():
    from nn_inference.pytorch.session_cupy import PyTorchCuPySession
    from nn_inference.tensorrt.session_cupy import TensorRtCupySession


@dataclass
class ImageReaderParams:
    size: tuple[int, int] | None = None
    resize_algo: str = ''



class UpscalePipeline(object):
    def __init__(
        self,
        frames: list[Frame],
        models: set[str],
        device: str,
        fp16: bool,
        debug: bool,
    ) -> None:

        # Decoder
        # ImageReaderParams
        max_nbytes: int = 0
        max_shape: tuple[int] = (0,0,0)
        start_time = time.time()
        for f in frames:
            shape, nbytes = get_image_shape(f.in_img_fp)
            if nbytes > max_nbytes:
                max_nbytes = nbytes
                max_shape = shape
        elapsed = time.time() - start_time
        print(f"{max_nbytes} bytes, with shape: {max_shape} ({elapsed * 1000:.03f}ms)")


        self.max_nbytes: int = max_nbytes
        self.frames = deque(frames)
        r_c_order = 'rgb'
        self.models = models
        self.device = device
        self.fp16 = fp16

        # Open models
        self.models: dict[str, NnModel] = {}
        for m in models:
            fp: str = absolute_path(os.path.join(ml_model_dir, m))
            print(lightcyan(f"Model:"), f"{fp}")
            self.models[os.path.basename(fp)] = nnlib.open(fp, device='cuda')
        # self.e_ffmpeg_cmd = generate_ffmpeg_encoder_cmd(
        #     i_video_info, self.e_params, in_media_info
        # )


    def run(self) -> tuple[bool, int, float, float]:
        # Params and settings
        model_key: str = list(self.models.keys())[0]
        model = self.models[model_key]
        sessions: dict[str, NnModelSession] = {}
        device: str = self.device
        channels_last: bool = False


        d_dtype: np.dtype = np.uint8
        i_out_dtype = e_in_dtype = np.float32


        # Set custom sessions
        if is_cuda_available():
            nnlib.set_session_constructor(NnFrameworkType.PYTORCH, PyTorchCuPySession)
        if is_tensorrt_available():
            nnlib.set_session_constructor(NnFrameworkType.TENSORRT, TensorRtCupySession)


        # In and Out max shapes used for memory allocation
        in_max_shape: tuple[int, int, int] = (self.max_nbytes, 1, 1)
        max_scale = max([m.scale for m in self.models.values()])
        out_max_shape: tuple[int, int, int] = (self.max_nbytes * max_scale * max_scale, 1, 1)


        # Initialize session
        _session: NnModelSession = nnlib.session(model)
        htod_cuda_stream = None
        dtoh_cuda_stream = None
        infer_cuda_stream = None
        if (
            model.fwk_type == NnFrameworkType.PYTORCH
            and is_cuda_available()
        ):
            session: PyTorchCuPySession = _session
            session.initialize(
                device=device,
                fp16=self.fp16,
                memalloc=False,
                in_max_shape=in_max_shape,
            )

            set_cuda_device(device)
            htod_cuda_stream = cp.cuda.stream.Stream(non_blocking=True)
            dtoh_cuda_stream = cp.cuda.stream.Stream(non_blocking=True)
            infer_cuda_stream = torch.cuda.Stream(device)
            tensor_dtype: cp.dtype = cp.float16 if self.fp16 else cp.float32

        if (
            is_tensorrt_available()
            and model.fwk_type == NnFrameworkType.TENSORRT
        ):
            session: TensorRtCupySession = _session
            session.initialize(
                device=device,
                fp16=self.fp16,
                memalloc=False
            )

            htod_cuda_stream = session.htod_stream
            dtoh_cuda_stream = session.dtoh_stream
            infer_cuda_stream = session.infer_stream
            tensor_dtype: cp.dtype = cp.float16 if self.fp16 else cp.float32

        if (
            model.fwk_type == NnFrameworkType.PYTORCH
            and not is_cuda_available()
        ):
            print("use CPU session")
            session: PyTorchStubSession = _session
            session.initialize(
                device=device,
                fp16=self.fp16,
            )
            tensor_dtype: np.dtype = np.float32

        sessions[model_key] = session


        # Allocate Host memory
        if (
            is_cuda_available()
            and model.fwk_type in (NnFrameworkType.PYTORCH, NnFrameworkType.TENSORRT)
            and 'cuda' in device
        ):
            htod_mem = allocate_memory(in_max_shape, d_dtype, htod_cuda_stream)
            dtoh_mem = allocate_memory(out_max_shape, i_out_dtype, dtoh_cuda_stream)

            if model.fwk_type == NnFrameworkType.TENSORRT:
                session.set_host_mem(htod_mem.host, dtoh_mem.host)
                session.warmup(10)
        else:
            htod_mem = None
            dtoh_mem = None

        print(yellow("HtoD memory:"))
        pprint(htod_mem)
        print(yellow("DtoH memory:"))
        pprint(dtoh_mem)


        # Create image reader thread
        r_thread_config = ImgReaderThreadConfig(
            htod_mem=htod_mem,
            frames=self.frames,
            cuda_stream=htod_cuda_stream,
            tensor_dtype=tensor_dtype,
            device=device
        )
        pprint(r_thread_config)
        try:
            r_thread = ImgReaderThread(r_thread_config)
        except Exception as e:
            print(red(f"[E] decoder: {type(e)}"))
            return True, 0, 0
        r_thread.setName("img_reader")


        # Create inference thread
        i_params: InferenceParams = InferenceParams(
            htod_mem=htod_mem,
            dtoh_mem=dtoh_mem,
            htod_cuda_stream=htod_cuda_stream,
            infer_cuda_stream=infer_cuda_stream,
            dtoh_cuda_stream=dtoh_cuda_stream,
            tensor_dtype=tensor_dtype,
        )
        i_thread_config: InferenceThreadConfig = InferenceThreadConfig(
            session=session,
            cuda_stream=infer_cuda_stream,
            channels_last=channels_last,
            skip_inference=False
        )
        try:
            i_thread = InferenceThread(i_thread_config)
        except Exception as e:
            print(red(f"[E] inference: {type(e)}"))
            return True, 0, 0
        i_thread.setName("inference")


        e_ffmpeg_cmd: list[str] = [
            ffmpeg_exe,
            "-hide_banner",
            "-loglevel", "error",
            '-f', 'rawvideo',
            # '-pixel_format', in_video_info['pix_fmt'],
            # '-video_size', f"{w}x{h}",
            # "-r", 25
        ]


        # Create encoder thread
        e_thread_config: EncoderThreadConfig = EncoderThreadConfig(
            command=e_ffmpeg_cmd,
            cuda_stream=i_params.dtoh_cuda_stream,
            tensor_dtype=i_params.tensor_dtype,
            dtoh_mem=i_params.dtoh_mem,
            img_shape=(), # i_video_info['shape'],
            img_dtype="uint8", # np.dtype(e_video_info['dtype']).name,
            img_c_order='bgr', # e_video_info['c_order'],
        )
        print("e_thread_config")
        pprint(e_thread_config)
        try:
            e_thread = EncoderThread(e_thread_config)
        except Exception as e:
            print(red(f"[E] encoder: {type(e)}"))
            return True, 0, 0
        e_thread.setName("encoder")

        # Start all threads
        for thread in (r_thread, i_thread, e_thread):
            ResourceManager().register_thread(thread)
            thread.start()

        # "Connect nodes"
        r_thread.set_consumer(i_thread)
        i_thread.set_producer(r_thread)
        i_thread.set_consumer(e_thread)
        e_thread.set_producer(i_thread)
        r_thread.set_produce_flag()

        progress_thread = ProgressThread(total=len(self.frames))
        ResourceManager().register_thread(progress_thread)
        e_thread.set_consumer(progress_thread)

        # Run until the end
        elapsed: float = 0.
        total_elapsed: float = 0.

        decoding: bool = True
        err: bool = False

        if progress_thread is not None:
            progress_thread.start()


        start_time = 0
        real_start = time.time()
        while True:
            if not decoding:
                # print("[V][C] Not decoding anymore")
                if (
                    not r_thread.is_alive()
                    and not i_thread.is_alive()
                    and not e_thread.is_alive()
                ):
                    current_time: float = time.time()
                    total_elapsed = current_time - real_start
                    if progress_thread is not None:
                        elapsed = progress_thread.elapsed()
                    else:
                        elapsed = current_time - start_time
                    encoded = e_thread.encoded
                    break
                time.sleep(0.0001)
                continue

            time.sleep(0.0001)
            if not r_thread.is_alive() and decoding:
                # print("[V][C] decoder has ended")
                err, message = r_thread.error_encountered()
                if err:
                    print(red(message))
                    break
                else:
                    decoding = False

            time.sleep(0.0001)
            if not e_thread.is_alive() and r_thread.is_alive():
                print(red("Error: the encoder encountered an unexpected error"))
                err, encoded, total_elapsed = True, 0, 0
                break

            time.sleep(0.001)

        # Stop remaining threads if not already stopped (error cases)
        for thread in (r_thread, e_thread, i_thread):
            thread.stop()
        if progress_thread is not None:
            progress_thread.stop()

        return err, encoded, elapsed, total_elapsed

