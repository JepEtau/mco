import cupy as cp
import numpy as np
from pprint import pprint

import torch
from pynnlib import is_tensorrt_available
from pynnlib.nn_tensor_rt.inference.session import (
    TensorRtSession,
    get_trt_logger,
)
from utils.p_print import yellow
if is_tensorrt_available():
    import tensorrt as trt

from typing import Any

from pynnlib.model import TrtModel
from pynnlib.session import set_cupy_cuda_device


class TensorRtCupySession(TensorRtSession):
    def __init__(
        self,
        model: TrtModel
    ):
        super().__init__(model)
        self._dtoh_stream = None
        self._htod_stream = None
        self._infer_stream = None
        self._host_mem: list[Any] = []

        # Use the best datatype
        self.fp16 = bool('fp16' in self.model.dtypes)
        self.in_tensor_dtype: cp.dtype = (
            cp.float16 if 'fp16' in self.model.dtypes else cp.float32
        )
        self.out_tensor_dtype: cp.dtype = self.in_tensor_dtype


    @property
    def dtoh_stream(self):
        # -> cp.cuda.Stream
        return self._dtoh_stream


    @property
    def htod_stream(self):
        # -> cp.cuda.Stream
        return self._htod_stream


    @property
    def infer_stream(self):
        # -> cp.cuda.Stream
        return self._infer_stream


    @infer_stream.setter
    def infer_stream(self, stream) -> None:
        # -> cp.cuda.Stream
        self._infer_stream = stream


    @property
    def h_in_mem(self):
        # -> cp.cuda.alloc_pinned_memory
        return self._host_mem[0]


    @property
    def h_out_mem(self):
        # -> cp.cuda.alloc_pinned_memory:
        return self._host_mem[1]


    def set_host_mem(self, h_in, h_out) -> None:
        self._host_mem = (h_in, h_out)


    def initialize(self,
        device: str = 'cuda:0',
        fp16: bool = True,
        in_max_shape: tuple[int, int, int] | None = None,
        memalloc: bool = True,
        create_streams: bool = False,
        warmup: bool = False,
        **kwargs,
    ):
        # Device and dtype
        self.device = device
        self.fp16 = fp16 and 'fp16' in self.model.dtypes
        self.in_tensor_dtype = cp.float16 if self.fp16 else cp.float32
        self.out_tensor_dtype = self.in_tensor_dtype

        if create_streams:
            set_cupy_cuda_device(device)
            self.dtoh_stream = cp.cuda.Stream(non_blocking=True)
            self.htod_stream = cp.cuda.Stream(non_blocking=True)
            self.infer_stream = cp.cuda.Stream()

        if self.infer_stream is None:
            raise RuntimeError("[TRT] inference stream must be defined before")

        # Deserialize and create the context
        model_path = self.model.filepath
        print(yellow("TensorRtCupySession::initialize"))
        trt_runtime = trt.Runtime(get_trt_logger())
        with torch.cuda.stream(self.infer_stream):
            if self.model.engine is None:
                with open(model_path, 'rb') as f:
                    serialized_engine = f.read()
                self.engine = trt_runtime.deserialize_cuda_engine(serialized_engine)
            else:
                print("reuse engine")
                self.engine = self.model.engine
            # Create a context (without reusing device memory)
            self.context = self.engine.create_execution_context()

        if warmup and self.infer_stream is not None:
            self.warmup(3)

        # Do not allocate memory when it is already done before
        if not memalloc:
            return

        # Calculate maximum shape
        if in_max_shape is not None:
            in_h, in_w = in_max_shape[:2]
        else:
            in_w, in_h = self.model.shape_strategy.max_size
        out_h, out_w = in_h * self.model.scale, in_w * self.model.scale
        in_nc, out_nc = self.model.in_nc, self.model.out_nc

        # Inference shapes
        in_tensor_shape = (1, in_nc, in_h, in_w)
        out_tensor_shape = (1, out_nc, out_h, out_w)
        print(f"[V][TRT] Initialization: in tensor shape: {in_tensor_shape}")
        print(f"[V][TRT] Initialization: out tensor shape: {out_tensor_shape}")

        dtype_size = np.dtype(np.float32).itemsize
        engine, context = self.engine, self.context

        # Allocate buffers
        if len(self._host_mem):
            raise RuntimeError("Already allocated host memory")

        for idx in range(engine.num_io_tensors):
            tensor_name = engine.get_tensor_name(idx)

            if engine.get_tensor_mode(tensor_name) == trt.TensorIOMode.INPUT:
                context.set_input_shape(tensor_name, in_tensor_shape)
                self.input_nbytes = trt.volume(in_tensor_shape) * dtype_size
                self._host_mem.append(
                    cp.cuda.alloc_pinned_memory(self.input_nbytes)
                )

            elif engine.get_tensor_mode(tensor_name) == trt.TensorIOMode.OUTPUT:
                self.output_nbytes = trt.volume(out_tensor_shape) * dtype_size
                self._host_mem.append(
                    cp.cuda.alloc_pinned_memory(self.output_nbytes)
                )

        # self.warmup(3)


    def warmup(self, count: int = 1):
        shape = [*reversed(self.model.shape_strategy.opt_size), self.model.in_nc]
        tensor_shape = [
            1,
            self.model.in_nc,
            *reversed(self.model.shape_strategy.opt_size)
        ]
        context, engine = self.context, self.engine
        for idx in range(engine.num_io_tensors):
            tensor_name = engine.get_tensor_name(idx)
            if engine.get_tensor_mode(tensor_name) == trt.TensorIOMode.INPUT:
                context.set_input_shape(tensor_name, tensor_shape)
        # print(f"[V] warmup ({count}x) with a random img ({shape})")
        img = np.random.random(shape).astype(np.float32)
        for _ in range(count):
            self.process(img)

