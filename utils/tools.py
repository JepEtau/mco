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

if sys.platform == "win32":
    ffmpeg_exe = os.path.join(external_dir, "ffmpeg", "ffmpeg.exe")
    ffprobe_exe = os.path.join(external_dir, "ffmpeg", "ffprobe.exe")
    python_exe = "python.exe"
    ffprobe_exe = absolute_path(ffprobe_exe)
    ffmpeg_exe = absolute_path(ffmpeg_exe)

elif sys.platform == "linux":
    ffmpeg_exe = os.path.join(external_dir, "ffmpeg", "ffmpeg")
    ffprobe_exe = os.path.join(external_dir, "ffmpeg", "ffprobe")
    python_exe = "python"

    ffprobe_exe = absolute_path(ffprobe_exe)
    ffmpeg_exe = absolute_path(ffmpeg_exe)
    for f in [ffmpeg_exe, ffprobe_exe]:
        st_mode = os.stat(f).st_mode
        if oct(st_mode & 0o100) == "0o0":
            os.chmod(f, st_mode |S_IEXEC)

else:
    sys.exit("[E] Platform/system not supported.")

nnedi3_weights = absolute_path(f"{external_dir}/nnedi3_weights.bin")
