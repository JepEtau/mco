from collections.abc import Callable
from pprint import pprint
import time
from typing import Any

import torch

from nn_inference.resource_mgr import NnFrame
from .cuda_filters import (
    gaussian_noise_,
    darker_thinner_,
    gpu_rotate_90_,
    unsharp_mask_,
    collor_correction_,
)
from .cv2_filters import (
    cv2_bilateral_,
    cv2_nlmeans_,
)
from utils.p_print import *
from .gpu_resize import (
    gpu_resize_,
    gpu_resize_to_,
)
from processing import (
    supported_ffmpeg_filters,
    supported_cuda_filters,
    supported_encoder_filters,
)



_cuda_functions: dict[str, Callable[..., object]] = {
    'cv2_bilateral': cv2_bilateral_,
    'cv2_nlmeans': cv2_nlmeans_,
    'darker_thinner': darker_thinner_,
    'gaussian_noise': gaussian_noise_,
    'resize': gpu_resize_,
    'resize_to': gpu_resize_to_,
    'rotate90': gpu_rotate_90_,
    'unsharp_mask': unsharp_mask_,
    'ccor': collor_correction_,
}



def apply_cuda_filters_(
    frame: NnFrame,
    verbose: bool = False
) -> None:
    """Inline modification of the frame"""
    # Loop until the encoder step is found
    # or if the followinf filter is a NN model
    if frame.step_no >= frame.encoder_step_no:
        return

    next_filter : list | tuple | str = frame.sequence[frame.step_no]
    while isinstance(next_filter, list | tuple):
        name, params = next_filter
        if verbose:
            verbose_prefix: str = f"[V][CUDA][{frame.step_no}]"
            print(f"{verbose_prefix} {name}, {params}")

        inplace_fct: Callable | None = _cuda_functions.get(name, None)
        if inplace_fct is not None:
            inplace_fct(frame, params)

        elif name not in supported_cuda_filters:
            raise NotImplementedError(f"Not implemented: {name}")

        else:
            raise ValueError(f"Not supported: {name}")

        frame.step_no += 1
        if frame.step_no >= frame.encoder_step_no:
            break
        next_filter = frame.sequence[frame.step_no]




def apply_cpu_filters_(
    frame: NnFrame,
    verbose: bool = False
) -> None:
    """Inline modification of the frame: np.ndarray only"""

    next_filter : list | tuple | str = frame.sequence[frame.step_no]
    while isinstance(next_filter, list | tuple):
        name, params = next_filter
        if verbose:
            verbose_prefix: str = f"[V][CV2][{frame.step_no}]"
            print(f"{verbose_prefix} {name}, {params}")

        if name == 'nlmeans':
            cv2_nlmeans_(frame=frame, params=params)
            if verbose:
                print(cyan(f"cv2_nlmeans_: {params}"))

        else:
            # Not a supported filter
            break

        frame.step_no += 1
        if frame.step_no >= frame.encoder_step_no:
            break
        next_filter = frame.sequence[frame.step_no]





def get_encoder_ffmpeg_filters(filters: list[Any], start_step_no: int) -> list[str]:
    # For each step, append to the FFmpeg complex filter
    fcomplex_list: list[str] = []
    started: bool = False
    for f in filters[start_step_no:]:
        name, params = f

        # Loop until first FFmpeg filter found
        if (
            not started
            and name in supported_encoder_filters
        ):
            started = True

        # Append FFMpeg filter
        if started:
            if name not in supported_encoder_filters:
                raise ValueError(red(f"Filter: {name} is following a FFmpeg filter"))

            fcomplex_str: str = name
            if params is not None:
                fcomplex_str += f"={params}"
            fcomplex_list.append(fcomplex_str)

    return fcomplex_list



def get_decoder_ffmpeg_filters(filters: list[Any]) -> tuple[list[str], int]:
    # For each step, append to the FFmpeg complex filter
    fcomplex_list: list[str] = []
    # Loop until non FFmpeg filter found
    for step_no, f in enumerate(filters):
        if not isinstance(f, list | tuple):
            break
        name, params = f
        if name not in supported_encoder_filters:
            break

        fcomplex_str: str = name
        if params is not None:
            fcomplex_str += f"={params}"
        fcomplex_list.append(fcomplex_str)

    return fcomplex_list, step_no
