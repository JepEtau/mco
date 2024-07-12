from dataclasses import dataclass
import gc
import logging
from pprint import pprint
import sys
import time
import numpy as np
from nn_inference.model_mgr import ModelManager

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

        if is_tensorrt_available():
            execution_provider = 'trt'
        else:
            execution_provider = 'cpu'
        opset: int = 17

        nnlogger.addHandler(logging.StreamHandler(sys.stdout))
        nnlogger.setLevel("DEBUG")


        # GPU memory, list shapes for each model, create a list of steps
        model_manager: ModelManager = ModelManager()

        in_max_nbytes: int = 0
        out_max_nbytes: int = 0
        model_shapes: dict[str, set] = {}
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

        pprint(model_manager._shapes)

        model_manager.consolidate()
        model_manager.set_in_out_max_nbytes(in_max_nbytes, out_max_nbytes)
        print(model_manager)


        self.simulation: bool = simulation

        # Output settings
        self.scenes: list[Scene] = scenes
        self.total_frames = total_frames

        # sys.exit()


    def run(self) -> tuple[bool, int, float, float]:
        # Params and settings
        device: str = self.device
        channels_last: bool = False

        model_manager: ModelManager = ModelManager()
        if is_cuda_available():
            model_manager.initialize_sessions()


        d_dtype: np.dtype = np.uint8
        i_out_dtype = e_in_dtype = np.float32

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


        # Create inference thread
        i_thread_config: InferenceThreadConfig = InferenceThreadConfig(
            execution_provider='cuda',
            channels_last=channels_last,
            skip_inference=False
        )
        try:
            i_thread = InferenceThread(i_thread_config)
        except Exception as e:
            print(red(f"[E] inference: {type(e)}"))
            return True, 0, 0
        i_thread.setName("inference")

        # Create encoder thread
        try:
            e_thread = EncoderThread()
        except Exception as e:
            print(red(f"[E] encoder: {type(e)}"))
            return True, 0, 0
        e_thread.setName("encoder")

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

        # "Connect nodes"
        d_thread.set_consumer(i_thread)

        i_thread.set_producer(d_thread)
        i_thread.set_consumer(e_thread)

        # w_thread.set_producer(i_thread)
        # w_thread.set_consumer(e_thread)

        e_thread.set_producer(i_thread)

        f_progress_thread = None
        # f_progress_thread = ProgressThread(total=self.total_frames)
        e_thread.set_progress_thread(f_progress_thread)

        # e_progress_thread = ProgressThread(total=self.video_count)
        # e_thread.set_progress_bar(e_progress_thread)

        if self.simulation:
            return [0] * 4

        # Start all threads
        d_thread.set_produce_flag()
        for thread in (
            d_thread,
            i_thread,
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
                #     f"reader={d_thread.is_alive()}",
                #     f"inference={i_thread.is_alive()}",
                #     f"encoder={e_thread.is_alive()}",
                # )
                if (
                    not d_thread.is_alive()
                    and not i_thread.is_alive()
                    and not e_thread.is_alive()
                ):
                    current_time: float = time.time()
                    total_elapsed = current_time - real_start
                    if f_progress_thread is not None:
                        elapsed = f_progress_thread.elapsed()
                    else:
                        elapsed = current_time - start_time
                    encoded = e_thread._encoded
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

            time.sleep(0.0001)
            if not e_thread.is_alive() and d_thread.is_alive():
                print(red("Error: the encoder encountered an unexpected error"))
                err, encoded, total_elapsed = True, 0, 0
                break

            time.sleep(0.001)

        # Stop remaining threads if not already stopped (error cases)
        for thread in (d_thread, i_thread, e_thread):
            thread.stop()
        if f_progress_thread is not None:
            f_progress_thread.stop()

        return err, encoded, elapsed, total_elapsed

