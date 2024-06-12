from collections import OrderedDict
from dataclasses import dataclass
import os
from pathlib import Path
from pprint import pprint
import re
import sys
from typing import Any, Literal

from utils.hash import calc_hash
from utils.media import FieldOrder, VideoInfo
from utils.p_print import *
from utils.path_utils import absolute_path, get_app_tempdir, path_split
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




def patch_avs_script(
    in_script_filepath: str,
    out_script_filepath: str,
    in_video_info: VideoInfo,
    trim_start: int = 0,
    trim_count: int = -1,
) -> str:
    with open(in_script_filepath, mode='r') as script:
        lines = script.readlines()

    if trim_count != -1 and trim_start + trim_count > in_video_info['frame_count']:
        raise ValueError(f"Erroneous trim value: {trim_start+trim_count} > {in_video_info['frame_count']}")

    trim_line: str = ""
    if trim_start != 0 and trim_count == -1:
        trim_line = "trim(%d, 0)\n" % (trim_start)
    elif trim_start != 0 and trim_count != -1:
        trim_line = "trim(%d, end=%d)\n" % (trim_start, (trim_start + trim_count - 1))

    filepath_replaced: bool = False
    trim_replaced: bool = False
    for i, line in enumerate(lines):

        # Discard comments
        if (search := re.search(re.compile("^\s*#"), line)):
            continue

        # Replace input file
        if not filepath_replaced:
            found: bool = False
            if (search := re.search(re.compile("\s*FFMPEGSource2\(\s*\"(.+)\"\s*"), line)):
                found = True
            elif (search := re.search(re.compile("\s*FFMPEGSource2\(\s*source\s=\s*\"(.+)\""), line)):
                found = True
            if found:
                lines[i] = line.replace(search.group(1), in_video_info['filepath'])
                filepath_replaced = True

        # Trim
        if not trim_replaced:
            if (search := re.search(re.compile("\s*trim\(([^\)]+)\)"), line)):
                lines[i] = trim_line
                trim_replaced = True

    if (trim_start != 0 or trim_count != -1) and not trim_replaced:
        raise ValueError("Missing trim instruction")

    with open(out_script_filepath, mode='w') as script:
        script.write(''.join(lines))



def _clean_str(line: str):
    cleaned: str = line
    for c in ('\\', '\"', ' ', '\r', '\n'):
        cleaned = cleaned.replace(c, '')
    return cleaned.strip()


_ordered_arg_keys: tuple[str] = (
    "preset",
    'TR0', 'TR1', 'TR2',
    'Rep0', 'Rep1', 'Rep2', 'RepChroma',
    'EdiMode',
    'ChromaEdi',
    'Sharpness',
    'SourceMatch',
    'EZDenoise',
    'EZKeepGrain',
    'NoisePreset',
    'Denoiser',
    'EdiThreads'
)


def get_qtgmc_args(
    script_filepath: str
) -> OrderedDict[str, str]:

    # Open script filepath
    script: str = ""
    with open(script_filepath, mode='r') as f:
        for line in f.readlines():
            # Discard comments
            if (search := re.search(re.compile("(.*)#.*"), line)):
                script += search.group(1)
                continue
            script += line
    script = _clean_str(script)
    if (qtgmc_arg:= re.search(re.compile("QTGMC\(([^\)]+)\)"), _clean_str(script))):
        arguments: list[str] = qtgmc_arg.group(1).split(',')
    else:
        raise ValueError("QTGMC function not found in script")

    # get arguments
    qtgmc_args: dict[str, str] = {}
    for _arg in arguments:
        k_value = _arg.split('=')
        if len(k_value) != 2:
            raise ValueError(f"unrecognized argument format for QTGMC function")
        k, value = k_value
        qtgmc_args[k.strip()] = _clean_str(value)

    # Sort keys
    keys: list[str] = list([k for k in _ordered_arg_keys if k in qtgmc_args.keys()])
    keys.extend(list([k for k in qtgmc_args.keys() if k not in _ordered_arg_keys]))

    ordered_dict = OrderedDict()
    for k in keys:
        ordered_dict[k] = qtgmc_args[k]

    return ordered_dict



def create_hash(args_dict: OrderedDict[str, str]) -> tuple[str, str]:
    """Returns hashcode and values for log"""
    qtgmc_arg_str: str = ", ".join([f"{k}={v}" for k, v in args_dict.items()])

    return calc_hash(qtgmc_arg_str), qtgmc_arg_str



def create_qtgmc_ffmpeg_command(
    in_video_info: VideoInfo,
    qtgmc_args: dict[str, str],
    out_filepath: str | None = None
) -> list[str]:
    ffmpeg_command: list[str] = [
        ffmpeg_exe,
        "-hide_banner",
        "-loglevel", "warning",
        "-stats",
    ]

    # Input file
    # ffmpeg_command.extend(["-t", "10"])
    ffmpeg_command.extend(["-i", in_video_info['filepath']])

    # Resize with SAR
    in_h, in_w = in_video_info['shape'][:2]
    resize = f"""
        scale=
        {int((in_w * float(in_video_info['sar'][0]) / in_video_info['sar'][1]) + 0.5)}
        :{in_h}
        :sws_flags=
            bilinear
            + full_chroma_int
            + full_chroma_inp
            + accurate_rnd
            + bitexact
    """
    ffmpeg_filter = _clean_str(resize)
    ffmpeg_command.extend([
        "-filter_complex", f"[0:v]{ffmpeg_filter}[outv]",
        "-map", "[outv]"
    ])

    # Frame rate
    fps: float | int | tuple[int, int] = in_video_info['frame_rate_r']
    ffmpeg_command.extend([
        "-r",
        '/'.join(map(str, fps)) if isinstance(fps, tuple | list) else f"{fps}"
    ])

    ffmpeg_command.extend([
        "-pix_fmt", # out_video_info['pix_fmt']
        "yuv420p"
    ])

    ffmpeg_command.extend([
        "-an",
        "-sn",
        "-map_chapters", "-1"
    ])

    if qtgmc_args.keys():
        ffmpeg_command.extend([
            "-movflags",
            "use_metadata_tags",
        ])
        i: int = 1
        for k, v in qtgmc_args.items():
            ffmpeg_command.extend([
                "-metadata:s:v:0",
                f"qtgmc_{i:02}_{k}={v}"
            ])
            i += 1

    ffmpeg_command.extend([out_filepath, "-y"])
    return ffmpeg_command
