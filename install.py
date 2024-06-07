import logging
from pprint import pprint
import signal
import sys

from utils.ext_packages import (
    ExtPackage,
    install_ext_packages
)
from utils.p_print import *
from utils.logger import logger
from utils.py_packages import (
    PyPackage,
    install_py_packages,
    update_package_info,
    update_package_url,
    update_pip,
)


def external_packages() -> tuple[ExtPackage]:
    packages: tuple[ExtPackage] = (
        ExtPackage(
            name="FFmpeg",
            dirname='ffmpeg',
            filename=(
                "ffmpeg_win32_x64.zip"
                if sys.platform == "win32"
                else "ffmpeg_linux_amd64.zip"
            )
        ),
        ExtPackage(
            name="AviSynth+ plugins",
            dirname="avs",
            filename=(
                "avs.zip"
                if sys.platform == "win32"
                else ""
            )
        ),
        ExtPackage(
            name="NNedi3",
            dirname="nnedi3",
            filename="nnedi3.zip"
        )
    )
    return packages



py_packages: tuple[PyPackage] = (
    PyPackage(
        pretty_name="PyTorch",
        name="torch",
        index_url="https://download.pytorch.org/whl/cu121",
        uninstall_before=True,
    ),
    PyPackage(
        pretty_name="TorchVision",
        name="torchvision",
        index_url="https://download.pytorch.org/whl/cu121",
        uninstall_before=True,
    ),
    PyPackage(
        pretty_name="NumPy",
        name="numpy",
    ),
    PyPackage(
        pretty_name="SafeTensors",
        name="safetensors",
    ),
    PyPackage(
        pretty_name="ONNX",
        name="onnx",
    ),
    PyPackage(
        pretty_name="ONNX Runtime",
        name="onnxruntime",
    ),
    PyPackage(
        pretty_name="ONNX Runtime DirectML",
        name="onnxruntime-directml",
    ),
    PyPackage(
        pretty_name="ONNX Optimizer",
        name="onnxoptimizer",
    ),
)



def main():
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.setLevel("INFO")


    success: bool = update_pip()
    if success:
        logger.info("[I] pip is up-to-date")
    else:
        logger.warning("[W] Failed updating pip")


    install_py_packages(py_packages)


    sys.exit()

    installed: bool = install_ext_packages(
        external_packages(),
        rehost_url_base="https://github.com/JepEtau/external_rehost/releases/download/external",
        threads=2,
    )
    if installed:
        print(lightgreen("All packages installed"))
    else:
        print(red("Error: missing package(s)"))


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
