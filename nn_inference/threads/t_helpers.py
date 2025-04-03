from pprint import pprint
from typing import Any
from utils.p_print import *
from processing import (
    supported_ffmpeg_filters,
)
from nn_inference.resource_mgr import NnFrame
from nn_inference.model_mgr import ModelManager
from pynnlib import (
    NnModel
)


def get_first_nnmodel_step_no(filters: list[Any]) -> int:
    """Before this step, process the frame in the decoder thread"""
    for i, f in enumerate(filters):
        if isinstance(f, str):
            break

    if i == len(filters) - 1:
        print(red("get_first_nnmodel_step_no: at least a model is required"))
        return -1

    return min(i, len(filters) - 1)



def get_encoder_step_no(filters: list[Any]) -> int:
    """Used to detect at which step the frame has to be sent to the encoder"""
    encoder_step_no: int = len(filters) + 1
    # parse the list in reverse orderand stop as sson as
    # filter is not executed in the encoder.
    # cv2 filters are done in the encoder thread
    for i, f in enumerate(reversed(filters)):
        if (
            not isinstance(f, tuple | list)
            or f[0] not in supported_ffmpeg_filters
        ):
            encoder_step_no = len(filters) - i
            break

    print(red(f"encoder step no. {encoder_step_no}"))
    return encoder_step_no



def get_first_nnmodel(filters: list[Any], model_manager: ModelManager) -> NnModel:
    step_no = get_first_nnmodel_step_no(filters)
    nn_model: NnModel = model_manager.model(filters[step_no])
    return nn_model



def get_last_nnmodel(filters: list[Any], model_manager: ModelManager) -> NnModel:
    step_no = get_encoder_step_no(filters) - 1
    nn_model: NnModel = model_manager.model(filters[step_no])
    return nn_model



def patch_next_step_no_(frame: NnFrame, model_manager: ModelManager) -> None:
    """Skip following model if possible: Inpaint model,
    """
    if frame.step_no < frame.encoder_step_no:
        # Skip following model if inpaint
        # and (task is dsr or not to be processed)
        next_model: NnModel = model_manager.model(frame.sequence[frame.step_no])
        if next_model.arch.infer_type.type == 'inpaint':
            if (
                frame.scene['task'].name == 'dsr'
                or frame.src_scene['dsr'].get(frame_no=frame.f_no) is None
            ):
                frame.step_no += 1
