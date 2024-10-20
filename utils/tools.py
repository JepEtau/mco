import os
import sys
from .path_utils import absolute_path
from stat import S_IEXEC

external_dir: str = absolute_path(
        os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        os.pardir,
        "external",
    )
)

if not os.path.exists(external_dir):
    os.makedirs(external_dir, exist_ok=True)
if not os.path.exists(os.path.join(external_dir, "ffmpeg")):
    os.makedirs(os.path.join(external_dir, "ffmpeg"), exist_ok=True)

if sys.platform == "win32":
    ffmpeg_exe = os.path.join(external_dir, "ffmpeg", "ffmpeg.exe")
    ffprobe_exe = os.path.join(external_dir, "ffmpeg", "ffprobe.exe")
    python_exe = "python.exe"
    ffprobe_exe = absolute_path(ffprobe_exe)
    ffmpeg_exe = absolute_path(ffmpeg_exe)
    mkvmerge_exe = r"C:\Program Files\MKVToolNix\mkvmerge.exe"
    ml_model_dir = r"A:\ml_models"

elif sys.platform == "linux":
    ffmpeg_exe = os.path.join(external_dir, "ffmpeg", "ffmpeg")
    ffprobe_exe = os.path.join(external_dir, "ffmpeg", "ffprobe")
    python_exe = "python"

    ffprobe_exe = absolute_path(ffprobe_exe)
    ffmpeg_exe = absolute_path(ffmpeg_exe)
    try:
        for f in [ffmpeg_exe, ffprobe_exe]:
            st_mode = os.stat(f).st_mode
            if oct(st_mode & 0o100) == "0o0":
                os.chmod(f, st_mode |S_IEXEC)
    except:
        pass

    mkvmerge_exe = "mkvmerge"
    ml_model_dir = "~/ml_models"

else:
    sys.exit("[E] Platform/system not supported.")

nnedi3_weights: str = "external/nnedi3/nnedi3_weights.bin"
font_dir: str = os.path.join(external_dir, "fonts")

avs_dir = os.path.join(external_dir, "avs")

ml_model_dir = absolute_path(ml_model_dir)
