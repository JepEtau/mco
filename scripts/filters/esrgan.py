# -*- coding: utf-8 -*-
import cv2
import numpy as np
import os
import sys
import torch
from typing import (
    Optional,
    Union,
)

from upscale import (
    AlphaOptions,
    SeamlessOptions
)
from utils.architecture.RRDB import RRDBNet
import utils.dataops as ops

class Esrgan_upscale():
    seamless: SeamlessOptions = None
    cpu: bool = None
    fp16: bool = None
    # device_id: int = None
    cache_max_split_depth: bool = None
    binary_alpha: bool = None
    ternary_alpha: bool = None
    alpha_threshold: float = None
    alpha_boundary_offset: float = None
    alpha_mode: AlphaOptions = None

    device: torch.device = None
    in_nc: int = None
    out_nc: int = None
    last_model: str = None
    last_in_nc: int = None
    last_out_nc: int = None
    last_nf: int = None
    last_nb: int = None
    last_scale: int = None
    last_kind: str = None
    model: Union[torch.nn.Module, RRDBNet] = None

    def __init__(
        self,
        seamless: Optional[SeamlessOptions] = None,
        cpu: bool = False,
        fp16: bool = False,
        device_id: int = 0,
        cache_max_split_depth: bool = False,
        binary_alpha: bool = False,
        ternary_alpha: bool = False,
        alpha_threshold: float = 0.5,
        alpha_boundary_offset: float = 0.2,
        alpha_mode: Optional[AlphaOptions] = None,
    ) -> None:
        self.seamless = seamless
        self.cpu = cpu
        self.fp16 = fp16
        self.device = torch.device('cpu' if self.cpu else f"cuda:{device_id}")
        self.cache_max_split_depth = cache_max_split_depth
        self.binary_alpha = binary_alpha
        self.ternary_alpha = ternary_alpha
        self.alpha_threshold = alpha_threshold
        self.alpha_boundary_offset = alpha_boundary_offset
        self.alpha_mode = alpha_mode
        if self.fp16:
            torch.set_default_tensor_type(
                torch.HalfTensor if self.cpu else torch.cuda.HalfTensor
            )


    def load_model(self, model_path: str):
        print("\t\t\tload_model: %s" % (os.path.abspath(model_path)))
        state_dict = torch.load(os.path.abspath(model_path))

        # Regular ESRGAN, "new-arch" ESRGAN, Real-ESRGAN v1
        self.model = RRDBNet(state_dict)
        self.in_nc = self.model.in_nc
        self.out_nc = self.model.out_nc
        self.nf = self.model.num_filters
        self.nb = self.model.num_blocks
        self.scale = self.model.scale

        del state_dict
        self.model.eval()
        for k, v in self.model.named_parameters():
            v.requires_grad = False
        self.model = self.model.to(self.device)


    def upscale(self, img: np.ndarray, scale:int) -> np.ndarray:
        # Seamless modes
        if self.seamless == SeamlessOptions.TILE:
            img = cv2.copyMakeBorder(img, 16, 16, 16, 16, cv2.BORDER_WRAP)
        elif self.seamless == SeamlessOptions.MIRROR:
            img = cv2.copyMakeBorder(
                img, 16, 16, 16, 16, cv2.BORDER_REFLECT_101
            )
        elif self.seamless == SeamlessOptions.REPLICATE:
            img = cv2.copyMakeBorder(img, 16, 16, 16, 16, cv2.BORDER_REPLICATE)
        elif self.seamless == SeamlessOptions.ALPHA_PAD:
            img = cv2.copyMakeBorder(
                img, 16, 16, 16, 16, cv2.BORDER_CONSTANT, value=[0, 0, 0, 0]
            )
        final_scale: int = 1


        rlt, depth = ops.auto_split_upscale(
            lr_img=img,
            upscale_function=self.__upscale,
            scale=scale
        )
        img = rlt.astype("uint8")
        if self.seamless:
            img = self.crop_seamless(img, final_scale)

        return img


    # This code is a somewhat modified version of  joeyballentine's fork
    #  of BlueAmulet's fork which is a fork of ESRGAN by Xinntao
    def __upscale(self, img: np.ndarray) -> np.ndarray:
        """
        Upscales the image passed in with the specified model

                Parameters:
                        img: The image to upscale
                        model_path (string): The model to use

                Returns:
                        output: The processed image
        """

        img = img * 1.0 / np.iinfo(img.dtype).max

        if (
            img.ndim == 3
            and img.shape[2] == 4
            and self.in_nc == 3
            and self.out_nc == 3
        ):

            # Fill alpha with white and with black, remove the difference
            if self.alpha_mode == AlphaOptions.BG_DIFFERENCE:
                img1 = np.copy(img[:, :, :3])
                img2 = np.copy(img[:, :, :3])
                for c in range(3):
                    img1[:, :, c] *= img[:, :, 3]
                    img2[:, :, c] = (img2[:, :, c] - 1) * img[:, :, 3] + 1

                output1 = self.process(img1)
                output2 = self.process(img2)
                alpha = 1 - np.mean(output2 - output1, axis=2)
                output = np.dstack((output1, alpha))
                output = np.clip(output, 0, 1)
            # Upscale the alpha channel itself as its own image
            elif self.alpha_mode == AlphaOptions.ALPHA_SEPARATELY:
                img1 = np.copy(img[:, :, :3])
                img2 = cv2.merge((img[:, :, 3], img[:, :, 3], img[:, :, 3]))
                output1 = self.process(img1)
                output2 = self.process(img2)
                output = cv2.merge(
                    (
                        output1[:, :, 0],
                        output1[:, :, 1],
                        output1[:, :, 2],
                        output2[:, :, 0],
                    )
                )
            # Use the alpha channel like a regular channel
            elif self.alpha_mode == AlphaOptions.SWAPPING:
                img1 = cv2.merge((img[:, :, 0], img[:, :, 1], img[:, :, 2]))
                img2 = cv2.merge((img[:, :, 1], img[:, :, 2], img[:, :, 3]))
                output1 = self.process(img1)
                output2 = self.process(img2)
                output = cv2.merge(
                    (
                        output1[:, :, 0],
                        output1[:, :, 1],
                        output1[:, :, 2],
                        output2[:, :, 2],
                    )
                )
            # Remove alpha
            else:
                img1 = np.copy(img[:, :, :3])
                output = self.process(img1)
                output = cv2.cvtColor(output, cv2.COLOR_BGR2BGRA)

            if self.binary_alpha:
                alpha = output[:, :, 3]
                threshold = self.alpha_threshold
                _, alpha = cv2.threshold(alpha, threshold, 1, cv2.THRESH_BINARY)
                output[:, :, 3] = alpha
            elif self.ternary_alpha:
                alpha = output[:, :, 3]
                half_transparent_lower_bound = (
                    self.alpha_threshold - self.alpha_boundary_offset
                )
                half_transparent_upper_bound = (
                    self.alpha_threshold + self.alpha_boundary_offset
                )
                alpha = np.where(
                    alpha < half_transparent_lower_bound,
                    0,
                    np.where(alpha <= half_transparent_upper_bound, 0.5, 1),
                )
                output[:, :, 3] = alpha
        else:
            if img.ndim == 2:
                img = np.tile(
                    np.expand_dims(img, axis=2), (1, 1, min(self.in_nc, 3))
                )
            if img.shape[2] > self.in_nc:  # remove extra channels
                img = img[:, :, : self.in_nc]
            # pad with solid alpha channel
            elif img.shape[2] == 3 and self.in_nc == 4:
                img = np.dstack((img, np.full(img.shape[:-1], 1.0)))
            output = self.process(img)

        output = (output * 255.0).round()

        return output



    # This code is a somewhat modified version of  joeyballentine's fork
    #  of BlueAmulet's fork which is a fork of ESRGAN by Xinntao
    def process(self, img: np.ndarray):
        """
        Does the processing part of ESRGAN. This method only exists because the same block of code needs to be ran twice for images with transparency.

                Parameters:
                        img (array): The image to process

                Returns:
                        rlt (array): The processed image
        """
        if img.shape[2] == 3:
            img = img[:, :, [2, 1, 0]]
        elif img.shape[2] == 4:
            img = img[:, :, [2, 1, 0, 3]]
        img = torch.from_numpy(np.transpose(img, (2, 0, 1))).float()
        if self.fp16:
            img = img.half()
        img_LR = img.unsqueeze(0)
        img_LR = img_LR.to(self.device)

        output = self.model(img_LR).data.squeeze(0).float().cpu().clamp_(0, 1).numpy()
        if output.shape[0] == 3:
            output = output[[2, 1, 0], :, :]
        elif output.shape[0] == 4:
            output = output[[2, 1, 0, 3], :, :]
        output = np.transpose(output, (1, 2, 0))
        return output


    def crop_seamless(self, img: np.ndarray, scale: int) -> np.ndarray:
        img_height, img_width = img.shape[:2]
        y, x = 16 * scale, 16 * scale
        h, w = img_height - (32 * scale), img_width - (32 * scale)
        img = img[y : y + h, x : x + w]
        return img

