from dataclasses import dataclass
import logging
import math
from pprint import pprint
import sys
import time
import numpy as np
from nn_inference.model_mgr import ModelManager

from nn_inference.progress import ProgressThread
from nn_inference.resource_mgr import ResourceManager
from nn_inference.threads.t_cpu_decoder import CpuDecoderThread
from nn_inference.threads.t_cpu_encoder import CpuEncoderThread
from nn_inference.threads.t_cpu_inference import CpuInferenceThread, CpuInferenceThreadConfig
from nn_inference.threads.t_decoder import (
    DecoderThread,
    VideoStreamInfo,
    DecoderThreadConfig,
)
from nn_inference.threads.t_encoder import (
    EncoderThread
)
from nn_inference.threads.t_inference import (
    InferenceThread,
    InferenceThreadConfig,
)
from nn_inference import (
    is_cuda_available,
    nnlogger,
)
from parsers import Filter
from utils.mco_types import Scene
from utils.p_print import *
from utils.pxl_fmt import PIXEL_FORMAT



@dataclass
class ImageReaderParams:
    size: tuple[int, int] | None = None
    resize_algo: str = ''



class UpscalePipeline(object):
    def __init__(
        self,
        device: str,
        scenes: list[Scene],
        total_frames: int,
        debug: bool,
        simulation: bool = False,
    ) -> None:

        # Decoder
        # ImageReaderParams
        self.device = device
        self.simulation: bool = simulation
        self.scenes: list[Scene] = scenes
        self.total_frames = total_frames

        nnlogger.addHandler(logging.StreamHandler(sys.stdout))
        nnlogger.setLevel("DEBUG")

        # GPU memory, list shapes for each model, create a list of steps
        model_manager: ModelManager = ModelManager()

        in_max_nbytes: int = 0
        out_max_nbytes: int = 0
        in_max_sync_nbytes: int = 0
        for scene in scenes:
            # Verify that input videos to generate this scene have the same info
            vi: VideoStreamInfo = (
                scene['src'].primary_scene()['scene']['inputs'].progressive().info
            )
            shape = [vi.img_shape[1], vi.img_shape[0]]

            for src_scene in scene['src'].scenes():
                _vi: VideoStreamInfo = src_scene['scene']['inputs'].progressive().info
                if (
                    _vi.img_shape[1] != vi.img_shape[1]
                    or _vi.img_shape[0] != vi.img_shape[0]
                ):
                    raise ValueError(
                        f"{src_scene['k_ed_ep_ch_no']}:",
                        "input video must have the same resolution as the primary one"
                    )

            # Get HtoD max bytes.
            # The decoder MUST NOT resize the input video
            vi: VideoStreamInfo = (
                scene['src'].primary_scene()['scene']['inputs'].progressive().info
            )
            nbytes: int = vi.img_nbytes * np.dtype(vi.img_dtype).itemsize
            if nbytes > in_max_nbytes:
                in_max_nbytes = nbytes

            task_name = scene['task'].name
            filters: Filter = scene['filters'][task_name]

            pprint(filters.steps)
            print(lightcyan(f"Calculate in/out shapes:"))
            print(f"  initial shape: {shape}")
            scale: int = 1
            model_key: str = ""
            for i, filter_param in enumerate(filters.steps):
                model_key = ""
                if isinstance(filter_param, tuple | list):
                    _scale: int = 1
                    name, param = filter_param
                    if name == 'resize':
                        _scale = param
                    elif name == 'resize_to':
                        raise ValueError("not yet supported")
                    # elif name not in supported_filters:
                    #     continue

                else:
                    model_key = filter_param
                    _scale = model_manager.get_scale(model_key)
                    filters.steps[i] = model_manager.set_input_size(model_key, shape)

                print(lightgreen(f"  step {i}:"), shape, end='')
                shape = list([int(((x * _scale) // 2) * 2) for x in shape])
                print(f"-> {shape} (scale: {_scale})")
                scale = _scale * scale
                # pprint(filters)


                # Calculate maximum nb of bytes for inpaint models
                # print(red(model_key))
                if (
                    model_key
                    and (model_manager.model(model_key)
                        .arch
                        .infer_type
                        .type) == 'inpaint'
                ):
                    # scale = 1
                    # Allocate memory for inpaint mask,
                    # which is done synchronously.
                    in_sync_nbytes = math.prod(shape)
                    if in_sync_nbytes > in_max_sync_nbytes:
                        in_max_sync_nbytes = in_sync_nbytes

            # The encoder MUST NOT resize the video

            # We can include all models because inpaint models have a scale of 1:1
            out_nbytes = int(scale * scale * in_max_nbytes + 0.5)
            if PIXEL_FORMAT[scene['task'].video_settings.pix_fmt]['bpp'] > 8:
                out_nbytes *= 2
            if out_nbytes > out_max_nbytes:
                out_max_nbytes = out_nbytes

        # if in_max_sync_nbytes > 0:
        #     print(f"Scene {scene['no']} (inpaint), in: {nbytes} bytes, out: {out_nbytes}")
        # else:
        #     print(f"Scene {scene['no']}, in: {nbytes} bytes, out: {out_nbytes}")

        print(f"Max: in: {in_max_nbytes} bytes, out: {out_max_nbytes}")
        print(f"Inpaint: mask: {in_max_sync_nbytes} bytes")
        print(f"Total scale: {scale}")

        model_manager.consolidate()
        model_manager.set_in_out_max_nbytes(in_max_nbytes, out_max_nbytes)
        # Consider that all inpaint models are executed by cuda provider
        model_manager.set_sync_in_max_nbytes(
            xprovider='cuda',
            in_nbytes=in_max_sync_nbytes,
            out_nbytes=0
        )
        model_manager.set_sync_dtypes(in_dtype=np.uint8, out_dtype=np.uint8)
        print(model_manager)


    def run(self) -> tuple[bool, int, float, float]:
        if not is_cuda_available():
            return self.run_cpu()

        # Params and settings
        channels_last: bool = False

        model_manager: ModelManager = ModelManager()
        model_manager.initialize_sessions()

        print(yellow("HtoD memory:"))
        pprint(model_manager.htod_mem)
        print(yellow("DtoH memory:"))
        pprint(model_manager.dtoh_mem)
        print(yellow("HtoD (sync) memory:"))
        pprint(model_manager.htod_sync_memory('cuda'))

        # Create encoder thread
        try:
            e_thread = EncoderThread()
        except Exception as e:
            print(red(f"[E] encoder: {type(e)}"))
            return True, 0, 0
        e_thread.setName("encoder")

        # Video decoder for each scene
        d_thread_config: DecoderThreadConfig = DecoderThreadConfig(e_thread=e_thread)
        try:
            d_thread = DecoderThread(config=d_thread_config, scenes=self.scenes)
        except Exception as e:
            print(red(f"[E] decoder: {type(e)}"))
            return True, 0, 0
        d_thread.setName("decoder")

        # Create CUDA inference thread
        i_cuda_thread: InferenceThread = None
        if model_manager.has_torch_models():
            i_cuda_thread_config: InferenceThreadConfig = InferenceThreadConfig(
                execution_provider='cuda',
                d_thread=d_thread,
                e_thread=e_thread,
                channels_last=channels_last,
            )
            try:
                i_cuda_thread = InferenceThread(i_cuda_thread_config)
            except Exception as e:
                print(red(f"[E] inference: {type(e)}"))
                return True, 0, 0
            i_cuda_thread.setName("cuda_inference")

        # Create TensorRT inference thread
        i_trt_thread: InferenceThread = None
        if model_manager.has_trt_models():
            i_trt_thread_config: InferenceThreadConfig = InferenceThreadConfig(
                execution_provider='trt',
                d_thread=d_thread,
                e_thread=e_thread,
            )
            try:
                i_trt_thread = InferenceThread(i_trt_thread_config)
            except Exception as e:
                print(red(f"[E] inference: {type(e)}"))
                return True, 0, 0
            i_trt_thread.setName("trt_inference")

        # Update each thread so that they obtain a pointer to consumer
        i_threads: dict[str, InferenceThread] = {
            'cuda': i_cuda_thread,
            'trt': i_trt_thread,
        }
        for thread in (d_thread, i_cuda_thread, i_trt_thread):
            if thread is not None:
                thread.set_inference_threads(i_threads)

        # Progress bar
        f_progress_thread = None
        f_progress_thread = ProgressThread(total=self.total_frames)
        e_thread.set_progress_thread(f_progress_thread)

        if self.simulation:
            return [0] * 4

        # Verbose
        d_thread.verbose = False
        e_thread.verbose = False

        # Start all threads
        d_thread.set_produce_flag()
        for thread in (
            d_thread,
            i_cuda_thread,
            i_trt_thread,
            e_thread,
            f_progress_thread,
        ):
            if thread is not None:
                ResourceManager().register_thread(thread)
                thread.start()

        # Run until the end
        elapsed: float = 0.
        total_elapsed: float = 0.

        decoding: bool = True
        err: bool = False

        start_time = 0
        real_start = time.time()
        ask_to_end: bool = False
        while True:
            if not decoding:
                if e_thread.encoded == self.total_frames and ask_to_end:
                    e_thread.put_frame(None)
                    ask_to_end = False

                if (
                    not d_thread.is_alive()
                    # and inference_threads_ended
                    and not e_thread.is_alive()
                ):
                    current_time: float = time.time()
                    total_elapsed = current_time - real_start
                    if f_progress_thread is not None:
                        elapsed = f_progress_thread.elapsed()
                    else:
                        elapsed = current_time - start_time
                    encoded = e_thread.encoded
                    break
                time.sleep(0.0001)
                continue

            time.sleep(0.0001)
            if not d_thread.is_alive() and decoding:
                # print("[V][C] decoder has ended")
                err, message = d_thread.error_encountered()
                if err:
                    print(red(message))
                    break
                else:
                    decoding = False
                    ask_to_end = True

            time.sleep(0.0001)
            if not e_thread.is_alive() and d_thread.is_alive():
                print(red("Error: the encoder encountered an unexpected error"))
                err, encoded, total_elapsed = True, 0, 0
                break

            time.sleep(0.001)

        # Stop remaining threads if not already stopped (error cases)
        for thread in (i_cuda_thread, i_trt_thread):
            if thread is not None:
                thread.put_frame(None)
                time.sleep(0.001)

        for thread in (d_thread, i_cuda_thread, i_trt_thread, e_thread):
            if thread is not None:
                thread.stop()
        if f_progress_thread is not None:
            f_progress_thread.stop()

        return err, encoded, elapsed, total_elapsed



    def run_cpu(self) -> tuple[bool, int, float, float]:
        # Create encoder thread
        try:
            e_thread = CpuEncoderThread()
        except Exception as e:
            print(red(f"[E] encoder: {type(e)}"))
            return True, 0, 0
        e_thread.setName("encoder")

        # Video decoder for each scene
        d_thread_config: DecoderThreadConfig = DecoderThreadConfig(e_thread=e_thread)
        try:
            d_thread = CpuDecoderThread(config=d_thread_config, scenes=self.scenes)
        except Exception as e:
            print(red(f"[E] decoder: {type(e)}"))
            return True, 0, 0
        d_thread.setName("decoder")

        # Create CUDA inference thread
        i_thread_config: CpuInferenceThreadConfig = CpuInferenceThreadConfig(
            d_thread=d_thread,
            e_thread=e_thread,
            resize_scale=2,
        )
        i_thread: CpuInferenceThread = CpuInferenceThread(i_thread_config)

        for thread in (d_thread, i_thread):
            if thread is not None:
                thread.set_inference_threads({'cpu': i_thread})

        # Progress bar
        f_progress_thread = None
        f_progress_thread = ProgressThread(total=self.total_frames)
        e_thread.set_progress_thread(f_progress_thread)

        if self.simulation:
            return [0] * 4

        # Verbose
        d_thread.verbose = False
        e_thread.verbose = False

        # Start all threads
        d_thread.set_produce_flag()
        for thread in (
            d_thread,
            i_thread,
            e_thread,
            f_progress_thread,
        ):
            if thread is not None:
                ResourceManager().register_thread(thread)
                thread.start()

        # Run until the end
        elapsed: float = 0.
        total_elapsed: float = 0.

        decoding: bool = True
        err: bool = False

        start_time = 0
        real_start = time.time()
        ask_to_end: bool = False
        while True:
            if not decoding:
                if e_thread.encoded == self.total_frames and ask_to_end:
                    e_thread.put_frame(None)
                    ask_to_end = False

                if (
                    not d_thread.is_alive()
                    # and inference_threads_ended
                    and not e_thread.is_alive()
                ):
                    current_time: float = time.time()
                    total_elapsed = current_time - real_start
                    if f_progress_thread is not None:
                        elapsed = f_progress_thread.elapsed()
                    else:
                        elapsed = current_time - start_time
                    encoded = e_thread.encoded
                    break
                time.sleep(0.0001)
                continue

            time.sleep(0.0001)
            if not d_thread.is_alive() and decoding:
                # print("[V][C] decoder has ended")
                err, message = d_thread.error_encountered()
                if err:
                    print(red(message))
                    break
                else:
                    decoding = False
                    ask_to_end = True

            time.sleep(0.0001)
            if not e_thread.is_alive() and d_thread.is_alive():
                print(red("Error: the encoder encountered an unexpected error"))
                err, encoded, total_elapsed = True, 0, 0
                break

            time.sleep(0.001)

        # Stop remaining threads if not already stopped (error cases)
        for thread in (i_thread,):
            if thread is not None:
                thread.put_frame(None)
                time.sleep(0.001)

        for thread in (d_thread, i_thread, e_thread):
            if thread is not None:
                thread.stop()
        if f_progress_thread is not None:
            f_progress_thread.stop()

        return err, encoded, elapsed, total_elapsed
