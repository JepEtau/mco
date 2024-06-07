import logging
from pprint import pprint
import signal
import sys

from utils.external_packages import (
    ExternalPackage,
    install_external_packages
)
from utils.p_print import *
from utils.logger import logger
from utils.py_packages import (
    PyPackage,
    update_package_info,
    update_package_url,
    update_pip,
)


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



py_packages: list[PyPackage] = (
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
        pretty_name="ONNX Runtime",
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
        pretty_name="ONNX Runtime DirectML",
        name="onnxoptimizer",
    ),
)



def main():
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.setLevel("WARNING")


    success: bool = update_pip()
    if success:
        logger.info("[I] pip is up-to-date")
    else:
        logger.warning("[W] Failed updating pip")


    for package in py_packages:
        update_package_info(package)
        update_package_url(package)
        logger.info(f"[I] {package.pretty_name}: {package.url}")
        pprint(package)



    sys.exit()

    installed: bool = install_external_packages(
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
