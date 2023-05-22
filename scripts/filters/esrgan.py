# -*- coding: utf-8 -*-
from collections import OrderedDict
import cv2
import logging
from pathlib import Path
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
from utils.architecture.RRDB import RRDBNet as ESRGAN
from utils.architecture.SPSR import SPSRNet as SPSR
from utils.architecture.SRVGG import SRVGGNetCompact as RealESRGANv2

import pickle
from types import SimpleNamespace

from utils.pretty_print import *

class UnsupportedModel(Exception):
    pass

safe_list = {
    ("collections", "OrderedDict"),
    ("typing", "OrderedDict"),
    ("torch._utils", "_rebuild_tensor_v2"),
    ("torch", "BFloat16Storage"),
    ("torch", "FloatStorage"),
    ("torch", "HalfStorage"),
    ("torch", "IntStorage"),
    ("torch", "LongStorage"),
}


class RestrictedUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        # Only allow required classes to load state dict
        if (module, name) not in safe_list:
            raise pickle.UnpicklingError(
                "Global '{}.{}' is forbidden".format(module, name)
            )
        return super().find_class(module, name)


RestrictedUnpickle = SimpleNamespace(
    Unpickler=RestrictedUnpickler,
    __name__="pickle",
    load=lambda *args, **kwargs: RestrictedUnpickler(*args, **kwargs).load(),
)



PyTorchSRModels = (RealESRGANv2, SPSR, ESRGAN)
PyTorchSRModel = Union[
    RealESRGANv2,
    SPSR,
    ESRGAN,
]

PyTorchModels = (*PyTorchSRModels,None)
PyTorchModel = Union[PyTorchSRModel,None]



class Esrgan_upscale():
    model_str: str = None
    input: Path = None
    output: Path = None
    reverse: bool = None
    skip_existing: bool = None
    delete_input: bool = None
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
    log: logging.Logger = None

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
    model: Union[torch.nn.Module, ESRGAN, RealESRGANv2, SPSR] = None

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
        log: logging.Logger = logging.getLogger(),
    ) -> None:
        self.model_str = ""
        self.input = ""
        self.output = ""
        self.reverse = False
        self.skip_existing = True
        self.delete_input = False
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
        self.log = log
        self.__device_id = device_id
        if self.fp16:
            torch.set_default_tensor_type(
                torch.HalfTensor if self.cpu else torch.cuda.HalfTensor
            )

    # This code is a somewhat modified version of  joeyballentine's fork
    #  of BlueAmulet's fork which is a fork of ESRGAN by Xinntao
    def run(self, img: np.ndarray, scale:int) -> np.ndarray:

        split_depths = {}

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

        i = 0

        if self.cache_max_split_depth and len(split_depths.keys()) > 0:
            rlt, depth = ops.auto_split_upscale(
                img,
                self.upscale,
                self.scale,
                max_depth=split_depths[i],
            )
        else:
            rlt, depth = ops.auto_split_upscale(
                img, self.upscale, self.scale
            )
            split_depths[i] = depth

        final_scale *= self.scale

        img = rlt.astype("uint8")

        if self.seamless:
            img = self.crop_seamless(img, final_scale)

        return img



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





    def load_state_dict(self, state_dict) -> PyTorchModel:

        state_dict_keys = list(state_dict.keys())

        if "params_ema" in state_dict_keys:
            state_dict = state_dict["params_ema"]
        elif "params-ema" in state_dict_keys:
            state_dict = state_dict["params-ema"]
        elif "params" in state_dict_keys:
            state_dict = state_dict["params"]

        state_dict_keys = list(state_dict.keys())
        # SRVGGNet Real-ESRGAN (v2)
        if "body.0.weight" in state_dict_keys and "body.1.weight" in state_dict_keys:
            print_lightcyan(f"SRVGGNet Real-ESRGAN (v2)")
            model = RealESRGANv2(state_dict)

        # SPSR (ESRGAN with lots of extra layers)
        elif "f_HR_conv1.0.weight" in state_dict:
            print_lightcyan(f"SPSR")
            model = SPSR(state_dict)

        # # Swift-SRGAN
        # elif (
        #     "model" in state_dict_keys
        #     and "initial.cnn.depthwise.weight" in state_dict["model"].keys()
        # ):
        #     model = SwiftSRGAN(state_dict)
        # # HAT -- be sure it is above swinir
        # elif "layers.0.residual_group.blocks.0.conv_block.cab.0.weight" in state_dict_keys:
        #     model = HAT(state_dict)
        # # SwinIR
        # elif "layers.0.residual_group.blocks.0.norm1.weight" in state_dict_keys:
        #     if "patch_embed.proj.weight" in state_dict_keys:
        #         model = Swin2SR(state_dict)
        #     else:
        #         model = SwinIR(state_dict)
        # # GFPGAN
        # elif (
        #     "toRGB.0.weight" in state_dict_keys
        #     and "stylegan_decoder.style_mlp.1.weight" in state_dict_keys
        # ):
        #     model = GFPGANv1Clean(state_dict)
        # # RestoreFormer
        # elif (
        #     "encoder.conv_in.weight" in state_dict_keys
        #     and "encoder.down.0.block.0.norm1.weight" in state_dict_keys
        # ):
        #     model = RestoreFormer(state_dict)
        # elif (
        #     "encoder.blocks.0.weight" in state_dict_keys
        #     and "quantize.embedding.weight" in state_dict_keys
        # ):
        #     model = CodeFormer(state_dict)
        # # LaMa
        # elif (
        #     "model.model.1.bn_l.running_mean" in state_dict_keys
        #     or "generator.model.1.bn_l.running_mean" in state_dict_keys
        # ):
        #     model = LaMa(state_dict)
        # # MAT
        # elif "synthesis.first_stage.conv_first.conv.resample_filter" in state_dict_keys:
        #     model = MAT(state_dict)
        # # Omni-SR
        # elif (
        #     "total_ops" in state_dict_keys
        #     and "residual_layer.0.total_ops" in state_dict_keys
        # ):
        #     model = OmniSR(state_dict)

        # Regular ESRGAN, "new-arch" ESRGAN, Real-ESRGAN v1
        else:
            print_lightcyan(f"ESRGAN")
            try:
                model = ESRGAN(state_dict)
            except:
                # pylint: disable=raise-missing-from
                print_red("ERROR loading model")
                raise UnsupportedModel
        return model



    def load_model(self, model_path: str):
        print("\t\t\tload_model: %s" % (os.path.abspath(model_path)))

        exec_options_full_device = f"cuda:{self.__device_id}"
        state_dict = torch.load(
            model_path,
            map_location=self.device,
            pickle_module=RestrictedUnpickle,
        )
        model = self.load_state_dict(state_dict)


        if model is None:
            print_yellow(f"state not found")
            # SRVGGNet Real-ESRGAN (v2)
            if (
                "params" in state_dict.keys()
                and "body.0.weight" in state_dict["params"].keys()
            ):
                model = RealESRGANv2(state_dict)
                self.in_nc = self.model.num_in_ch
                self.out_nc = self.model.num_out_ch
                self.nf = self.model.num_feat
                self.nb = self.model.num_conv
                self.scale = self.model.scale

            # SPSR (ESRGAN with lots of extra layers)
            elif "f_HR_conv1.0.weight" in state_dict:
                model = SPSR(state_dict)
                self.in_nc = self.model.in_nc
                self.out_nc = self.model.out_nc
                self.nf = self.model.num_filters
                self.nb = self.model.num_blocks
                self.scale = self.model.scale

            # Regular ESRGAN, "new-arch" ESRGAN, Real-ESRGAN v1
            else:
                model = ESRGAN(state_dict)
                self.in_nc = self.model.in_nc
                self.out_nc = self.model.out_nc
                self.nf = self.model.num_filters
                self.nb = self.model.num_blocks
                self.scale = self.model.scale

        else:
            # print(type(model))
            if type(model) is RealESRGANv2:
                self.in_nc = model.num_in_ch
                self.out_nc = model.num_out_ch
                self.scale = model.scale
                self.nf = model.num_feat
                self.nb = model.num_conv
            elif type(model) is SPSR:
                self.in_nc = model.in_nc
                self.out_nc = model.out_nc
                self.nf = model.num_filters
                self.nb = model.num_blocks
                self.scale = model.scale
            elif type(model) is ESRGAN:
                self.in_nc = model.in_nc
                self.out_nc = model.out_nc
                self.nf = model.num_filters
                self.nb = model.num_blocks
                self.scale = model.scale
            else:
                print_red("model not supported")


        for _, v in model.named_parameters():
            v.requires_grad = False
        model.eval()
        model = model.to(torch.device(exec_options_full_device))
        if not hasattr(model, "supports_fp16"):
            model.supports_fp16 = False  # type: ignore
        should_use_fp16 = self.fp16
        if should_use_fp16:
            # print_lightgrey("use fp16")
            self.model = model.half()
        else:
            # print_lightgrey("use float")
            self.model = model.float()




    # This code is a somewhat modified version of BlueAmulet's fork of ESRGAN by Xinntao
    def upscale(self, img: np.ndarray) -> np.ndarray:
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
                self.log.warning("Truncating image channels")
                img = img[:, :, : self.in_nc]
            # pad with solid alpha channel
            elif img.shape[2] == 3 and self.in_nc == 4:
                img = np.dstack((img, np.full(img.shape[:-1], 1.0)))
            output = self.process(img)

        output = (output * 255.0).round()

        return output


    def crop_seamless(self, img: np.ndarray, scale: int) -> np.ndarray:
        img_height, img_width = img.shape[:2]
        y, x = 16 * scale, 16 * scale
        h, w = img_height - (32 * scale), img_width - (32 * scale)
        img = img[y : y + h, x : x + w]
        return img

