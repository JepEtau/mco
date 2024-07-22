from collections import OrderedDict
from dataclasses import dataclass
import os
from pathlib import Path
from pprint import pprint
import re
import sys
from typing import Any, Literal

from utils.hash import calc_hash
from utils.logger import main_logger
from utils.media import FieldOrder, VideoInfo
from utils.p_print import *
from utils.path_utils import absolute_path, get_extension
from utils.pxl_fmt import PIXEL_FORMAT
from utils.time_conversions import frame_to_sexagesimal
from utils.tools import ffmpeg_exe, avs_dir, nnedi3_weights
from parsers import db

g_deint_algorithms = [
    'nnedi',
    'bob',
    'bwdif',
    'decomb',
    'estdif',
    'kerneldeint',
    'mcdeint',
    'w3fdif',
    'yadif'
]
if sys.platform == 'win32':
    g_deint_algorithms.extend([
        'qtgmc'
    ])



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



def get_template_script(k_ep: str, k_ed: str) -> str:
    # Find AviSynth+ template. Priorities: edition, episode, global
    db_directories: dict[str, str] = db['common']['directories']
    ep_db_dir: str = os.path.join(db_directories['config'], k_ep)
    template_script: str = ''
    for script in (
        os.path.join(ep_db_dir, f"{k_ep}_{k_ed}_deint.avs"),
        os.path.join(ep_db_dir, f"{k_ep}_deint.avs"),
        os.path.join(db_directories['config'], f"deint.avs")
    ):
        if os.path.exists(script):
            template_script = script
            break

    if template_script == '':
        raise ValueError(f"No deinterlace script found for {k_ed}:{k_ep}")
    return template_script



def generate_avs_script(
    in_video_info: VideoInfo,
    out_video_info: VideoInfo,
    settings: QtgmcSettings
) -> Path | str:
    script = """
        SetFilterMTMode("DEFAULT_MT_MODE", MT_MULTI_INSTANCE)
        SetFilterMTMode("FFMPEGSource2", MT_SERIALIZED)
        SetFilterMTMode ("QTGMC", MT_MULTI_INSTANCE)

        FFMPEGSource2("{filepath}", cache=false)
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




def generate_avs_script(
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

    main_logger.debug(f"trim: start: {trim_start}, count: {trim_count}")
    trim_line: str = ""
    if trim_start != 0 and trim_count == -1:
        trim_line = f"trim({trim_start}, 0)\n"
    elif trim_start == 0 and trim_count != -1:
        trim_line = f"trim({trim_start}, {trim_start + trim_count - 1})\n"
    elif trim_start != 0 or trim_count != -1:
        trim_line = f"trim({trim_start}, {trim_start + trim_count - 1})\n"
    main_logger.debug(f"trim_line: {trim_line}")

    filepath_replaced: bool = False
    trim_replaced: bool = False
    for i, line in enumerate(lines):

        # Discard comments
        if (search := re.search(re.compile(r"^\s*#"), line)):
            continue

        # Replace input file
        if not filepath_replaced:
            found: bool = False
            if (search := re.search(re.compile(r"\s*FFMPEGSource2\(\s*\"(.+)\"\s*"), line)):
                found = True
            elif (search := re.search(re.compile(r"\s*FFMPEGSource2\(\s*source\s=\s*\"(.+)\""), line)):
                found = True
            elif (search := re.search(re.compile(r"\s*FFVideoSource\(\s*\"(.+)\"\s*"), line)):
                found = True
            elif (search := re.search(re.compile(r"\s*FFVideoSource\(\s*source\s=\s*\"(.+)\""), line)):
                found = True
            if found:
                lines[i] = line.replace(search.group(1), in_video_info['filepath'])
                filepath_replaced = True

        # Trim
        if not trim_replaced:
            if (search := re.search(re.compile(r"\s*trim\(([^\)]+)\)"), line)):
                lines[i] = trim_line
                trim_replaced = True

    if not filepath_replaced:
        raise ValueError(red("Error: failed to modify input video"))
    if not trim_replaced and (trim_start != 0 or trim_count != -1):
        raise ValueError(red("Error: failed to modify trim values"))

    # Imports
    ignore: tuple[str] = (
        "AviSynth.dll"
    )
    import_lines: list[str] = ["ClearAutoloadDirs()"]
    for root, _, files in os.walk(avs_dir):
        for f in files:
            if f in ignore:
                continue
            fp: str = os.path.join(root, f)
            ext: str = get_extension(fp)
            if ext == '.dll':
                import_lines.append(f"LoadPlugin(\"{fp}\")")
            elif ext == '.avsi':
                import_lines.append(f"Import(\"{fp}\")")
    import_lines.append('\n')

    with open(out_script_filepath, mode='w') as script:
        script.write('\n'.join(import_lines))
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
            if (search := re.search(re.compile(r"(.*)#.*"), line)):
                script += search.group(1)
                continue
            script += line
    script = _clean_str(script)
    if (qtgmc_arg:= re.search(re.compile(r"QTGMC\(([^\)]+)\)"), _clean_str(script))):
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



def calc_deint_hash(args_dict: OrderedDict[str, str]) -> tuple[str, str]:
    """Returns hashcode and values for log"""
    qtgmc_arg_str: str = ", ".join([f"{k}={v}" for k, v in args_dict.items()])

    return calc_hash(qtgmc_arg_str), qtgmc_arg_str



def qtgmc_deint_command(
    in_video_info: VideoInfo,
    script: str,
    qtgmc_args: dict[str, str],
    out_filepath: str
) -> list[str]:
    ffmpeg_command: list[str] = [
        ffmpeg_exe,
        "-hide_banner",
        "-loglevel", "warning",
        "-stats",
    ]

    # Avisynth+ file
    ffmpeg_command.extend(["-i", script])

    # Resize with SAR
    in_h, in_w = in_video_info['shape'][:2]
    if in_video_info['sar'][0] >= in_video_info['sar'][1]:
        in_w = int((in_w * float(in_video_info['sar'][0]) / in_video_info['sar'][1]) + 0.5)
    else:
        in_h = int((in_h * float(in_video_info['sar'][1]) / in_video_info['sar'][0]) + 0.5)

    resize = f"""
        scale={in_w}:{in_h}:sws_flags=
            bilinear
            + full_chroma_int
            + full_chroma_inp
            + accurate_rnd
            + bitexact
    """

    # FFmpeg complex filter
    ffmpeg_filter = _clean_str(resize)
    ffmpeg_command.extend([
        "-filter_complex", f"[0:v]{ffmpeg_filter}[outv]",
        "-map", "[outv]"
    ])

    # Frame rate
    fps: float | int | tuple[int, int] = in_video_info['frame_rate_r']
    # ffmpeg_command.extend([
    #     "-r",
    #     '/'.join(map(str, fps)) if isinstance(fps, tuple | list) else f"{fps}"
    # ])
    ffmpeg_command.extend([
        "-r", "25"
    ])
    ffmpeg_command.extend([
        "-pixel_format", "rgb24",
        "-vcodec", "ffv1",
    ])

    # ffmpeg_command.extend([
    #     "-pixel_format", "yuv444p",
    #     "-vcodec", "libx264",
    #     "-crf", "14",
    #     "-preset", "slow",
    #     "-tune", "stillimage"
    # ])

    # ffmpeg_command.extend([
    #     "-pix_fmt", "yuv444p",
    #     "-vcodec", "libx264",
    #     "-preset", "slow",
    #     "-crf", "10",
    #     "-tune", "stillimage"
    # ])

    ffmpeg_command.extend([
        "-an",
        "-sn",
        "-map_chapters", "-1"
    ])

    if qtgmc_args.keys():
        ffmpeg_command.extend([
            "-movflags",
            "use_metadata_tags"
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




def deint_command(
    in_video_info: VideoInfo,
    algo: str,
    params: str,
    out_filepath: str,
    trim_start: int = 0,
    trim_count: int = -1,
) -> list[str]:
    in_pix_fmt = in_video_info['pix_fmt']
    fps: float | int | tuple[int, int] = in_video_info['frame_rate_r']

    # Chroma interpolation
    chroma_interpolation: str = ""
    c_order = PIXEL_FORMAT[in_pix_fmt]['c_order']
    if (
        ('yuv' in c_order or 'gray' in c_order)
        and '444' not in in_pix_fmt
    ):
        chroma_interpolation = """
            scale=iw:ih
                :sws_flags=
                    lanczos
                    + full_chroma_int
                    + full_chroma_inp
                    + accurate_rnd
                    + bitexact
        """

    # Deinterlace algo/params
    ffmpeg_deint: str = ""
    if in_video_info['is_interlaced']:
        deint_algo: str = algo
        deint_params: str = params

        ffmpeg_deint: str = ""
        sep: str = '='
        if algo == 'nnedi':
            deint_algo = f"nnedi=weights={nnedi3_weights}"
            sep = ':'

        ffmpeg_deint = (
            f"{deint_algo}{sep}{deint_params}"
            if deint_algo and deint_params
            else deint_algo
        )
        if ffmpeg_deint:
            ffmpeg_deint = f"{ffmpeg_deint}"

    # Resize with SAR
    in_h, in_w = in_video_info['shape'][:2]
    if in_video_info['sar'][0] >= in_video_info['sar'][1]:
        in_w = int((in_w * float(in_video_info['sar'][0]) / in_video_info['sar'][1]) + 0.5)
    else:
        in_h = int((in_h * float(in_video_info['sar'][1]) / in_video_info['sar'][0]) + 0.5)

    resize = f"""
        scale={in_w}:{in_h}:sws_flags=
            bilinear
            + full_chroma_int
            + full_chroma_inp
            + accurate_rnd
            + bitexact
    """

    ## FFmpeg filter
    ffmpeg_filter = ','.join([
        s for s in (
            ffmpeg_deint,
            chroma_interpolation,
            resize,
        ) if len(s) != 0
    ])
    ffmpeg_filter = _clean_str(ffmpeg_filter)

    # Create the command
    ffmpeg_command: list[str] = [
        ffmpeg_exe,
        "-hide_banner",
        "-loglevel", "warning",
        "-stats",
    ]

    # Seek
    main_logger.debug(f"trim: start: {trim_start}, count: {trim_count}")
    if trim_count != -1 and trim_start + trim_count > in_video_info['frame_count']:
        raise ValueError(f"Erroneous trim value: {trim_start+trim_count} > {in_video_info['frame_count']}")

    if trim_start:
        ffmpeg_command.extend(["-ss", frame_to_sexagesimal(trim_start, fps)])

    if trim_count != -1:
        ffmpeg_command.extend(["-t", frame_to_sexagesimal(trim_count, fps)])

    # Input file
    ffmpeg_command.extend(["-i", in_video_info['filepath']])

    # Add filters
    if ffmpeg_filter:
        ffmpeg_command.extend([
            "-filter_complex", f"[0:v]{ffmpeg_filter}[outv]",
            "-map", "[outv]"
        ])

    # Frame rate
    ##### FORCE TO 25 fps
    fps = 25
    ffmpeg_command.extend([
        "-r",
        '/'.join(map(str, fps)) if isinstance(fps, tuple | list) else f"{fps}"
    ])

    ffmpeg_command.extend([
        "-pixel_format", "bgr24",
        "-vcodec", "ffv1",
    ])

    ffmpeg_command.extend([
        "-an",
        "-sn",
        "-map_chapters", "-1"
    ])

    if params != '':
        ffmpeg_command.extend([
            "-movflags", "use_metadata_tags",
            "-metadata:s:v:0", f"deint_algo={algo}",
            "-metadata:s:v:0", f"deint_params=\"{params}\""
        ])

    ffmpeg_command.extend([out_filepath, "-y"])
    pprint(ffmpeg_command)
    return ffmpeg_command
