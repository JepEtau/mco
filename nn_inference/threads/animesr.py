from __future__ import annotations
import math
from pprint import pprint
import numpy as np
from torch import Tensor
from typing import TYPE_CHECKING, Literal

import torch
import torch.nn.functional as F

from nn_inference.model_mgr import ModelManager
from nn_inference.resource_mgr import NnFrame, Singleton
from processing.dsr import generate_dsr_mask
from pynnlib.utils.torch_tensor import to_nchw
from utils.p_print import *
from pynnlib import (
    NnModelSession,
    NnModel,
)




# class FrameCacheManager(metaclass=Singleton):
#     def __init__(self) -> None:
#         pass

#     def
class TemporalFrameCache(metaclass=Singleton):
    def __init__(
        self,
        tensor: Tensor,
        model: NnModel,
    ) -> None:
        self._previous: Tensor = None
        self._current: Tensor = None
        self._next: Tensor = None

        self._shape = tensor.shape
        b = 1
        n, c, h, w = tensor.shape
        h, w = tensor.shape[2:]
        # modulo = 4
        # pad_h = (modulo - h % modulo) % modulo
        # pad_w = (modulo - w % modulo) % modulo
        # padded_out_h, padded_out_w = h + pad_h, w + pad_w
        self._out: Tensor = torch.zeros(
            (b, c, model.scale * h, model.scale * w),
            dtype=tensor.dtype,
            device=tensor.device
        )
        self._state: Tensor = torch.zeros(
            b,
            model.num_feat,
            h,
            w,
            dtype=tensor.dtype,
            device=tensor.device
        )
        # self._pad = (0, padded_out_w - w, 0, padded_out_h - h)

        self.out_w = model.scale * w
        self.out_h = model.scale * h
        self._frame_no: int = -1
        self._ncached: int = 0
        self.cache_depth: int = 3


    @property
    def next(self) -> Tensor:
        return self._next


    @next.setter
    def next(self, tensor: Tensor) -> None:
        # self._next = F.pad(tensor, self._pad, "replicate")
        self._next = tensor

    @property
    def previous(self) -> Tensor:
        return self._previous

    @previous.setter
    def previous(self, tensor: Tensor) -> None:
        self._previous = tensor

    @property
    def current(self) -> Tensor:
        return self._current

    @current.setter
    def current(self, tensor: Tensor) -> None:
        self._current = tensor


    @property
    def out(self) -> Tensor:
        return self._out

    @out.setter
    def out(self, tensor: Tensor) -> None:
        self._out = tensor


    @property
    def state(self) -> Tensor:
        return self._state

    @state.setter
    def state(self, state: Tensor) -> None:
        self._state = state


    def update(self, out: Tensor, state: Tensor) -> Tensor:
        """Update pointers and returns output tensor"""
        self._out = out
        self._state = state
        self._previous = self._current
        self._current = self.next
        return out[:, :, : self.out_h, : self.out_w]

    @property
    def frame_no(self) -> int:
        return self._frame_no

    @frame_no.setter
    def frame_no(self, no: int) -> None:
        self._frame_no = no

    @property
    def ncached(self) -> int:
        return self._ncached

    def ncache_add(self, v: int = 1) -> None:
        self._ncached = max(0, min(self._ncached + v, self.cache_depth))

    # @ncached.setter
    # def ncached(self, v: int) -> None:
    #     self._ncached = max(0, min(self._ncached + v, self.cache_depth))
    #     print(purple(f"set nvcache: {self._ncached} with v = {v}"))



@torch.inference_mode
def animesr_inference(
    frame: NnFrame,
    in_tensor: Tensor,
    model_manager: ModelManager,
) -> tuple[int, Tensor, Literal['request', 'last', 'none']]:

    # print(f"  input frame no.: {frame.f_no}")

    model_key: str = frame.sequence[frame.step_no]
    model: NnModel = model_manager.model(model_key)
    frame_cache = TemporalFrameCache(in_tensor, model)

    if frame_cache.current is None:
        # Beginning of a scene
        frame_cache.previous = in_tensor
        frame_cache.current = in_tensor
        frame_cache.frame_no = frame.f_no
        # print(f"  do not output")
        return 0, None, 'request'

    if in_tensor is None:
        # last frame
        # print(red(f"last frame, in_tensor is none, start emptying queue: {frame_cache.ncached}"))
        frame_cache.next = frame_cache.current
    else:
        frame_cache.next = in_tensor
        frame_cache.ncache_add()

    # print(f"frame no. {frame.f_no}, step no. {frame.step_no}, tensor:{in_tensor.data_ptr()}, last: {frame.last}")
    # print(f"  previous: {frame_cache.previous.shape}, {frame_cache.previous.device}")
    # print(f"  current: {frame_cache.current.shape}, {frame_cache.current.device}")
    # print(f"  next: {frame_cache.next.shape}, {frame_cache.next.device}")
    # print(f"  state: {frame_cache.state.shape}, {frame_cache.state.device}")
    multi_tensor: Tensor = torch.cat(
        (frame_cache.previous, frame_cache.current, frame_cache.next),
        dim=1
    )
    # print(f"  multi_tensor: {multi_tensor.shape}")

    # (previous, current, next frame), previous out frame, previous hidden state
    out, state = model.module(multi_tensor, frame_cache.out, frame_cache.state)

    # generate frame to be put in cache
    out_tensor = frame_cache.update(out, state)
    out_tensor = out_tensor.contiguous()
    out_tensor = torch.clamp_(out_tensor, 0., 1.)

    # Update next frame no
    out_frame_no = frame_cache.frame_no
    frame_cache.frame_no = frame.f_no

    command: str = 'none'
    if frame.last:
        # frame.last = False
        # print(f"  send command last bc frame is last: {frame.f_no}")
        command = 'last'
        frame_cache.ncache_add(-1)
        if frame_cache.ncached <= 0:
            # print(red("No frame anymore"))
            return 0, None, 'none'

    # print(f"  output frame no.: {out_frame_no}")
    return out_frame_no, out_tensor, command

