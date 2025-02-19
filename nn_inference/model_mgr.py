from dataclasses import dataclass
import gc
import os
from pprint import pprint
import time
from typing import Literal
import cupy as cp
import numpy as np
from torch import Tensor

from pynnlib import (
    Idtype,
    nnlib,
    NnModel,
    NnModelSession,
    ShapeStrategy,
    TrtModel,
    is_cuda_available,
    is_tensorrt_available,
    NnFrameworkType,
    set_cupy_cuda_device,
    TrtEngine,
    np_dtype_to_torch,
    TensorRtSession,
)
from .cupy_utils import HostDeviceMemory

if is_tensorrt_available():
    import tensorrt as trt

if is_cuda_available():
    from .pytorch.session_cupy import PyTorchCuPySession

import torch
from utils.p_print import *

from .resource_mgr import Singleton
from utils.path_utils import absolute_path, os_path_basename, path_split
from utils.tools import ml_model_dir



def _nested_dict_set(d: dict, o: object, *keys) -> None:
    nested_d = d
    for k in keys:
        if k == keys[-1]:
            break
        if k not in nested_d.keys():
            nested_d[k] = dict()
        nested_d = nested_d[k]
    nested_d[k] = o



@dataclass
class ModelInfo:
    name: str
    path: str
    dtype: Idtype
    xprovider: Literal['cuda', 'trt']
    key: str = ""
    model: NnModel | None = None
    session: NnModelSession = None


@dataclass
class _SyncMemory:
    in_max_nbytes: int = 0
    out_max_nbytes: int = 0
    in_dtype: np.dtype = 0
    out_dtype: np.dtype = 0
    htod_mem: HostDeviceMemory | None = None
    dtoh_mem: HostDeviceMemory | None = None



# class ModelManager(metaclass=Singleton):
class ModelManager:
    def __init__(self) -> None:
        self._models: dict = {}
        self._models_by_keys: dict[str, ModelInfo] = {}
        self._shapes: dict[str, set[str]] = {}

        self._opset: int = 20
        self._device: str = "cuda:0"

        self.in_max_nbytes: int = 0
        self.in_dtype: np.dtype = np.uint16
        self.out_max_nbytes: int = 0
        self.out_dtype: np.dtype = np.uint16

        self.htod_cuda_stream: torch.cuda.Stream  = None
        self.dtoh_cuda_stream: torch.cuda.Stream  = None
        self.torch_infer_stream: torch.cuda.Stream = None
        self.trt_cuda_stream: torch.cuda.Stream  = None

        self.htod_host_mem: Tensor | None = None
        # self.htod_mem: Tensor | None = None
        self.dtoh_host_mem: Tensor | None = None

        # Memory used for synchronous operations
        self.sync_memory: dict[str, _SyncMemory] = {
            'cuda': _SyncMemory(),
            'torch': _SyncMemory(),
        }


    def clean(self):
        print(red("clean ModelManager"))
        del self.trt_cuda_stream
        del self.htod_cuda_stream
        del self.dtoh_cuda_stream
        del self.torch_infer_stream
        for v in self.sync_memory.values():
            del v
        for m in self._models_by_keys.values():
            del m.model
            try:
                del m.session.context
            except:
                pass
            try:
                del m.session.engine
            except:
                pass
            try:
                del m.session.module
            except:
                pass
            del m.session
        try:
            del self.trt_session
        except:
            pass
        try:
            del self.torch_session
        except:
            pass
        del self._models_by_keys

        gc.collect()

    # def __del__(self):
    #     print(red("delete ModelManager"))
    #     return super().__del__()

    @property
    def opset(self) -> int:
        return self._opset


    @opset.setter
    def opset(self, opset: int) -> None:
        self._opset = opset


    @property
    def device(self) -> str:
        return self._device


    def model(self, model_key: str) -> NnModel:
        return self._models_by_keys[model_key].model


    def session(self, model_key: str) -> NnModelSession:
        return self._models_by_keys[model_key].session


    def xprovider(self, model_key: str) -> Literal['cuda', 'trt']:
        return self._models_by_keys[model_key].xprovider


    def model_info(self, model_key: str) -> ModelInfo:
        return self._models_by_keys[model_key]


    @device.setter
    def device(self, device: str) -> None:
        self._device = device


    def register(
        self,
        model: str,
    ) -> str | None:
        infos = model.split(':')
        name: str = infos[0]
        path: str = absolute_path(os.path.join(ml_model_dir, name))
        # Patch filename to facilitate tests
        name = f"{name}"
        path = f"{path}"
        if (
            (not name.endswith('.pth')
            and not name.endswith('.safetensors')
            )
            and os.path.exists(f"{path}.pth")
        ):
            name = f"{name}.pth"
            path = f"{path}.pth"
        print(path)

        dtype: Idtype = 'fp16'
        if 'fp32' in infos[1:]:
            dtype = 'fp32'
        elif 'bf16' in infos[1:]:
            dtype = 'bf16'

        xprovider: str = 'cuda' if 'cuda' in infos[1:] else 'trt'

        if not is_cuda_available():
            xprovider = 'stub'

        model_key: str = ':'.join((name, xprovider, dtype))

        _model: ModelInfo | None = None
        try:
            _model = self._models[name][xprovider][dtype]
        except:
            pass

        if _model is None:
            _model = ModelInfo(
                name=os_path_basename(name),
                path=path,
                dtype=dtype,
                xprovider=xprovider,
                key=model_key,
            )
            _nested_dict_set(self._models, _model, name, xprovider, dtype)
            self._models_by_keys[model_key] = self._models[name][xprovider][dtype]

            print(lightcyan(f"Open model:"), f"{path}")
            try:
                _model.model = nnlib.open(
                    path,
                    device='cuda' if is_cuda_available() else 'cpu'
                )
            except:
                raise ValueError(red(f"Failed opening {path}"))

            if _model.model.framework.type != NnFrameworkType.ONNX:
                if xprovider == 'trt' and _model.model.arch.to_onnx is None:
                    # Force to cuda if tensorrt is not supported
                    xprovider = 'cuda'
                    raise ValueError(f"{name} cannot be converted to trt, arch={_model.model.arch.type}")

        return _model.key


    def count(self) -> int:
        return len(self._models_by_keys)


    def __str__(self) -> str:
        return (
            "Models:\n"
            +"\n".join([f"  \'{key}\': {model.path}" for key, model in self._models_by_keys.items()])
        )


    def get_scale(self, model_key: str) -> int:
        return self._models_by_keys[model_key].model.scale


    def set_input_size(self, model_key: str, size: tuple[int, int]) -> str:
        """Save size for each model to generate trt engine (shape strategy)
        returns a new key
        """
        if self._models_by_keys[model_key].xprovider != 'trt':
            return model_key

        if model_key not in self._shapes:
            self._shapes[model_key] = set()
        size_key: str = 'x'.join(map(str, size))
        self._shapes[model_key].add(size_key)

        return ":".join((model_key, size_key))


    def consolidate(self) -> None:
        """Convert models to TRT engines
        """
        _keys: list[str] = list(self._shapes.keys())
        print(yellow("consolidate:"))
        pprint(self._shapes)
        for model_key, sizes in self._shapes.items():
            print(lightcyan(f"model: {model_key}"))
            print(f"  sizes: {sizes}")
            for size_key in sizes:
                model: ModelInfo = self._models_by_keys[model_key]
                print(f"  convert to TensorRT, ",
                    f"onnx opset={self.opset}, ",
                    f"dtype={model.dtype}",
                    f"size: {size_key}"
                )
                start_time = time.time()
                shape_strategy: ShapeStrategy = ShapeStrategy(
                    opt_size = tuple(map(int, size_key.split('x')))
                )
                trt_model: TrtModel = nnlib.convert_to_tensorrt(
                    model=model.model,
                    shape_strategy=shape_strategy,
                    dtype=model.dtype,
                    # optimization_level=3,
                    opset=self.opset,
                    device=self.device,
                    out_dir=path_split(model.path)[0],
                )

                elapsed_time = time.time() - start_time
                if elapsed_time > 2:
                    print(f"[V] Converted to TRT engine in {elapsed_time:.2f}s")

                trt_model_key: str = ":".join((model_key, size_key))
                self._models_by_keys[trt_model_key] = ModelInfo(
                    name=self._models_by_keys[model_key].name,
                    path=trt_model.filepath,
                    dtype=model.dtype,
                    xprovider='trt',
                    key=trt_model_key,
                    model=trt_model,
                )

        for k in _keys:
            del self._models_by_keys[k]


    def set_sync_in_max_nbytes(
        self,
        xprovider: Literal['cuda', 'trt'],
        in_nbytes: int = 0,
        out_nbytes: int = 0,
    ) -> None:
        """Allocate some memory"""
        # the execution provider is required
        # because the stream used for transfers uses different cuda streams
        self.sync_memory[xprovider].in_max_nbytes = in_nbytes
        self.sync_memory[xprovider].out_max_nbytes = out_nbytes


    def set_sync_dtypes(self, in_dtype: np.dtype, out_dtype: np.dtype) -> None:
        for v in self.sync_memory.values():
            v.in_dtype = in_dtype
            v.out_dtype = out_dtype


    def set_in_out_max_nbytes(self, in_nbytes: int, out_nbytes: int):
        self.in_max_nbytes = in_nbytes
        self.out_max_nbytes = out_nbytes


    def set_dtypes(self, in_dtype: np.dtype, out_dtype: np.dtype) -> None:
        self.in_dtype = in_dtype
        self.out_dtype = out_dtype


    def has_torch_models(self) -> bool:
        for m in self._models_by_keys.values():
            if m.model.fwk_type == NnFrameworkType.PYTORCH:
                return True
        return False


    def has_trt_models(self) -> bool:
        for m in self._models_by_keys.values():
            if m.model.fwk_type == NnFrameworkType.TENSORRT:
                return True
        return False


    def initialize_sessions(self) -> None:
        torch.backends.cudnn.enabled = True
        # torch.backends.cudnn.benchmark = False

        # Set custom sessions
        if is_cuda_available():
            nnlib.set_session_constructor(NnFrameworkType.PYTORCH, PyTorchCuPySession)

        # Create streams
        self.htod_cuda_stream = torch.cuda.Stream(self.device)
        self.dtoh_cuda_stream = torch.cuda.Stream(self.device)
        if self.has_torch_models():
            self.torch_infer_stream = torch.cuda.Stream(self.device)
        if self.has_trt_models():
            self.trt_cuda_stream = torch.cuda.Stream(self.device)

        # Allocate memory for each stream
        self.allocate_memory()
        # self.allocate_sync_memory()

        # For each session don not allocate memory because already done here.
        # This permits to use the same memory area whatever the session type
        warmup_done: bool = False
        for m in self._models_by_keys.values():
            m.session = nnlib.session(m.model)

            print(lightgreen(f"initialize {m.session.model.arch_name} {m.model.fwk_type}"))
            if m.model.fwk_type == NnFrameworkType.PYTORCH:
                self.torch_session: PyTorchCuPySession = m.session
                self.torch_session.infer_stream = self.torch_infer_stream
                self.torch_session.initialize(
                    device=self.device,
                    dtype=m.dtype,
                    memalloc=False,
                    in_max_shape=None,
                    warmup=False,
                )

            elif m.model.fwk_type == NnFrameworkType.TENSORRT:
                self.trt_session: TensorRtSession = m.session
                self.trt_session.infer_stream = self.trt_cuda_stream
                self.trt_session.initialize(
                    device=self.device,
                    dtype=m.dtype,
                    memalloc=False,
                    in_max_shape=None,
                    create_streams=False,
                    warmup=False,
                )

                engine: TrtEngine = self.trt_session.engine
                in_tensor_name: str = ''
                for idx in range(engine.num_io_tensors):
                    tensor_name: str = engine.get_tensor_name(idx)
                    if engine.get_tensor_mode(tensor_name) == trt.TensorIOMode.INPUT:
                        in_tensor_name = tensor_name
                        break
                self.trt_session.in_tensor_name = in_tensor_name

            if not warmup_done:
                # print(f"Warmup with {session.model.filepath}")
                # session.warmup(5)
                warmup_done = True


    def allocate_memory(self) -> None:
        if self.in_max_nbytes == 0 or self.out_max_nbytes == 0:
            raise ValueError(
                f"Cannot allocate memory: in: {self.in_max_nbytes}B, out: {self.out_max_nbytes}B"
            )

        # Allocate Host memory
        # self.htod_mem = torch.empty(1000, 1000, dtype=torch.float32, pin_memory=True)
        self.htod_host_mem: Tensor = torch.empty(
            self.in_max_nbytes,
            dtype=torch.uint8,
            pin_memory=True
        )
        # self.htod_mem = HostDeviceMemory(
        #     host=htod_tensor.untyped_storage(),
        #     device=None,
        #     nbytes=self.in_max_nbytes
        # )


        self.dtoh_host_mem: Tensor = torch.empty(
            self.out_max_nbytes,
            dtype=torch.uint8,
            pin_memory=True
        )
        # print(f"Allocated memory:\n  HtoD: {self.htod_mem}\n  DtoH: {self.dtoh_mem}")


    def allocate_sync_memory(self) -> None:
        """Allocate memory for synchronous models (inpaint)
        """
        self.htod_cuda_stream_sync = cp.cuda.stream.Stream(non_blocking=False)
        for xprovider, mem in self.sync_memory.items():
            print(f"[{xprovider}] allocate sync memory:")
            # HtoD pin memory
            if mem.in_max_nbytes:
                print(f"  HtoD: {mem.in_max_nbytes}")
                allocate_memory(
                    shape=(mem.in_max_nbytes, 1, 1),
                    dtype=mem.in_dtype,
                    stream=self.htod_cuda_stream_sync
                )

            # DtoH pin memory
            if mem.out_max_nbytes:
                print(f"  DtoH: {mem.out_max_nbytes}")
                mem.dtoh_mem = allocate_memory(
                    shape=(mem.out_max_nbytes, 1, 1),
                    dtype=mem.out_dtype,
                    stream=self.htod_cuda_stream_sync
                )


    def htod_sync_memory(self, xprovider: Literal['cuda', 'trt']) -> HostDeviceMemory:
        return self.sync_memory[xprovider].htod_mem


    def dtoh_sync_memory(self, xprovider: Literal['cuda', 'trt']) -> HostDeviceMemory:
        return self.sync_memory[xprovider].dtoh_mem
