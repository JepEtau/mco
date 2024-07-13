from dataclasses import dataclass
import gc
import logging
from pprint import pprint
import sys
import time
import numpy as np
from nn_inference.model_mgr import ModelManager

from nn_inference.progress import ProgressThread
from nn_inference.resource_mgr import ResourceManager
from nn_inference.threads.t_decoder import DecoderThread, VideoStreamInfo
from nn_inference.threads.t_encoder import EncoderThread
from nn_inference.threads.t_inference import InferenceThread, InferenceThreadConfig
from parsers._types import Filter
from pynnlib import (
    nnlib,
    is_cuda_available,
    NnModelSession,
    NnModel,
    nnlogger,
    NnFrameworkType,
    set_cuda_device,
    is_tensorrt_available,
)
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
        fp16: bool,
        scenes: list[Scene],
        total_frames: int,
        debug: bool,
        simulation: bool = False,
    ) -> None:

        # Decoder
        # ImageReaderParams
        self.device = device
        self.fp16 = fp16
        self.simulation: bool = simulation
        self.scenes: list[Scene] = scenes
        self.total_frames = total_frames

        nnlogger.addHandler(logging.StreamHandler(sys.stdout))
        nnlogger.setLevel("DEBUG")

        # GPU memory, list shapes for each model, create a list of steps
        model_manager: ModelManager = ModelManager()

        in_max_nbytes: int = 0
        out_max_nbytes: int = 0
        for scene in scenes:
            vi: VideoStreamInfo = scene["inputs"]['progressive']['info']
            nbytes: int = vi.img_nbytes * np.dtype(vi.img_dtype).itemsize

            if nbytes > in_max_nbytes:
                in_max_nbytes = nbytes

            task_name = scene['task'].name
            filters: Filter = scene['filters'][task_name]
            scale: int = 1
            shape = [vi.img_shape[1], vi.img_shape[0]]
            for i, model_key in enumerate(filters.steps):
                _scale = model_manager.get_scale(model_key)
                filters.steps[i] = model_manager.set_input_size(model_key, shape)
                shape = list([x * _scale for x in shape])
                scale *= _scale

            out_nbytes = scale * scale * in_max_nbytes
            if PIXEL_FORMAT[scene['task'].video_settings.pix_fmt]['bpp'] > 8:
                out_nbytes *= 2
            if out_nbytes > out_max_nbytes:
                out_max_nbytes = out_nbytes

            print(f"Scene {scene['no']}, in: {nbytes} bytes, out: {out_nbytes}")

        print(f"Max: in: {in_max_nbytes} bytes, out: {out_max_nbytes}")
        print(f"Scale: {scale}")

        pprint(model_manager._shapes)
        model_manager.consolidate()
        model_manager.set_in_out_max_nbytes(in_max_nbytes, out_max_nbytes)
        print(model_manager)



    def run(self) -> tuple[bool, int, float, float]:
        # Params and settings
        channels_last: bool = False

        model_manager: ModelManager = ModelManager()
        if is_cuda_available():
            model_manager.initialize_sessions()

        print(yellow("HtoD memory:"))
        pprint(model_manager.htod_mem)
        print(yellow("DtoH memory:"))
        pprint(model_manager.dtoh_mem)

        # Video decoder for each scene
        try:
            d_thread = DecoderThread(scenes=self.scenes)
        except Exception as e:
            d_thread = DecoderThread(scenes=self.scenes)
            print(red(f"[E] decoder: {type(e)}"))
            return True, 0, 0
        d_thread.setName("decoder")

        # Create encoder thread
        try:
            e_thread = EncoderThread()
        except Exception as e:
            print(red(f"[E] encoder: {type(e)}"))
            return True, 0, 0
        e_thread.setName("encoder")

        # Create cuda inference thread
        i_cuda_thread: InferenceThread = None
        if model_manager.has_torch_models():
            i_cuda_thread_config: InferenceThreadConfig = InferenceThreadConfig(
                execution_provider='cuda',
                d_thread=d_thread,
                e_thread=e_thread,
                channels_last=channels_last,
                skip_inference=False
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

        i_threads: dict[str, InferenceThread] = {
            'cuda': i_cuda_thread,
            'trt': i_trt_thread,
        }
        for thread in (d_thread, i_cuda_thread, i_trt_thread):
            if thread is not None:
                thread.set_inference_threads(i_threads)

        # Create image writer thread
        # w_thread_config: ImgWriterThreadConfig = ImgWriterThreadConfig(
        #     cuda_stream=i_params.dtoh_cuda_stream,
        #     tensor_dtype=i_params.tensor_dtype,
        #     dtoh_mem=i_params.dtoh_mem,
        #     img_shape=(), # i_video_info['shape'],
        #     img_dtype=np.dtype(self.img_dtype).name,
        #     img_c_order='bgr', # e_video_info['c_order'],
        # )
        # print("w_thread_config")
        # pprint(w_thread_config)
        # w_thread = ImgWriterThread(w_thread_config)
        # try:
        #     w_thread = ImgWriterThread(w_thread_config)
        # except Exception as e:
        #     print(red(f"[E] img_writer: {type(e)}"))
        #     return True, 0, 0
        # w_thread.setName("img_writer")
        # w_thread.set_producer(i_thread)
        # w_thread.set_consumer(e_thread)


        f_progress_thread = None
        f_progress_thread = ProgressThread(total=self.total_frames)
        e_thread.set_progress_thread(f_progress_thread)

        # e_progress_thread = ProgressThread(total=self.video_count)
        # e_thread.set_progress_bar(e_progress_thread)

        if self.simulation:
            return [0] * 4

        # Start all threads
        d_thread.set_produce_flag()
        for thread in (
            d_thread,
            i_cuda_thread,
            i_trt_thread,
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
        ask_to_end: bool = False
        while True:
            if not decoding:
                # inference_threads_ended = True
                # if i_cuda_thread is not None and not i_cuda_thread.ended():
                #     print(red("i_cuda_thread ended"))
                #     inference_threads_ended = False
                # if i_trt_thread is not None and not i_trt_thread.ended():
                #     print(red("i_trt_thread ended"))
                #     inference_threads_ended = False

                # if inference_threads_ended and ask_to_end:
                #     print(red("inference_threads_ended, send None to encoder threads"))
                #     e_thread.put_frame(None)
                #     ask_to_end = False

                # inference_threads_ended = bool(
                #     (i_cuda_thread is None or not i_cuda_thread.is_alive())
                #     and (i_trt_thread is None or not i_trt_thread.is_alive())
                # )
                # print(
                #     f"d_thread: {d_thread.is_alive()}",
                #     f"e_thread: {e_thread.is_alive()}",
                #     f"inference_threads_ended: {inference_threads_ended}"
                # )
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

