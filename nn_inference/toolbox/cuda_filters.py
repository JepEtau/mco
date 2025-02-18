import torch
from torch import Tensor
from torch import from_dlpack, to_dlpack
import torch.nn.functional as F

import cupy as cp
from torchvision.transforms.v2 import GaussianNoise
from .darker_thinner import DarkerThinner

from nn_inference.resource_mgr import NnFrame
from utils.p_print import *


def gaussian_noise_(
    frame: NnFrame,
    params: str | None,
) -> NnFrame:

    param_list: list[str] = params.split(":")
    mean, sigma = 0., 0.1
    try:
        mean, sigma = float(param_list[0]), float(param_list[1])
    except:
        raise ValueError(f"unrecognized parameters for gaussian noise: {param_list}")

    gaussian_noise = GaussianNoise(mean, sigma)
    out_x: Tensor = gaussian_noise(frame.tensor)
    frame.tensor = out_x.contiguous()

    return frame



def darker_thinner_(
    frame: NnFrame,
    params: str | None,
) -> NnFrame:
    args: dict[str, int] = {}
    verbose: bool = False

    if params is not None:
        param_list: list[str] = params.split(":")
        if len(param_list) >= 1:
            args['strength'] = float(param_list[0])
        if len(param_list) >= 2:
            args['thin'] = float(param_list[1])

    darker_thinner = DarkerThinner(**args)

    if isinstance(frame.tensor, Tensor):
        raise NotImplementedError("not supported input tensor for darker_thinner_")
        darker_thinner.to(frame.tensor.device)
        if frame.tensor.dtype == torch.float16:
            darker_thinner.half()
        frame.tensor = darker_thinner(frame.tensor)

    elif isinstance(frame.tensor, cp.ndarray):
        if verbose:
            print(purple(f"[V][F]   darker_thinner_"))

        in_x: Tensor = frame.tensor
        if verbose:
            print(purple(f"[V][F]     in_x"), f"{in_x.shape}, {in_x.dtype}")

        darker_thinner.to(in_x.device)
        if in_x.dtype == torch.float16:
            darker_thinner.half()

        if verbose:
            print(purple(f"[V][F]     in_x"), f"{in_x.shape}, {in_x.dtype}")
        out_x: Tensor = darker_thinner(in_x)
        if verbose:
            print(purple(f"[V][F]     out_x"), f"{out_x.shape}, {out_x.dtype}")

        frame.tensor = torch.clamp(out_x.contiguous(), 0, 1.0)

    return frame




def gpu_rotate_90_(frame: NnFrame, k: int | None = 1) -> NnFrame:
    if k is None:
        k = 1
    elif k < 0:
        k += 4
    out_x: Tensor = torch.rot90(frame.tensor, k=k, dims=(2, 3))
    frame.tensor = out_x.contiguous()
    return frame



def _create_gaussian_kernel(
    x: Tensor,
    kernel_size: int,
    sigma: float,
) -> torch.Tensor:
    """Create a Gaussian kernel for blurring. Use same device/dtype as x tensor.
        x must be in nchw format
    """
    # Create a 1D Gaussian kernel
    nc: int = x.shape[1]
    linspace: Tensor = torch.linspace(
        -kernel_size // 2, kernel_size // 2, kernel_size, dtype=x.dtype, device=x.device
    )
    # linspace = linspace.to(dtype=x.dtype, device=x.device)
    gaussian = torch.exp(-(linspace.pow(2) / (2 * sigma ** 2)))
    gaussian = gaussian / gaussian.sum()

    # Create 2D kernel by outer product
    kernel_2d = gaussian.unsqueeze(1) @ gaussian.unsqueeze(0)
    kernel_2d = kernel_2d / kernel_2d.sum()

    # Reshape kernel for conv2d: (channels, 1, kernel_size, kernel_size)
    kernel = kernel_2d.expand(nc, 1, kernel_size, kernel_size)
    return kernel



def unsharp_mask_(
    frame: NnFrame,
    params: str = ""
) -> NnFrame:
    """
    Apply unsharp masking to a tensor, inplace operation

    Args:
        frame.tensor: nchw
        radius: radius of the Gaussian kernel
        amount: Strength of sharpening effect
        sigma: Standard deviation for Gaussian kernel

    Returns:
        self
    """

    radius: int = 2
    amount: float = 1.0
    sigma: float = 1.0
    try:
        param_list: list[str] = params.split(":")
        radius, amount = int(param_list[0]), float(param_list[1])
        if len(param_list) >= 3:
            sigma = float(param_list[2])
    except:
        raise ValueError(f"unrecognized parameters for gaussian noise: {param_list}")


    in_x: Tensor = frame.tensor
    nc: int = in_x.shape[1]

    # Gaussian blur's kernel
    kernel_size: int = radius * 2 + 1
    kernel = _create_gaussian_kernel(in_x, kernel_size, sigma)

    # Apply blur
    padding = kernel_size // 2
    blurred = F.conv2d(in_x, kernel, padding=padding, groups=nc)

    # Calculate unsharp mask and apply sharpening
    mask = in_x - blurred
    sharpened = in_x + amount * mask

    frame.tensor = torch.clamp(sharpened.contiguous(), 0., 1.)

    return frame
