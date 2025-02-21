from typing import Any
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


