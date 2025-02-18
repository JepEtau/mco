import math
import os
import cupy as cp
import numpy as np
from pprint import pprint
from queue import Queue
import subprocess
import sys
from threading import Event
import torch
from nn_inference.resource_mgr import NnFrame, RlgThread
from utils.images_io import write_image
from utils.mco_types import Scene
from utils.media import ChannelOrder, FShape
from typing import Any, Callable, Type, TypedDict

from pynnlib import (
    is_cuda_available,
    flip_r_b_channels,
    MemcpyKind,
    to_hwc,
)
from nn_inference import HostDeviceMemory
from utils.p_print import *
from utils.path_utils import path_split



class ImgWriterThreadConfig(TypedDict):
    # The FFMpeg command MUST  not contain the output video file
    command: list[str]
    # Read from GPU bank
    cuda_stream: Any
    tensor_dtype: str
    dtoh_mem: HostDeviceMemory
    # Write to stdout
    img_shape: FShape
    img_dtype: str
    img_c_order: ChannelOrder



class ImgWriterThread(RlgThread):
    def __init__(
        self,
        config: ImgWriterThreadConfig,
    ) -> None:
        super().__init__()
        self._stop_event: Event = Event()

        self.in_queue: Queue = Queue(4)
        self.config = config
        self._written: int = 0
        self.callback: Callable = None
        print(purple("[V][W] Init ImgWriterThread"))
        pprint(config['dtoh_mem'])


    def run(self) -> None:
        cuda_stream = self.config['cuda_stream']
        if cuda_stream is None:
            return self.run_cpu()

        verbose: bool = False
        in_queue: Queue = self.in_queue
        tensor_dtype: cp.dtype = cp.dtype(self.config['tensor_dtype'])
        img_cp_dtype: cp.dtype = cp.dtype(self.config['img_dtype'])

        img_shape: FShape = self.config['img_shape']
        img_dtype: np.dtype = np.dtype(self.config['img_dtype'])
        img_ncount: int = math.prod(img_shape)
        img_nbytes: int = img_ncount * np.dtype(img_dtype).itemsize

        # Change pixel value range
        multiplier: float = 1.
        if tensor_dtype != img_cp_dtype:
            num = float(np.iinfo(img_cp_dtype).max) if tensor_dtype in (cp.float32, cp.float16) else 1.
            denum = float(np.iinfo(tensor_dtype).max) if img_cp_dtype == np.float32 else 1.
            multiplier: float = num / denum

        # Memory Banks in GPU, as np/cp ndarray
        dtoh_mem: HostDeviceMemory = self.config['dtoh_mem']

        # host mem banks
        if img_nbytes > dtoh_mem.nbytes:
            raise "[W] Input HostDevice memory is too small"

        flip_r_b: bool = self.config['img_c_order'] != 'bgr'
        self._written: int = 0
        current_scene: Scene | None = None
        # try:
        with cuda_stream:
            while not self._stop_event.is_set():
                if verbose:
                    print(purple("[V][W] Wait out tensor"))
                input = in_queue.get(block=True)
                # if input is None:
                    # print(purple("[V][W] Received Null tensor"))
                if input is None or self._stop_event.is_set():
                    if self.progress_thread is not None:
                        self.progress_thread.put(self._written, force=True)
                    if self.consumer is not None:
                        self.consumer.put(current_scene)
                    break

                frame: NnFrame = input

                if current_scene is None:
                    current_scene = frame.scene
                elif current_scene is not frame.scene:
                    if verbose:
                        print(purple(f"[V][W] ask to create : {frame.out_video_fp}"))
                    self.consumer.put(current_scene)
                    current_scene = frame.scene

                tensor, tensor_shape = frame.tensor, frame.tensor_shape
                if verbose:
                    print(purple(f"[V][W] Received: {tensor.data.ptr}, {tensor.shape}, {tensor.dtype}, {tensor_shape}"))

                tensor = cp.reshape(tensor, tensor_shape)
                tensor = cp.clip(tensor, 0, 1.0, tensor)
                tensor = to_hwc(tensor)
                if flip_r_b:
                    # print("[V][W] flip out tensor RB")
                    tensor = flip_r_b_channels(tensor)

                tensor = tensor.astype(cp.float32, copy=False)
                if multiplier != 1.:
                    tensor *= multiplier

                tensor = tensor.astype(img_cp_dtype, copy=False)
                if verbose:
                    print(purple(f"[V][W] copy to Host: {tensor.data.ptr}, {tensor.shape}, {tensor.dtype}"))
                out_img_shape: tuple[int, int, int] = tensor.shape
                tensor = cp.ravel(tensor)
                cp.cuda.runtime.memcpyAsync(
                    int(dtoh_mem.host),
                    tensor.data.ptr,
                    tensor.nbytes,
                    MemcpyKind.DeviceToHost,
                    cuda_stream.ptr
                )
                cuda_stream.synchronize()
                out_img: np.ndarray = np.frombuffer(
                    dtoh_mem.host,
                    dtype=img_dtype,
                    count=math.prod(out_img_shape)
                ).reshape(out_img_shape)
                if verbose:
                    print(purple(f"[V][W] write to image: {out_img.shape}, {out_img.dtype}"))
                write_image(f"A:\\tmp\\aaa\\out_{self._written:05}.png", out_img)
                del frame.tensor
                self._written += 1

                if self.progress_thread is not None:
                    self.progress_thread.put(self._written)

        # except Exception as e:
        #     print(purple(f"[W] Failed to add a frame to the image writer: {type(e)}"), flush=True)

        if self.progress_thread is not None:
            self.progress_thread.put(None)

        if self.consumer is not None:
            self.consumer.put(None)



    def stop(self, force: bool=False) -> None:
        self._stop_event.set()
        if force:
            while not self.in_queue.empty():
                self.in_queue.get_nowait()
        self.put_frame(None)


    def put_frame(self, frame: NnFrame) -> bool:
        self.in_queue.put(frame)
        return True


    @property
    def written(self) -> int:
        return self._written


    def set_progress_callback(self, function: Callable) -> None:
        self.callback = function


    def run_cpu(self) -> None:
        verbose: bool = True
        in_queue: Queue = self.in_queue
        tensor_dtype: np.dtype = np.dtype(self.config['tensor_dtype'])
        img_np_dtype: np.dtype = np.dtype(self.config['img_dtype'])

        # Change pixel value range
        multiplier: float = 1.
        if tensor_dtype != img_np_dtype:
            num = float(np.iinfo(img_np_dtype).max) if tensor_dtype in (np.float32, np.float16) else 1.
            denum = float(np.iinfo(tensor_dtype).max) if img_np_dtype == np.float32 else 1.
            multiplier: float = num / denum

        if verbose:
            print(purple("[V][W] Image writer, config:"))
            pprint(self.config)
            print(purple(f"[V][W] multiplier={multiplier}"))

        # flip_r_b: bool = self.config['img_c_order'] != 'bgr'
        flip_r_b = True
        self._written: int = 0
        current_scene: Scene | None = None
        # try:
        while not self._stop_event.is_set():
            if verbose:
                print(purple("[V][W] Wait out tensor"))
            input = in_queue.get(block=True)
            if input is None or self._stop_event.is_set():
                if self.progress_thread is not None:
                    self.progress_thread.put(self._written, force=True)
                if self.consumer is not None:
                    self.consumer.put(current_scene)
                break

            frame: NnFrame = input

            if current_scene is None:
                current_scene = frame.scene
            elif current_scene is not frame.scene:
                if verbose:
                    print(purple(f"[V][W] ask to create : {frame.out_video_fp}"))
                self.consumer.put(current_scene)
                current_scene = frame.scene

            tensor: torch.Tensor = frame.tensor
            tensor_shape = frame.tensor_shape
            if verbose:
                print(purple(f"[V][W] Received: {tensor.shape}, {tensor.dtype}, {tensor_shape}"))

            tensor = np.reshape(tensor, tensor_shape)
            tensor = np.clip(tensor, 0, 1.0)
            tensor = to_hwc(tensor)
            if flip_r_b:
                if verbose:
                    print(purple("[V][W] flip out tensor RB"))
                tensor = flip_r_b_channels(tensor)

            if multiplier != 1.:
                tensor *= multiplier

            out_img: np.ndarray = tensor.detach().cpu().numpy()
            out_img = out_img.astype(img_np_dtype)
            if verbose:
                print(purple(f"[V][W] ({self._written}) write image: {out_img.shape}, {out_img.dtype}"))
                # print(purple(f"[V][W] min={np.min(out_img)}, max={np.max(out_img)}"))
            write_image(f"./cache/aaa/out_{self._written:05}.png", out_img)
            self._written += 1

            if self.progress_thread is not None:
                self.progress_thread.put(self._written)

        # except Exception as e:
        #     print(purple(f"[W] Failed to add a frame to the encoder: {type(e)}"), flush=True)

        if self.progress_thread is not None:
            self.progress_thread.put(None)

        if self.consumer is not None:
            self.consumer.put(None)

        if verbose:
            print(purple(f"[V][W] Subprocess ended"))
