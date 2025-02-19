from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Any
import cupy as cp
import numpy as np
from torch import Tensor, UntypedStorage
from utils.media import FShape


# pinned_memory_pool = cp.cuda.PinnedMemoryPool()
# cp.cuda.set_pinned_memory_allocator(pinned_memory_pool.malloc)



@dataclass
class HostDeviceMemory:
    # commented to refactory without breaking, it will raise an error
    # host: Tensor
    # device: Tensor
    nbytes: int



# def allocate_memory(
#     shape: FShape,
#     dtype: np.dtype,
#     stream: Any | None = None
# ) -> HostDeviceMemory:
#     nbytes = math.prod(shape) * np.dtype(dtype).itemsize

#     if stream is not None:
#         with stream:
#             h_mem = cp.cuda.alloc_pinned_memory(nbytes)
#             # d_mem = cp.cuda.MemoryPointer(cp.cuda.Memory(nbytes), 0)
#             d_mem = cp.empty((math.prod(shape),), dtype)
#     else:
#         h_mem = cp.cuda.alloc_pinned_memory(nbytes)
#         # d_mem = cp.cuda.MemoryPointer(cp.cuda.Memory(nbytes), 0)
#         d_mem = cp.empty((math.prod(shape),), dtype)

#     # print(f"[V] allocated: host={h_mem}, device={d_mem}, {nbytes}")
#     return HostDeviceMemory(
#         host=h_mem,
#         device=d_mem,
#         nbytes=nbytes
#     )

