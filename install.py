import logging
import signal
import sys
from utils.external_packages import (
    ExternalPackage,
    install_external_packages
)
from utils.p_print import *
from utils.logger import logger


def external_packages() -> tuple[ExternalPackage]:
    packages: tuple[ExternalPackage] = (
        ExternalPackage(
            name="FFmpeg",
            dirname='ffmpeg',
            filename=(
                "ffmpeg_win32_x64.zip"
                if sys.platform == "win32"
                else "ffmpeg_linux_amd64.zip"
            )
        ),
        ExternalPackage(
            name="AviSynth+ plugins",
            dirname="avs",
            filename=(
                "avs.zip"
                if sys.platform == "win32"
                else ""
            )
        ),
        ExternalPackage(
            name="NNedi3",
            dirname="nnedi3",
            filename="nnedi3.zip"
        )
    )
    return packages



def main():
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.setLevel("WARNING")

    installed: bool = install_external_packages(external_packages())
    if installed:
        print(lightgreen("All packages installed"))
    else:
        print(red("Error: missing package(s)"))


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
