from __future__ import annotations
from pprint import pprint
import numpy as np
from torch import Tensor
from typing import TYPE_CHECKING

import torch

from nn_inference.model_mgr import ModelManager
from nn_inference.resource_mgr import NnFrame
from processing.dsr import generate_dsr_mask
from pynnlib.utils.torch_tensor import to_nchw
from utils.p_print import *
from pynnlib import (
    NnModelSession,
    NnModel,
)


@torch.inference_mode
def perform_inpaint_inference(
    frame: NnFrame,
    in_tensor: Tensor,
    model_manager: ModelManager,
) -> Tensor:

    # Specific to MCO
    # Generate a binary mask
    mask_img: np.ndarray | None = generate_dsr_mask(
        scene=frame.src_scene,
        frame_no=frame.f_no,
        shape=frame.tensor.shape,
    )

    if mask_img is None:
        return in_tensor

    print(yellow(f"inpainting {frame.f_no}"))

    # Get session
    model_key: str = frame.sequence[frame.step_no]
    session: NnModelSession = model_manager.session(model_key)

    mask_tensor: Tensor = (
        torch.from_numpy(np.ascontiguousarray(mask_img))
        .to(in_tensor.device, non_blocking=False)
    )
    mask_tensor = mask_tensor.to(dtype=session.torch_dtype)
    mask_tensor = mask_tensor / 255.
    mask_tensor = to_nchw(mask_tensor).contiguous()

    # Inpainting
    module: NnModel = model_manager.model(model_key).module
    out_tensor: Tensor = module(in_tensor, mask_tensor)
    out_tensor = out_tensor.contiguous()
    out_tensor = torch.clamp_(out_tensor, 0, 1)

    del mask_tensor
    del mask_img
    torch.cuda.empty_cache()

    return out_tensor

