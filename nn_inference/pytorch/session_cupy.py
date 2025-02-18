from typing import Any
import cupy as cp
import math
import numpy as np
from pynnlib import (
    PytorchModel,
    PyTorchSession,
)
from pynnlib.nn_types import Idtype
from pynnlib.utils.cp_tensor import (
    MemcpyKind,
    to_nchw_cp,
    to_hwc_cp
)
import torch
from torch.utils.dlpack import from_dlpack, to_dlpack


def allocate_memory(
    model: PytorchModel,
    shape: tuple[int],
    dtype: np.dtype
) -> tuple[Any, Any]:
    # Allocate a fixed amount of memory
    #   ensure all images will fit inside this
    scale = model.scale

    # Inference shapes
    in_h, in_w, in_nc = shape
    in_dtype_size = np.dtype(dtype).itemsize
    print(f"dtype: {dtype}")
    print(f"in_dtype_size: {in_dtype_size}")
    h_input_nbytes = in_h * in_w * in_nc * in_dtype_size

    out_h, out_w, out_nc = in_h * scale, in_w * scale, model.out_nc
    out_dtype_size = in_dtype_size
    h_output_nbytes = out_h * out_w * out_nc * out_dtype_size

    h_input = cp.cuda.alloc_pinned_memory(h_input_nbytes)
    h_output = cp.cuda.alloc_pinned_memory(h_output_nbytes)

    print(f"[V] h_input: {h_input_nbytes}bytes")
    print(f"[V] h_output: {h_output_nbytes}bytes")

    return [h_input, h_output]



class PyTorchCuPySession(PyTorchSession):
    def __init__(self, model: PytorchModel):
        super().__init__(model=model)
        self.h_input = None
        self.h_output = None
        self._infer_stream = None


    @property
    def infer_stream(self):
        # -> cp.cuda.Stream
        return self._infer_stream


    @infer_stream.setter
    def infer_stream(self, stream) -> None:
        # -> cp.cuda.Stream
        self._infer_stream = stream


    def initialize(
        self,
        device: str,
        dtype: Idtype = 'fp16',
        memalloc: bool = True,
        in_max_shape: tuple[int, int, int] | None = None,
        warmup: bool = False
    ) -> None:
        super().initialize(device=device, dtype=dtype, warmup=warmup)

        if "cuda" in self.device:
            self._process_fct = self.process_cupy

            if memalloc and in_max_shape is not None:
                self.h_input, self.h_output = allocate_memory(
                    self.model, in_max_shape,  np.float32
                )
        else:
            raise NotImplementedError(f"Device not supported: {self.device}")


    @torch.inference_mode()
    def process_cupy(
        self,
        in_img: np.ndarray,
        **kwargs
    ) -> np.ndarray | None:
        """This is an example to perform a synchronous inference
        (from HtoD to DtoH)
        input/output images: uint8
        """
        in_dtype = in_img.dtype
        scale = self.model.scale
        tensor_dtype = np.float16 if 'fp16' in self.model.dtypes else np.float32

        # Shapes
        in_nc = len(in_img.shape)
        in_nc = 2 if in_nc < 3 else in_nc
        in_h, in_w = in_img.shape[:2]

        out_h, out_w, out_nc = in_h * scale, in_w * scale, self.model.out_nc
        out_shape = (out_h, out_w, out_nc)

        # HtoD
        h_input = np.frombuffer(
            self.h_input,
            dtype=in_img.dtype,
            count=in_h * in_w * in_nc
        ).reshape(in_img.shape)
        h_input[...] = np.ascontiguousarray(in_img)
        x_gpu_in = cp.empty(in_img.shape, in_img.dtype)
        x_gpu_in.set(h_input)
        x_gpu_in = cp.flip(x_gpu_in, 2)
        x_gpu_in = to_nchw_cp(x_gpu_in)

        x_gpu_in = x_gpu_in.astype(tensor_dtype)
        # if in_dtype != np.float32:
        #     dtype_max_value = float(MAX_INT_VALUES_BY_DTYPE.get(in_dtype.name, 1.0))
        #     x_gpu_in /= dtype_max_value
        in_tensor = from_dlpack(x_gpu_in.toDlpack())

        # Perform the inference
        out_tensor: torch.Tensor = self.module(in_tensor)

        x_gpu_out = cp.from_dlpack(to_dlpack(out_tensor))
        # if in_dtype != np.float32:
        #     dtype_max_value = float(MAX_INT_VALUES_BY_DTYPE.get(in_dtype.name, 1.0))
        #     x_gpu_out *= dtype_max_value
        x_gpu_out = x_gpu_out.astype(in_dtype)
        x_gpu_out = to_hwc_cp(x_gpu_out)
        x_gpu_out = cp.flip(x_gpu_out, 2)
        x_gpu_out = cp.clip(x_gpu_out, 0, 1.0, out=x_gpu_out)

        # DtoH
        x_gpu_out = cp.ravel(x_gpu_out)
        cp.cuda.runtime.memcpy(
            int(self.h_output),
            x_gpu_out.data.ptr,
            x_gpu_out.nbytes,
            MemcpyKind.DeviceToHost
        )

        return np.frombuffer(
            self.h_output,
            dtype=in_dtype,
            count=math.prod(out_shape)
        ).reshape(out_shape)

