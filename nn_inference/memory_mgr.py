
from dataclasses import dataclass

import numpy as np
from .resource_mgr import Singleton
from .cupy_utils import HostDeviceMemory, allocate_memory


# TODO: for non cuda filters


class SyncMemoryMgr(metaclass=Singleton):

    def __init__(self) -> None:
        # Memory used for synchronous operations
        self.sync_in_max_nbytes: int = 0
        self.sync_in_dtype: np.dtype = np.uint16
        self.sync_htod_mem: HostDeviceMemory | None = None


    def allocate_sync_memory(self) -> None:
        """Allocate memory for synchronous operations"""
        if self.sync_in_max_nbytes == 0:
            return

        # In and Out max shapes used for memory allocation
        sync_in_max_shape: tuple[int, int, int] = (self.sync_in_max_nbytes, 1, 1)

        # Allocate Host memory
        self.sync_htod_mem = allocate_memory(
            sync_in_max_shape, self.in_dtype, self.htod_cuda_stream
        )
