from collections import deque
import math
import numpy as np
from pprint import pprint
from threading import Event, Lock
import time
from typing import Any, TypedDict
import torch
from pynnlib import (
    flip_r_b_channels,
    to_nchw,
)
from ..resource_mgr import NnFrame, BaseThread
from nn_inference import HostDeviceMemory
from utils.p_print import *
from utils.images_io import load_image



class ImgReaderThreadConfig(TypedDict):
    htod_mem: HostDeviceMemory
    frames: deque
    # Write to GPU
    cuda_stream: Any
    tensor_dtype: str
    device: str



class ImgReaderThread(BaseThread):
    def __init__(
        self,
        config: ImgReaderThreadConfig
    ) -> None:
        super().__init__()
        self._stop_event: Event = Event()
        self._lock: Lock = Lock()
        self._lock.acquire(blocking=False)

        # push bank no which is ready for inference
        self.config: ImgReaderThreadConfig = config

        print(lightgreen("[V][D] ImgReaderThread, config="))
        # pprint(self.config)
        pprint(self.config['htod_mem'])


    def run(self) -> None:
        cuda_stream = self.config['cuda_stream']
        if cuda_stream is None:
            return self.run_cpu()

        verbose: bool = False

        # Tensor
        tensor_dtype = self.config['tensor_dtype']
        htod_mem: HostDeviceMemory = self.config['htod_mem']
        d_tensor = htod_mem.device
        frames: deque = self.config['frames']

        # Image reader is BGR, inference in RGB
        flip_r_b: bool = True
        np_flip: bool = False

        # Flow control
        remaining_frame_count: int = len(frames)

        f_no: int = 0
        with cuda_stream:
            while (
                not self._stop_event.is_set()
                and len(frames) > 0
            ):
                frame: NnFrame = frames.popleft()
                img = load_image(frame.in_img_fp)
                if verbose:
                    print(lightgreen(f"[V][D] Read image: {frame.in_img_fp}"))
                img_shape, in_dtype = img.shape, img.dtype
                h_img: np.ndarray = np.frombuffer(
                    htod_mem.host,
                    dtype=in_dtype,
                    count=math.prod(img_shape)
                )

                # Change pixel value range
                divisor: float = (
                    float(np.iinfo(in_dtype).max)
                    if in_dtype != tensor_dtype
                    else 1.
                )

                if flip_r_b and np_flip:
                    img = flip_r_b_channels(img)

                # Wait for release
                self._lock.acquire(blocking=True)
                if self._stop_event.is_set():
                    return

                np.copyto(h_img, img.ravel())
                d_tensor = htod_mem.device
                if verbose:
                    print(lightgreen(f"[V][D] h_img: {h_img.shape}, {h_img.dtype}"))
                    print(lightgreen(f"[V][D] d_tensor: {d_tensor.shape}, {d_tensor.dtype}"))
                d_tensor.set(h_img)
                d_tensor = d_tensor.reshape(img_shape)

                if flip_r_b and not np_flip:
                    d_tensor = flip_r_b_channels(d_tensor)

                d_tensor = to_nchw(d_tensor)

                if verbose:
                    print(lightgreen(f"[V][D] change tensor type to {tensor_dtype}"))
                d_tensor = d_tensor.astype(cp.float32)
                if divisor != 1.:
                    d_tensor /= divisor
                d_tensor = d_tensor.astype(tensor_dtype)

                time.sleep(0.00001)
                cuda_stream.synchronize()

                remaining_frame_count -= 1
                if verbose:
                    print(f"[V][D] ({lightgreen(f_no)}) ({remaining_frame_count}) Put tensor in queue: {d_tensor.data_ptr()}, {d_tensor.shape}, {d_tensor.dtype}")
                f_no += 1

                frame.tensor = d_tensor
                frame.tensor_shape = d_tensor.shape
                self.consumer.put_frame(frame)

        if verbose:
            print(lightgreen(f"[V][D] Ended"))
        self.consumer.put_frame(None)


    def stop(self, force: bool=False) -> None:
        self._stop_event.set()
        if force:
            self.release()


    def release(self) -> None:
        try:
            self._lock.release()
        except:
            pass


    def set_produce_flag(self) -> None:
        self.release()


    def run_cpu(self) -> None:
        tensor_dtype = self.config['tensor_dtype']
        frames: deque = self.config['frames']
        device: str = 'cpu'
        # Image reader is BGR, inference in RGB
        flip_r_b: bool = True
        np_flip: bool = True
        f_no: int = 0

        # Flow control
        remaining_frame_count: int = len(frames)
        while (
            not self._stop_event.is_set()
            and len(frames) > 0
        ):
            frame: NnFrame = frames.popleft()
            # print(lightgreen(f"[V][D] Read image: {frame.in_img_fp}"))
            img = load_image(frame.in_img_fp)
            img_shape, in_dtype = img.shape, img.dtype

            # Change pixel value range
            divisor: float = (
                float(np.iinfo(in_dtype).max)
                if in_dtype != tensor_dtype
                else 1.
            )

            # Wait for release
            # print(lightgreen(f"[V][D] img: {img.shape}, {img.dtype}, waiting for unlock"))
            self._lock.acquire(blocking=True)
            if self._stop_event.is_set():
                return

            d_tensor: torch.Tensor = torch.from_numpy(np.ascontiguousarray(img))
            d_tensor = d_tensor.to(device, dtype=torch.float32)
            # print(lightgreen(f"[V][D] d_tensor: {d_tensor.shape}, {d_tensor.dtype}"))

            d_tensor = d_tensor.reshape(img_shape)
            d_tensor = flip_r_b_channels(d_tensor)
            d_tensor = to_nchw(d_tensor).contiguous()

            # print(lightgreen(f"[V][D] change tensor type to {tensor_dtype}"))
            if divisor != 1.:
                d_tensor /= divisor

            time.sleep(0.00001)

            remaining_frame_count -= 1

            # print(f"[V][D] ({lightgreen(f_no)}) ({remaining_frame_count}) Put tensor in queue: {d_tensor.shape}, {d_tensor.dtype}")
            f_no += 1

            frame.tensor = d_tensor
            self.consumer.put_frame(frame)

        # print(lightgreen(f"[V][D] Ended"))
        self.consumer.put_frame(None)

