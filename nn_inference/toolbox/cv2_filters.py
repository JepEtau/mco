import math
import time

import cv2
from nn_inference.cupy_utils import HostDeviceMemory, allocate_memory
from nn_inference.resource_mgr import NnFrame, Singleton
import numpy as np
import cupy as cp
from pynnlib.utils.cp_tensor import (
    flip_r_b_channels_cp,
    MemcpyKind,
    to_hwc_cp,
    to_nchw_cp,
)
from torch import Tensor
from utils.np_dtypes import np_to_float32, np_to_uint8
from utils.p_print import *



def bilateral_filter(
    img: np.ndarray,
    radius: int,
    sigmaColor: float,
    sigmaSpace: float
):
    return cv2.bilateralFilter(
        src=img,
        d=(2 * radius + 1),
        sigmaColor=sigmaColor,
        sigmaSpace=sigmaSpace
    )


def cv2_nlmeans_(
    frame: NnFrame,
    params: str | None,
) -> NnFrame:
    verbose : bool = False

    h: float = 3
    h_color: float = 3
    patch_window_size: float = 7
    search_window_size: float = 21

    if params is not None:
        param_list: list[str] = params.split(":")
        if len(param_list) == 4:
            h, h_color = list(map(float, param_list[:2]))
            patch_window_size, search_window_size = list(map(int, param_list[2:]))

    # Get tensor from frame
    tensor: Tensor = frame.tensor
    if verbose:
        print(purple(f"[V][F] cv2 bilateral:"))
        print(
            purple(f"[V][F]  in_tensor:"),  f"{tensor.shape}, {tensor.dtype}"
        )

    # Cuda: DtoH, HtoD and CUDA stream
    filter_mem_manager = FilterMemManager()
    if filter_mem_manager.cuda_stream is None:
        print(
            purple(f"[V][F] Initialize memory")
        )
        in_out_nbytes: int = math.prod(tensor.shape)
        filter_mem_manager.set_in_out_max_nbytes(
            in_nbytes=in_out_nbytes,
            out_nbytes=in_out_nbytes
        )
        filter_mem_manager.set_dtypes(
            in_dtype=cp.float32,
            out_dtype=cp.float32
        )
        filter_mem_manager.initialize()

    cuda_stream = filter_mem_manager.cuda_stream
    htod_mem: HostDeviceMemory = filter_mem_manager.htod_mem
    dtoh_mem: HostDeviceMemory = filter_mem_manager.dtoh_mem

    # Copy tensor to Host, Filter and copy the result to the Device
    raise NotImplementedError("tensor is not a cupy tensor")
    with cuda_stream:
        in_dtype = tensor.dtype
        tensor = to_hwc_cp(tensor)
        tensor = flip_r_b_channels_cp(tensor)
        d_img = tensor.astype(cp.float32)
        in_img_shape: tuple[int, int, int] = d_img.shape
        if verbose:
            print(purple(f"[V][F]   d_img"), f"{d_img.shape}, {d_img.dtype}, {d_img.nbytes}")

        d_img = cp.ravel(d_img)
        cp.cuda.runtime.memcpy(
            int(dtoh_mem.host),
            d_img.data.ptr,
            d_img.nbytes,
            MemcpyKind.DeviceToHost
        )
        in_img: np.ndarray = np.frombuffer(
            dtoh_mem.host,
            dtype=np.float32,
            count=math.prod(d_img.shape)
        )
        in_img = in_img.reshape(in_img_shape)
        if verbose:
            print(purple(f"[V][F]   in_img"), f"{in_img.shape}, {in_img.dtype}")

        # Apply filter on the numpy image
        out_img = np_to_float32(
            cv2.fastNlMeansDenoisingColored(
                src=np_to_uint8(in_img),
                dst=None,
                h=h,
                hColor=h_color,
                templateWindowSize=patch_window_size,
                searchWindowSize=search_window_size,
            )
        )



        if verbose:
            print(purple(f"[V][F]   out_img"), f"{out_img.shape}, {out_img.dtype}")

        h_img: np.ndarray = np.frombuffer(
            htod_mem.host,
            dtype=np.float32,
            count=math.prod(out_img.shape)
        )
        if verbose:
            print(purple(f"[V][F]   h_img"), f"{h_img.shape}, {h_img.dtype}")

        np.copyto(h_img, out_img.ravel())
        d_tensor: cp.ndarray = cp.ndarray(
            h_img.shape,
            dtype=h_img.dtype,
            memptr=htod_mem.device.data
        )
        d_tensor.set(h_img)

        d_tensor = d_tensor.reshape(out_img.shape)
        d_tensor = flip_r_b_channels_cp(d_tensor)
        d_tensor = to_nchw_cp(d_tensor)
        d_tensor = d_tensor.astype(in_dtype)
        if verbose:
            print(purple(f"[V][F]   d_tensor"), f"{d_tensor.shape}, {d_tensor.dtype}")

        time.sleep(0.00001)
        cuda_stream.synchronize()

    if verbose:
        print(
            purple(f"[V][F]  ->"),  f"{d_tensor.shape}, {d_tensor.dtype}"
        )


    frame.tensor = d_tensor

    return frame




class FilterMemManager(metaclass=Singleton):
    def __init__(self) -> None:
        self._device: str = "cuda:0"

        self.in_max_nbytes: int = 0
        self.out_max_nbytes: int = 0
        self.in_dtype: np.dtype = np.uint16
        self.out_dtype: np.dtype = np.uint16

        self.cuda_stream = None

        self.htod_mem: HostDeviceMemory | None = None
        self.dtoh_mem: HostDeviceMemory | None = None


    @property
    def device(self) -> str:
        return self._device


    @device.setter
    def device(self, device: str) -> None:
        self._device = device


    def set_in_out_max_nbytes(self, in_nbytes: int, out_nbytes: int):
        self.in_max_nbytes = in_nbytes
        self.out_max_nbytes = out_nbytes


    def set_dtypes(self, in_dtype: np.dtype, out_dtype: np.dtype) -> None:
        self.in_dtype = in_dtype
        self.out_dtype = out_dtype


    def initialize(self) -> None:
        # set_cuda_device(self.device)
        self.cuda_stream = cp.cuda.stream.Stream(non_blocking=False)
        self.allocate_memory()


    def allocate_memory(self) -> None:
        # In and Out max shapes used for memory allocation
        in_max_shape: tuple[int, int, int] = (self.in_max_nbytes, 1, 1)
        out_max_shape: tuple[int, int, int] = (self.out_max_nbytes, 1, 1)

        if (
            self.in_max_nbytes == 0
            or self.out_max_nbytes == 0
        ):
            raise ValueError(
                f"Cannot allocate memory: in: {self.in_max_nbytes}B, out: {self.out_max_nbytes}B"
            )

        # Allocate Host memory
        self.htod_mem = allocate_memory(in_max_shape, self.in_dtype, self.cuda_stream)
        self.dtoh_mem = allocate_memory(out_max_shape, self.out_dtype, self.cuda_stream)




def cv2_bilateral_(
    frame: NnFrame,
    params: str | None,
) -> NnFrame:
    verbose : bool = False

    param_list: list[str] = params.split(":")
    radius, sigma_color, sigma_space = 4, 11, 11
    if len(param_list) >= 1:
        radius = int(param_list[0])
    if len(param_list) >= 2:
        sigma_color = float(param_list[1])
    if len(param_list) >= 3:
        sigma_space = float(param_list[2])


    # Get tensor from frame
    tensor: Tensor = frame.tensor
    if verbose:
        print(purple(f"[V][F] cv2 bilateral:"))
        print(
            purple(f"[V][F]  in_tensor:"),  f"{tensor.shape}, {tensor.dtype}"
        )

    # Cuda: DtoH, HtoD and CUDA stream
    filter_mem_manager = FilterMemManager()
    if filter_mem_manager.cuda_stream is None:
        print(
            purple(f"[V][F] Initialize memory")
        )
        in_out_nbytes: int = math.prod(tensor.shape)
        filter_mem_manager.set_in_out_max_nbytes(
            in_nbytes=in_out_nbytes,
            out_nbytes=in_out_nbytes
        )
        filter_mem_manager.set_dtypes(
            in_dtype=cp.float32,
            out_dtype=cp.float32
        )
        filter_mem_manager.initialize()

    cuda_stream = filter_mem_manager.cuda_stream
    htod_mem: HostDeviceMemory = filter_mem_manager.htod_mem
    dtoh_mem: HostDeviceMemory = filter_mem_manager.dtoh_mem

    # Copy tensor to Host, Filter and copy the result to the Device
    raise NotImplementedError("tensor is not a cupy tensor")
    with cuda_stream:
        in_dtype = tensor.dtype
        tensor = to_hwc_cp(tensor)
        tensor = flip_r_b_channels_cp(tensor)
        d_img = tensor.astype(cp.float32)
        in_img_shape: tuple[int, int, int] = d_img.shape
        if verbose:
            print(purple(f"[V][F]   d_img"), f"{d_img.shape}, {d_img.dtype}, {d_img.nbytes}")

        d_img = cp.ravel(d_img)
        cp.cuda.runtime.memcpy(
            int(dtoh_mem.host),
            d_img.data.ptr,
            d_img.nbytes,
            MemcpyKind.DeviceToHost
        )
        in_img: np.ndarray = np.frombuffer(
            dtoh_mem.host,
            dtype=np.float32,
            count=math.prod(d_img.shape)
        )
        in_img = in_img.reshape(in_img_shape)
        if verbose:
            print(purple(f"[V][F]   in_img"), f"{in_img.shape}, {in_img.dtype}")

        # Apply filter on the numpy image
        out_img = cv2.bilateralFilter(
            src=in_img,
            d=(2 * radius + 1),
            sigmaColor=sigma_color,
            sigmaSpace=sigma_space
        )

        if verbose:
            print(purple(f"[V][F]   out_img"), f"{out_img.shape}, {out_img.dtype}")

        h_img: np.ndarray = np.frombuffer(
            htod_mem.host,
            dtype=np.float32,
            count=math.prod(out_img.shape)
        )
        if verbose:
            print(purple(f"[V][F]   h_img"), f"{h_img.shape}, {h_img.dtype}")

        np.copyto(h_img, out_img.ravel())
        d_tensor: cp.ndarray = cp.ndarray(
            h_img.shape,
            dtype=h_img.dtype,
            memptr=htod_mem.device.data
        )
        d_tensor.set(h_img)

        d_tensor = d_tensor.reshape(out_img.shape)
        d_tensor = flip_r_b_channels_cp(d_tensor)
        d_tensor = to_nchw_cp(d_tensor)
        d_tensor = d_tensor.astype(in_dtype)
        if verbose:
            print(purple(f"[V][F]   d_tensor"), f"{d_tensor.shape}, {d_tensor.dtype}")

        time.sleep(0.00001)
        cuda_stream.synchronize()

    if verbose:
        print(
            purple(f"[V][F]  ->"),  f"{d_tensor.shape}, {d_tensor.dtype}"
        )


    frame.tensor = d_tensor

    return frame
