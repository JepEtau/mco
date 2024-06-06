from dataclasses import dataclass
import logging
import signal
import subprocess
import sys

import pip
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


@dataclass
class PyPackage:
    pretty_name: str
    name: str
    version: str | None = None
    index_url: str = ""
    extra: str = ""

py_packages: list[PyPackage] = (
    PyPackage(
        pretty_name="PyTorch",
        name="torch",
        index_url="https://download.pytorch.org/whl/cu121"
    ),
    PyPackage(
        pretty_name="TorchVision",
        name="torchvision",
        index_url="https://download.pytorch.org/whl/cu121"
    ),
    PyPackage(
        pretty_name="SafeTensors",
        name="safetensors",
    ),
)


def main():
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.setLevel("WARNING")

    from importlib import metadata
    from pprint import pprint


    if False:
        py_packages: tuple[str] = (
            'safetensors',
            'torch',
            'torchvision',
            'onnx',
            'onnxruntime-directml',
            'onnxoptimizer',
            'onnxruntime',
        )
        versions: dict[str, str] = {}
        for package in py_packages:
            version = metadata.metadata(package).json['version']
            versions[package] = version
            print(metadata.metadata(package).json['name'])

    pp = 'torch'
    # "python -m pip install --upgrade pip"
    try:
        subprocess.run(["python", "-m", "pip", "uninstall", "-y", pp])
    except:
        pass
    import pip


    # index_url = "https://download.pytorch.org/whl/cu121"
    # finder = pip.PackageFinder(
    #     find_links=[],
    #     index_urls=[index_url],
    #     use_wheel=True,
    #     allow_all_prereleases=True,
    #     process_dependency_links=True)

    # url = finder.find_requirement(req, True)
    # pprint(finder)



    sub_process = subprocess.Popen(
        ["python", "-m", "pip", "install",
         "--dry-run",
         "--no-cache-dir", pp,
        "--index-url", "https://download.pytorch.org/whl/cu121",
         "--upgrade",
         "--progress-bar=off",
         "-vv",
           ],
        #    "--progress-bar=off"
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    print("start")
    while True:
        # data = sub_process.stdout.read(1).decode('utf-8')
        data = sub_process.stdout.readline()
        if sub_process.poll() is not None:
            break

        # if not line:
        #     continue

        print(data)
    # pprint(metadata.metadata('torch').json)

    # PyPackage(
    #     name="PyTorch",
    #     distribution="torch",
    #     index_url="https://download.pytorch.org/whl/nightly/cpu",
    #     version="2.2.0",
    #     strict=False,
    # ),


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
