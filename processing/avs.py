from dataclasses import dataclass
import os
from pathlib import Path
from pprint import pprint
import sys
from typing import Any, Literal

from utils.media import FieldOrder, VideoInfo
from utils.p_print import *
from utils.path_utils import absolute_path
from utils.pxl_fmt import PIXEL_FORMAT
from utils.tools import ffmpeg_exe



@dataclass(slots=True)
class QtgmcSettings:
    # http://avisynth.nl/index.php/QTGMC
    preset: Literal[
        "Placebo",
        "Very Slow",
        "Slower",
        "Slow",
        "Medium",
        "Fast",
        "Faster",
        "Very Fast",
        "Super Fast",
        "Ultra Fast",
        "Draft"
    ] = "Slower"
    tr0: int | None = None
    tr1: int | None = None
    tr2: int | None = None
    rep0: int | None = None
    rep1: int | None = None
    rep2: int | None = None
    rep_chroma: bool = False
    edi_mode: Literal[
        "Bob"
        "NNEDI3",
        "NNEDI2",
        "NNEDI",
        "EEDI3+NNEDI3",
        "EEDI3",
        "EEDI2",
        "Yadif",
        "TDeint",
        "RepYadif"
    ] | None = None
    # Sharpness
    sharpness: float | None = None
    # Source match / lossless
    source_match: int = 0
    # Denoising
    denoise_ez_denoise: float | None = None
    denoise_ez_keep_grain: float | None = None
    denoise_preset: Literal[
        "Slower",
        "Slow",
        "Medium",
        "Fast",
        "Faster"
    ] = "Fast"
    denoise_filter: Literal[
        "dfttest",
        "fft3dfilter"
    ] | None = None
    edi_threads: int | None = None






def generate_avs_script(
    in_video_info: VideoInfo,
    out_video_info: VideoInfo,
    settings: QtgmcSettings
) -> Path | str:
    script = """
        SetFilterMTMode("DEFAULT_MT_MODE", MT_MULTI_INSTANCE)
        SetFilterMTMode("FFVideoSource", MT_SERIALIZED)
        SetFilterMTMode ("QTGMC", MT_MULTI_INSTANCE)

        FFVideoSource("{filepath}", cache=false)
        {field_order}
        {trim}
        {qtgmc}
        SelectEven()
        {convert}()

        {prefetch}
    """
    pprint(in_video_info)
    pprint(out_video_info)

    vi = out_video_info

    field_order: str = ""
    if in_video_info['field_order'] in (FieldOrder.TOP_FIELD_FIRST, FieldOrder.TOP_FIELD_BOTTOM):
        field_order = "AssumeTFF()"
    elif in_video_info['field_order'] in (FieldOrder.BOTTOM_FIELD_FIRST, FieldOrder.BOTTOM_FIELD_TOP):
        field_order = "AssumeBFF()"

    trim: str = ""
    start = vi['frame_start'] if vi['frame_start'] > 0 else 0
    end = (
        vi['frame_start'] + vi['frame_count'] - 1
        if vi['frame_count'] > 0
        else -1
    )
    if start > 0 or end > -1:
        trim = f"trim({start}, {end})"

    qtgmc_settings: dict[str, Any] = {
        'Preset': f"\"{settings.preset}\"",
        'TR0': settings.tr0,
        'TR1': settings.tr1,
        'TR2': settings.tr2,
        'Rep0': settings.rep0,
        'Rep1': settings.rep1,
        'Rep2': settings.rep2,
        'RepChroma': settings.rep_chroma,
        'EdiMode': f"\"{settings.edi_mode}\"",
        'Sharpness': settings.sharpness,
        'SourceMatch': settings.source_match,
        'EZDenoise': settings.denoise_ez_denoise,
        'EZKeepGrain': settings.denoise_ez_keep_grain,
        'NoisePreset': f"\"{settings.denoise_preset}\"",
        'Denoiser': f"\"{settings.denoise_filter}\"",
        'EdiThreads': settings.edi_threads
    }

    qtgmc_arguments: list[str] = [
        f"__t__{name}={value}"
        for name, value in qtgmc_settings.items()
        if value is not None
    ]
    qtgmc = ', \\\n'.join(qtgmc_arguments)
    qtgmc: str = f"QTGMC(\\\n{qtgmc}\\\n)"

    prefetch: str = (
        f"Prefetch({settings.edi_threads})"
        if settings.edi_threads is not None
        else ""
    )

    if out_video_info['pix_fmt']:
        v = PIXEL_FORMAT[in_video_info['pix_fmt']]
    print(v)
    sys.exit()
    convert = "ConvertToRGB24"

    script = script.format(
        filepath=in_video_info['filepath'],
        field_order=field_order,
        trim=trim,
        qtgmc=qtgmc,
        prefetch=prefetch,
        convert=convert
    )

    script_filepath = absolute_path(
            os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            os.pardir,
            os.pardir,
            "deinterlace.avs"
        )
    )
    with open(script_filepath, mode='w') as script_file:
        for line in script.split('\n'):
            script_file.write(f"{line.strip()}\n".replace("__t__", "    "))

    return script_filepath



def create_ffmpeg_command(self) -> str:
    params = self.parameters

    vi: VideoInfo = self.video_info()
    in_filepath: str = absolute_path(vi['filepath'])
    out_filepath: str = absolute_path(vi['out_filepath'])

    ffmpeg_command = [
        ffmpeg_exe,
        "-hide_banner",
        "-loglevel", "info",
        '-f', 'rawvideo',
        '-i', in_filepath,
        '-o', out_filepath
    ]


    # Encoder
    ffmpeg_command.extend([
        "-vcodec", f"{params.encoder.value}"
    ])

    # Encoder settings
    settings = params.encoder_settings
    if settings is not None:
        ffmpeg_command.extend(
            list([[f"{k}", f"{v}"] for k, v in settings.__dict__.items()])
        )

    # Output filepath
    ffmpeg_command.append(out_filepath)
    if params.overwrite:
        ffmpeg_command.append('-y')


    print(lightgrey(f"ffmpeg_command: {' '.join(self.ffmpeg_command)}"))
    return ffmpeg_command
