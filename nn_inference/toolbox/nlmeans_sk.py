import math
import time
from nn_inference.cupy_utils import HostDeviceMemory
from nn_inference.resource_mgr import NnFrame, Singleton
from skimage.restoration import denoise_nl_means
import numpy as np
import cupy as cp
from pynnlib import (
    flip_r_b_channels,
    MemcpyKind,
    to_hwc,
    to_nchw,
)
from torch import Tensor
from utils.p_print import *



class _FilterMemManager(metaclass=Singleton):
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





def nlmeans_sk(
    frame: NnFrame,
    params: str | None,
) -> NnFrame:
    verbose : bool = True

    args: dict[str, int] = {}
    param_list: list[str] = params.split(":")
    if len(param_list) >= 1:
        args['h'] = float(param_list[0])
    if len(param_list) >= 2:
        args['patch_size'] = int(param_list[1])
    if len(param_list) >= 3:
        args['patch_distance'] = int(param_list[2])


    # Get tensor from frame
    tensor: Tensor = frame.tensor
    tensor_shape = frame.tensor_shape
    if verbose:
        print(
            purple(f"[V][F] NLmeans:"),
            f"{tensor.shape}, {tensor.dtype}, {tensor_shape}"
        )

    # Cuda: DtoH, HtoD and CUDA stream
    filter_mem_manager = _FilterMemManager()
    if filter_mem_manager.cuda_stream is None:
        print(
            purple(f"[V][F] Initialize memory")
        )
        in_out_nbytes: int = math.prod(tensor.shape)
        filter_mem_manager.set_in_out_max_nbytes(in_nbytes=in_out_nbytes, out_nbytes=in_out_nbytes)
        filter_mem_manager.set_dtypes(in_dtype=cp.float32, out_dtype=cp.float32)
        filter_mem_manager.initialize()

    cuda_stream = filter_mem_manager.cuda_stream
    htod_mem: HostDeviceMemory = filter_mem_manager.htod_mem
    dtoh_mem: HostDeviceMemory = filter_mem_manager.dtoh_mem

    # Copy tensor to Host, Filter and copy the result to the Device
    with cuda_stream:
        in_dtype = tensor.dtype
        tensor = cp.reshape(tensor, tensor_shape)
        tensor = cp.clip(tensor, 0, 1.0, tensor)
        tensor = to_hwc(tensor)
        tensor = flip_r_b_channels(tensor)
        tensor = tensor.astype(cp.float32, copy=False)

        cp.cuda.runtime.memcpy(
            int(dtoh_mem.host),
            tensor.data.ptr,
            tensor.nbytes,
            MemcpyKind.DeviceToHost
        )
        in_img: np.ndarray = np.frombuffer(
            dtoh_mem.host,
            dtype=np.float32,
            count=math.prod(tensor.shape)
        )
        in_img = in_img.reshape(tensor.shape)

        # Apply filter on the numpy image
        out_img = denoise_nl_means(
            in_img, **args, fast_mode=True, channel_axis=-1
        )

        h_img: np.ndarray = np.frombuffer(
            htod_mem.host, dtype=np.float32, count=math.prod(out_img.shape)
        )
        np.copyto(h_img, out_img.ravel())
        d_tensor: cp.ndarray = cp.ndarray(
            h_img.shape, dtype=h_img.dtype, memptr=htod_mem.device.data
        )
        d_tensor.set(h_img)

        d_tensor = d_tensor.reshape(in_img.shape)
        d_tensor = flip_r_b_channels(d_tensor)
        d_tensor = to_nchw(d_tensor)
        d_tensor = d_tensor.astype(in_dtype)
        d_tensor = d_tensor.reshape(frame.tensor.shape)

        time.sleep(0.00001)
        cuda_stream.synchronize()

    if verbose:
        print(
            purple(f"[V][F]  ->"),
            f"{d_tensor.shape}, {d_tensor.dtype}, {tensor_shape}"
        )


    frame.tensor = d_tensor

    return frame
