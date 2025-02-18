import re
import sys
from typing import Any
from pynnlib import (
    nnlib,
    NnModel,
    TrtModel,
    ShapeStrategy,
    Idtype,
)
from utils.media import VideoInfo
from utils.p_print import *
from utils.path_utils import path_split



def convert_to_tensorrt(
    arguments: Any,
    video_info: VideoInfo | None,
    model: NnModel,
    device: str,
    dtype: Idtype,
) -> TrtModel | None:
    trt_model: TrtModel | None = None

    # Shape strategy
    shape_strategy: ShapeStrategy = ShapeStrategy()
    if arguments.static:
        shape_strategy.static = True
        in_shape = video_info['shape']
        shape_strategy.opt_size = (in_shape[1], in_shape[0])

    else:

        def _str_to_size(size_str: str) -> tuple[int, int] | None:
            if (match := re.match(re.compile("^(\d+)x(\d+)$"), size_str)):
                return (int(match.group(1)), int(match.group(2)))
            return None

        if arguments.opt_size == 'input':
            in_shape = video_info['shape']
            shape_strategy.opt_size = (in_shape[1], in_shape[0])

        else:
            opt_size = _str_to_size(arguments.opt_size)
            if opt_size is None:
                sys.exit(red(f"[E] Erroneous option: {arguments.opt_size}"))
            shape_strategy.opt_size = opt_size

        if not arguments.fixed_size:
            min_size = _str_to_size(arguments.min_size)
            if min_size is None:
                sys.exit(red(f"[E] Erroneous option: {arguments.min_size}"))
            shape_strategy.min_size = min_size

            max_size = _str_to_size(arguments.max_size)
            if max_size is None:
                sys.exit(red(f"[E] Erroneous option: {arguments.max_size}"))
            shape_strategy.max_size = max_size

        else:
            shape_strategy.min_size = shape_strategy.opt_size
            shape_strategy.max_size = shape_strategy.opt_size

        if not shape_strategy.is_valid():
            sys.exit(red(f"[E] Erroneous sizes"))

    # Optimization
    opt_level = arguments.opt_level
    opt_level = None if not 1 <= opt_level <= 5 else opt_level

    trt_model: TrtModel = nnlib.convert_to_tensorrt(
        model=model,
        shape_strategy=shape_strategy,
        dtype=dtype,
        optimization_level=opt_level,
        opset=arguments.opset,
        device=device,
        out_dir=path_split(model.filepath)[0],
    )

    return trt_model
