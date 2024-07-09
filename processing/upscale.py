from collections import deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import gc
import logging
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
from nn_inference.threads.t_decoder import DecoderThread, DecoderThreadConfig, VideoStreamInfo
from nn_inference.threads.t_encoder import EncoderThread, EncoderThreadConfig
from nn_inference.threads.t_img_writer import ImgWriterThread, ImgWriterThreadConfig
from nn_inference.threads.t_inference import InferenceParams, InferenceThread, InferenceThreadConfig
from pynnlib import (
    nnlib,
    is_cuda_available,
    NnModelSession,
    NnModel,
    nnlogger,
    NnFrameworkType,
    set_cuda_device,
    is_tensorrt_available,
    ShapeStrategy,
)
import torch
from nn_inference.img_dim import get_image_shape
from nn_inference.resource_mgr import Frame
from nn_inference.threads.t_img_reader import ImgReaderThread, ImgReaderThreadConfig
from pynnlib.model import TrtModel
from utils.mco_types import Scene
from utils.media import FShape
from utils.p_print import *
from utils.path_utils import absolute_path, path_split
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
        models: set[str],
        device: str,
        fp16: bool,
        scenes: list[Scene],
        total_frames: int,
        debug: bool,
        simulation: bool = False,
    ) -> None:

        # Decoder
        # ImageReaderParams
        max_nbytes: int = 0
        max_shape: FShape = (0, 0, 0)
        min_nbytes: int = sys.maxsize
        min_shape: FShape = (0, 0, 0)

        for scene in scenes:
            v: VideoStreamInfo = scene["inputs"]['progressive']['info']
            shape, nbytes = v.img_shape, v.img_nbytes
            if nbytes > max_nbytes:
                max_nbytes = nbytes
                max_shape = shape
            if nbytes < min_nbytes:
                min_nbytes = nbytes
                min_shape = shape

        print(f"Max: {max_nbytes} bytes, with shape: {max_shape}")
        print(f"Min: {min_nbytes} bytes, with shape: {min_shape}")

        self.models = models
        self.device = device
        self.fp16 = fp16

        if is_tensorrt_available():
            execution_provider = 'trt'
        else:
            execution_provider = 'cpu'
        opset: int = 17

        min_size = np.flip(np.array(min_shape[:2]))
        max_size = np.flip(np.array(max_shape[:2]))

        nnlogger.addHandler(logging.StreamHandler(sys.stdout))
        nnlogger.setLevel("DEBUG")

        # Open models
        self.models: dict[str, NnModel] = {}
        for m in models:
            fp: str = absolute_path(os.path.join(ml_model_dir, m))
            print(lightcyan(f"Model:"), f"{fp}")
            _model: NnModel = nnlib.open(fp, device='cuda')
            k = os.path.basename(fp)

            if execution_provider == 'trt':
                # Convert model to TensorRT
                if _model.fwk_type != NnFrameworkType.TENSORRT:
                    shape_strategy: ShapeStrategy = ShapeStrategy()
                    print(f"\tconvert to TensorRT, ",
                        f"onnx opset={opset}, "
                        f"datatype={'fp16' if fp16 else 'fp32'}"
                    )
                    start_time = time.time()
                    if np.array_equal(min_size, max_size):
                        shape_strategy.opt_size = tuple(max_size)
                    else:
                        shape_strategy.opt_size = tuple((max_size - min_size) // 2)
                        shape_strategy.min_size = tuple(min_size)
                        shape_strategy.max_size = tuple(max_size)

                    trt_model: TrtModel = nnlib.convert_to_tensorrt(
                        model=_model,
                        shape_strategy=shape_strategy,
                        fp16=fp16,
                        bf16=False,
                        tf32=False,
                        # optimization_level=3,
                        opset=opset,
                        device=device,
                        out_dir=path_split(_model.filepath)[0],
                    )

                    elapsed_time = time.time() - start_time
                    if elapsed_time > 2:
                        print(f"[V] Converted to TRT engine in {elapsed_time:.2f}s")
                    del _model
                    gc.collect()
                    _model = trt_model

            self.models[k] = _model

            min_size = _model.scale * min_size
            max_size = _model.scale * min_size
            max_nbytes *= _model.scale * _model.scale

        self.out_max_nbytes: int = max_nbytes
        self.in_max_nbytes: int = min_nbytes


        # self.e_ffmpeg_cmd = generate_ffmpeg_encoder_cmd(
        #     i_video_info, self.e_params, in_media_info
        # )


        self.simulation: bool = simulation

        # Output settings
        self.img_dtype: np.dtype = np.uint16

        self.scenes: list[Scene] = scenes


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
        in_max_shape: tuple[int, int, int] = (self.in_max_nbytes, 1, 1)
        out_max_shape: tuple[int, int, int] = (self.out_max_nbytes, 1, 1)

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
                session: TensorRtCupySession
                session.set_host_mem(htod_mem.host, dtoh_mem.host)
                session.warmup(3)
        else:
            htod_mem = None
            dtoh_mem = None

        print(yellow("HtoD memory:"))
        pprint(htod_mem)
        print(yellow("DtoH memory:"))
        pprint(dtoh_mem)

        # Video decoder for each scene
        r_thread_config = DecoderThreadConfig(
            scenes=self.scenes,
            htod_mem=htod_mem,
            cuda_stream=htod_cuda_stream,
            tensor_dtype=tensor_dtype,
            device=device
        )

        # pprint(r_thread_config)
        try:
            r_thread = DecoderThread(r_thread_config)
        except Exception as e:
            print(red(f"[E] decoder: {type(e)}"))
            return True, 0, 0
        r_thread.setName("decoder")


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


        # Create image writer thread
        w_thread_config: ImgWriterThreadConfig = ImgWriterThreadConfig(
            cuda_stream=i_params.dtoh_cuda_stream,
            tensor_dtype=i_params.tensor_dtype,
            dtoh_mem=i_params.dtoh_mem,
            img_shape=(), # i_video_info['shape'],
            img_dtype=np.dtype(self.img_dtype).name,
            img_c_order='bgr', # e_video_info['c_order'],
        )
        print("w_thread_config")
        pprint(w_thread_config)
        w_thread = ImgWriterThread(w_thread_config)
        # try:
        #     w_thread = ImgWriterThread(w_thread_config)
        # except Exception as e:
        #     print(red(f"[E] img_writer: {type(e)}"))
        #     return True, 0, 0
        w_thread.setName("img_writer")


        e_ffmpeg_cmd: list[str] = [
            ffmpeg_exe,
            "-hide_banner",
            "-loglevel", "error",
            # '-f', 'rawvideo',
            # '-pixel_format', in_video_info['pix_fmt'],
            # '-video_size', f"{w}x{h}",
            # "-r", 25
        ]

        # Create encoder thread
        e_thread_config: EncoderThreadConfig = EncoderThreadConfig(
            command=e_ffmpeg_cmd,
        )
        e_thread = EncoderThread(e_thread_config)

        # "Connect nodes"
        r_thread.set_consumer(i_thread)

        i_thread.set_producer(r_thread)
        i_thread.set_consumer(w_thread)

        w_thread.set_producer(i_thread)
        w_thread.set_consumer(e_thread)

        e_thread.set_producer(w_thread)

        f_progress_thread = None
        # f_progress_thread = ProgressThread(total=total_frames)
        w_thread.set_progress_thread(f_progress_thread)

        # e_progress_thread = ProgressThread(total=self.video_count)
        # e_thread.set_progress_bar(e_progress_thread)

        if self.simulation:
            return [0] * 4

        # Start all threads
        r_thread.set_produce_flag()
        for thread in (
            r_thread,
            i_thread,
            w_thread,
            e_thread,
            f_progress_thread,
            # e_progress_thread,
        ):
            if thread is not None:
                ResourceManager().register_thread(thread)
                thread.start()

        # Filter

        # Run until the end
        elapsed: float = 0.
        total_elapsed: float = 0.

        decoding: bool = True
        err: bool = False

        start_time = 0
        real_start = time.time()
        while True:
            if not decoding:
                # print(f"[V][C] Not decoding anymore,",
                #     f"reader={r_thread.is_alive()}",
                #     f"inference={i_thread.is_alive()}",
                #     f"encoder={e_thread.is_alive()}",
                # )
                if (
                    not r_thread.is_alive()
                    and not i_thread.is_alive()
                    and not w_thread.is_alive()
                ):
                    current_time: float = time.time()
                    total_elapsed = current_time - real_start
                    if f_progress_thread is not None:
                        elapsed = f_progress_thread.elapsed()
                    else:
                        elapsed = current_time - start_time
                    encoded = w_thread._written
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
            if not w_thread.is_alive() and r_thread.is_alive():
                print(red("Error: the encoder encountered an unexpected error"))
                err, encoded, total_elapsed = True, 0, 0
                break

            time.sleep(0.001)

        # Stop remaining threads if not already stopped (error cases)
        for thread in (r_thread, i_thread, w_thread, e_thread):
            thread.stop()
        if f_progress_thread is not None:
            f_progress_thread.stop()

        return err, encoded, elapsed, total_elapsed

