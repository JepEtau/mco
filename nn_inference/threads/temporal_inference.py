from __future__ import annotations
import math
from pprint import pprint
import numpy as np
from torch import Tensor
from typing import TYPE_CHECKING, Literal

import torch
import torch.nn.functional as F

from nn_inference.model_mgr import ModelManager
from nn_inference.threads.animesr import animesr_inference
from nn_inference.resource_mgr import McoFrame, Singleton
from processing.dsr import generate_dsr_mask
from nnarchs.utils.torch_tensor import to_nchw
from utils.p_print import *
from nnarchs import (
    NnModelSession,
    NnModel,
)




def perform_temporal_inference(
    frame: McoFrame,
    in_tensor: Tensor,
    model_manager: ModelManager,
) -> tuple[int, Tensor, Literal['request', 'last', 'non']]:

    model_key: str = frame.sequence[frame.step_no]
    model: NnModel = model_manager.model(model_key)
    arch_name: str = model.arch_name.lower()
    if "animesr" in arch_name:
        return animesr_inference(frame, in_tensor, model_manager)

    raise ValueError(f"{arch_name} is not supported")

