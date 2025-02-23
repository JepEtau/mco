import cv2
import torch
import numpy as np
from torch import Tensor
from pynnlib import (
    tensor_to_img,
    img_to_tensor,
)
from utils.media import FShape
from utils.p_print import *
from nn_inference.resource_mgr import NnFrame, Singleton
from nn_inference.toolbox.dh_transfers import (
    dtoh_transfer_sync,
    htod_transfer_sync,
)


def bilateral_filter(
    img: np.ndarray,
    radius: int,
    sigmaColor: float,
    sigmaSpace: float
):
    return cv2.bilateralFilter(
        src=img,
        d=(2 * radius + 1),
        sigmaColor=sigmaColor,
        sigmaSpace=sigmaSpace
    )


class _DHMemory(metaclass=Singleton):
    def __init__(
        self,
        shape: torch.Size,
        dtype: torch.dtype,
        scale: int = 1
    ) -> None:
        h, w, c = shape
        self._dtoh_mem = torch.empty(
            (h, w, c),
            dtype=dtype,
            device=torch.device('cpu'),
            pin_memory=True
        )
        # Reuse same host memory if same size/same dtype
        if scale == 1:
            self._htod_mem = self._dtoh_mem
        else:
            self._htod_mem = torch.empty(
                int(h * scale), int(w * scale), c,
                dtype=dtype,
                device=torch.device('cpu'),
                pin_memory=True
            )

    @property
    def dtoh_mem(self) -> Tensor:
        return self._dtoh_mem

    @property
    def htod_mem(self) -> Tensor:
        return self._htod_mem



def cv2_nlmeans_(
    frame: NnFrame,
    params: str | None,
) -> NnFrame:
    verbose : bool = False

    h: float = 3
    h_color: float = 3
    patch_window_size: float = 7
    search_window_size: float = 21

    if params is not None:
        param_list: list[str] = params.split(":")
        if len(param_list) == 4:
            h, h_color = list(map(float, param_list[:2]))
            patch_window_size, search_window_size = list(map(int, param_list[2:]))

    # Get tensor from frame
    tensor: Tensor = frame.tensor
    if verbose:
        print(purple(f"[V][F] cv2 fast nlmeans:"))
        print(
            purple(f"[V][F]  in_tensor:"),  f"{tensor.shape}, {tensor.dtype}"
        )

    # DtoH transfer
    in_x: Tensor = frame.tensor
    d_img: Tensor = tensor_to_img(tensor=in_x, img_dtype=np.uint8, flip_r_b=True)
    dh_memory = _DHMemory(shape=d_img.shape, dtype=d_img.dtype)
    in_img: np.ndarray = dtoh_transfer_sync(host_mem=dh_memory.dtoh_mem, d_img=d_img)


    # Apply filter on the numpy image
    out_img = cv2.fastNlMeansDenoisingColored(
        src=in_img,
        dst=None,
        h=h,
        hColor=h_color,
        templateWindowSize=patch_window_size,
        searchWindowSize=search_window_size,
    )

    # HtoD transfer
    d_img = htod_transfer_sync(
        host_mem=dh_memory.htod_mem, h_img=torch.from_numpy(out_img)
    )
    d_tensor: Tensor = img_to_tensor(d_img=d_img, tensor_dtype=in_x.dtype, flip_r_b=True)

    frame.tensor = d_tensor
    return frame



def cv2_bilateral_(
    frame: NnFrame,
    params: str | None,
) -> NnFrame:
    verbose : bool = False

    param_list: list[str] = params.split(":")
    radius, sigma_color, sigma_space = 4, 11, 11
    if len(param_list) >= 1:
        radius = int(param_list[0])
    if len(param_list) >= 2:
        sigma_color = float(param_list[1])
    if len(param_list) >= 3:
        sigma_space = float(param_list[2])

    # Get tensor from frame
    tensor: Tensor = frame.tensor
    if verbose:
        print(purple(f"[V][F] cv2 bilateral:"))
        print(
            purple(f"[V][F]  in_tensor:"),  f"{tensor.shape}, {tensor.dtype}"
        )

    # DtoH transfer
    in_x: Tensor = frame.tensor
    d_img: Tensor = tensor_to_img(tensor=in_x, img_dtype=np.uint8, flip_r_b=True)
    dh_memory = _DHMemory(shape=d_img.shape, dtype=d_img.dtype)
    in_img: np.ndarray = dtoh_transfer_sync(host_mem=dh_memory.dtoh_mem, d_img=d_img)

    # Apply filter on the numpy image
    in_img = in_img.astype(np.float32)
    out_img = cv2.bilateralFilter(
        src=in_img,
        d=(2 * radius + 1),
        sigmaColor=sigma_color,
        sigmaSpace=sigma_space
    )

    # HtoD transfer
    d_img = htod_transfer_sync(
        host_mem=dh_memory.htod_mem, h_img=torch.from_numpy(out_img)
    )
    d_tensor: Tensor = img_to_tensor(d_img=d_img, tensor_dtype=in_x.dtype, flip_r_b=True)

    frame.tensor = d_tensor
    return frame
