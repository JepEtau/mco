import os
import sys
from .path_utils import absolute_path


external_dir = "external"
ffmpeg_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    os.pardir,
    external_dir,
    "ffmpeg"
)

if sys.platform == "win32":
    ffmpeg_exe = os.path.join(ffmpeg_path, "ffmpeg.exe")
    ffprobe_exe = os.path.join(ffmpeg_path, "ffprobe.exe")
    python_exe = "python.exe"

elif sys.platform == "linux":
    ffmpeg_exe = os.path.join(ffmpeg_path, "ffmpeg")
    ffprobe_exe = os.path.join(ffmpeg_path, "ffprobe")
    python_exe = "python"

else:
    sys.exit("[E] Platform/system not supported.")

ffprobe_exe = absolute_path(ffprobe_exe)
ffmpeg_exe = absolute_path(ffmpeg_exe)

nnedi3_weights = f"{ffmpeg_path}/nnedi3_weights.bin"
