# -*- coding: utf-8 -*-
import sys
# sys.path.append('scripts')


from img_toolbox.real_cugan import real_cugan_executor
from img_toolbox.pytorch import pytorch_executor
from img_toolbox.python import python_executor
from img_toolbox.scunet import scunet_executor
from img_toolbox.ffmpeg import ffmpeg_executor
from img_toolbox.avisynth import avisynth_executor
from img_toolbox.animesr import animesr_executor


EXECUTORS = {
    'animesr': animesr_executor,
    'real_cugan': real_cugan_executor,
    'pytorch': pytorch_executor,
    'scunet': scunet_executor,
    'python': python_executor,
    'ffmpeg': ffmpeg_executor,
    'avisynth': avisynth_executor,
}


