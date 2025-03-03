from dataclasses import dataclass
import logging
import math
from pprint import pprint
import sys
import time
import numpy as np
import torch
from nn_inference.model_mgr import ModelManager

from nn_inference.threads.t_progress import ProgressThread
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
    EncoderThread,
    EncoderThreadConfig
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
        scene: Scene,
        model_manager: ModelManager,
        progress_thread: ProgressThread,
        debug: bool,
        simulation: bool = False,
    ) -> None:

        # Decoder
        # ImageReaderParams
        self.device = device
        self.simulation: bool = simulation
        self.scene: Scene = scene
        self.f_progress_thread: ProgressThread = progress_thread
        self.model_manager: ModelManager = model_manager

        nnlogger.addHandler(logging.StreamHandler(sys.stdout))
        nnlogger.setLevel("DEBUG")

        in_max_nbytes: int = 0
        out_max_nbytes: int = 0
        in_max_sync_nbytes: int = 0
        # Verify that input videos to generate this scene have the same info
        vi: VideoStreamInfo = (
            scene['src'].primary_scene().in_scene['inputs'].progressive().info
        )
        shape = [vi.img_shape[1], vi.img_shape[0]]

        for src_scene in scene['src'].scenes():
            _vi: VideoStreamInfo = src_scene.in_scene['inputs'].progressive().info
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
            scene['src'].primary_scene().in_scene['inputs'].progressive().info
        )
        nbytes: int = vi.img_nbytes
        if nbytes > in_max_nbytes:
            in_max_nbytes = nbytes

        task_name = scene['task'].name
        filters: Filter = scene['filters'][task_name]

        pprint(filters.steps)
        print(darkgrey(f"Calculate in/out shapes:"))
        print(f"    initial shape: {shape}")
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
                    w, h = map(int, param.split(":")[:2])
                    shape = [w, h]

                elif name == 'rotate90':
                    if param not in (2, 4):
                        shape = [shape[1], shape[0]]

                # elif name not in supported_filters:
                #     continue

            else:
                model_key = filter_param
                try:
                    _scale = model_manager.get_scale(model_key)
                except:
                    raise ValueError(f"no valid scale for {model_key}")
                filters.steps[i] = model_manager.set_input_size(model_key, shape)

            print(
                darkgrey(f"    step {i}:"),
                (
                    f"{model_manager.model(model_key).arch_name}".ljust(22)
                    if model_key
                    else f"{name}".ljust(22)
                ),
                shape,
                end=''
            )

            shape = list([int(((x * _scale) // 2) * 2) for x in shape])
            print(f" -> {shape} (scale: {_scale})")
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
        out_nbytes = math.prod(shape) * vi.img_shape[2]
        if PIXEL_FORMAT[scene['task'].video_settings.pix_fmt]['bpp'] > 8:
            out_nbytes *= 2
        if out_nbytes > out_max_nbytes:
            out_max_nbytes = out_nbytes

        # if in_max_sync_nbytes > 0:
        #     print(f"Scene {scene['no']} (inpaint), in: {nbytes} bytes, out: {out_nbytes}")
        # else:
        #     print(f"Scene {scene['no']}, in: {nbytes} bytes, out: {out_nbytes}")

        print(f"  pinned memory: in: {in_max_nbytes} bytes, out: {out_nbytes}")
        print(f"  inpaint: mask: {in_max_sync_nbytes} bytes")
        print(f"  total scale: {scale}")

        model_manager.opset = 20
        model_manager.consolidate()
        model_manager.set_in_out_max_nbytes(in_max_nbytes, out_nbytes)

        print(model_manager)


    def run(self) -> tuple[bool, int]:
        if not is_cuda_available():
            return self.run_cpu()

        # Params and settings
        channels_last: bool = False

        model_manager: ModelManager = self.model_manager
        model_manager.initialize_sessions()

        if False:
            print(yellow("HtoD memory:"))
            pprint(model_manager.htod_mem)
            print(yellow("DtoH memory:"))
            pprint(model_manager.dtoh_mem)
            print(yellow("HtoD (sync) memory:"))
            pprint(model_manager.htod_sync_memory('cuda'))

        # Create encoder thread
        e_thread_config: EncoderThreadConfig = EncoderThreadConfig(
            model_manager=model_manager,
        )
        try:
            e_thread = EncoderThread(config=e_thread_config)
        except Exception as e:
            print(red(f"[E] encoder: {type(e)}"))
            return True, 0, 0
        e_thread.setName("encoder")

        # Video decoder for each scene
        d_thread_config: DecoderThreadConfig = DecoderThreadConfig(
            e_thread=e_thread,
            model_manager=model_manager,
        )
        try:
            d_thread = DecoderThread(config=d_thread_config, scene=self.scene)
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
                model_manager=model_manager,
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
                model_manager=model_manager,
            )
            try:
                i_trt_thread = InferenceThread(i_trt_thread_config)
            except Exception as e:
                print(red(f"[E] inference: {type(e)}"))
                return True, 0, 0
            i_trt_thread.setName("trt_inference")

        # Update each thread so that they obtain a pointer to consumer
        i_thread_dict: dict[str, InferenceThread] = {
            'cuda': i_cuda_thread,
            'trt': i_trt_thread,
        }

        return self._run(
            d_thread=d_thread,
            i_thread_dict=i_thread_dict,
            e_thread=e_thread
        )


    def run_cpu(self) -> tuple[bool, int]:
        # Create encoder thread
        try:
            e_thread = CpuEncoderThread()
        except Exception as e:
            print(red(f"[E] encoder: {type(e)}"))
            return True, 0, 0
        e_thread.setName("encoder")

        # Video decoder for each scene
        d_thread_config: DecoderThreadConfig = DecoderThreadConfig(
            e_thread=e_thread,
            model_manager=self.model_manager,
        )
        try:
            d_thread = CpuDecoderThread(
                config=d_thread_config,
                scene=self.scene
            )
        except Exception as e:
            print(red(f"[E] CPU decoder: {type(e)}"))
            return True, 0, 0
        d_thread.setName("decoder")

        # Create CUDA inference thread
        i_thread_config: CpuInferenceThreadConfig = CpuInferenceThreadConfig(
            d_thread=d_thread,
            e_thread=e_thread,
            resize_scale=2.4,
        )
        i_thread_dict = {'cpu': CpuInferenceThread(i_thread_config)}

        return self._run(
            d_thread=d_thread,
            i_thread_dict=i_thread_dict,
            e_thread=e_thread
        )


    def _run(
        self,
        d_thread: DecoderThread | CpuDecoderThread,
        i_thread_dict: dict[str, InferenceThread | CpuInferenceThread],
        e_thread: EncoderThread | CpuEncoderThread,
    ) -> tuple[bool, int]:

        i_threads = list(i_thread_dict.values())
        for thread in (d_thread, *i_threads):
            if thread is not None:
                thread.set_inference_threads(i_thread_dict)

        # Progress bar
        f_progress_thread = self.f_progress_thread
        e_thread.set_progress_thread(f_progress_thread)
        if not f_progress_thread.is_running:
            f_progress_thread.start()


        if self.simulation:
            return [0] * 4

        # Verbose
        d_thread.verbose = False
        for t in i_threads:
            if t is not None:
                t.verbose = True
        e_thread.verbose = False

        # Start all threads
        d_thread.set_produce_flag()
        for thread in (
            d_thread,
            *i_threads,
            e_thread,
        ):
            if thread is not None:
                ResourceManager().register_thread(thread)
                thread.start()


        decoding: bool = True
        err: bool = False
        encoded: int = 0

        ask_to_end: bool = False
        framecount: int = self.scene['dst']['count']
        while True:
            if not decoding:
                # All frames encoded, send poison pill to all inference threads
                if e_thread.encoded == framecount and ask_to_end:
                    print("[V][C] All frames encoded, send poison pill to encoder")
                    e_thread.put_frame(None)
                    ask_to_end = False

                # Encoding has ended
                if (
                    not d_thread.is_alive()
                    # and inference_threads_ended
                    and not e_thread.is_alive()
                ):
                    print("[V][C] All frames encoded, encoder has ended")
                    encoded = e_thread.encoded
                    break
                time.sleep(0.0001)
                continue

            time.sleep(0.0001)
            # Detect end of decoding
            if not d_thread.is_alive() and decoding:
                print("[V][C] decoder has ended")
                err, message = d_thread.error_encountered()
                if err:
                    print(red(message))
                    break
                else:
                    # Send a poison pill in each inference thread
                    # for thread in i_threads:
                    #     if thread is not None:
                    #         print(f"[V][C] sent posion pill to {thread.name}")
                    #         thread.put_frame(None)
                    decoding = False
                    ask_to_end = True
                    print(f"[V][C] wait for {framecount} to be encoded")

            time.sleep(0.0001)
            if not e_thread.is_alive() and d_thread.is_alive():
                print(red("Error: the encoder encountered an unexpected error"))
                err = True
                break

            time.sleep(0.0001)

        # Stop remaining threads if not already stopped (error cases)
        for thread in i_threads:
            if thread is not None and thread.is_alive():
                # print(f"[V][C] sent a poison pill at the end because still inference threads")
                thread.stop(force=True)
                while thread.is_alive():
                    time.sleep(0.02)


        for thread in (d_thread, *i_threads, e_thread):
            if thread is not None and thread.is_alive():
                thread.stop(force=True)
                time.sleep(0.5)

        torch.cuda.empty_cache()

        for thread in (d_thread, *i_threads, e_thread):
            if thread is not None and thread.is_alive():
                print(red(f"Error: {thread.name} is still alive"))

        return err, encoded

