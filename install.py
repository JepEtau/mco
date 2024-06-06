from dataclasses import dataclass
import logging
import os
import requests
import shutil
import signal
import sys
from tqdm import tqdm

from utils.p_print import *
from utils.path_utils import get_app_tempdir, get_extension
from utils.tools import external_dir
from utils.time_conversions import reformat_datetime


@dataclass
class ExternalPackage:
    name: str
    dirname: str
    filename: str
    size: int = 0
    response: requests.Response | None = None
    last_modified: str = ''
    downloaded: bool = False
    installed: bool = False
    tmp_file: str = ''
    skip: bool = False

    def __post_init__(self):
        self.skip = bool(self.filename == '')



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
            filename="nnedi3_weights.bin"
        )
    )
    return packages



def download_package(package: ExternalPackage, retry: int = 3) -> bool:
    tmp_dir: str = os.path.dirname(package.tmp_file)
    os.makedirs(tmp_dir, exist_ok=True)

    _retry: int = retry
    while _retry:
        logger.info(f"Downloading: {package.name} to {tmp_dir}")
        progress_bar: tqdm = tqdm(
            total=package.size,
            unit="iB",
            unit_scale=True,
            colour="white"
        )

        with open(package.tmp_file, "wb") as f:
            try:
                for data in package.response.iter_content(chunk_size=1024):
                    progress_bar.update(len(data))
                    f.write(data)
            except Exception as e:
                logger.info("[W] Retry download, error: type(e)")
                _retry -= 1
                continue

        if _retry == 0:
            logger.info(f"[E] failed downloading {package.filename}")
            return False

        _retry = 0

    progress_bar.close()
    open(
        os.path.join(tmp_dir, package.last_modified), 'w'
    ).close()
    return  True


def install_external_packages(retry: int = 3) -> bool:
    rehost_url_base = "https://github.com/JepEtau/external_rehost/releases/download/external"
    temp_dir: str = get_app_tempdir()
    packages: tuple[ExternalPackage] = external_packages()

    # Create a dict of packages to download/install
    for package in packages:
        if package.skip:
            continue
        logger.info(f"Package: {package.name}")

        # Get info from host and update package info
        url: str = f"{rehost_url_base}/{package.filename}"
        response: requests.Response
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(e)
            return False
        last_modified: str = reformat_datetime(response.headers['Last-Modified'])
        package.size=int(response.headers.get('Content-length', 0))
        package.response=response
        package.last_modified=last_modified
        package.tmp_file=os.path.join(temp_dir, package.dirname, package.filename)

        # Check if installed
        install_dir: str = os.path.join(external_dir, package.dirname)
        if os.path.exists(os.path.join(install_dir, last_modified)):
            package.installed = True
            logger.info(lightgrey(f"  already installed"))
            try:
                shutil.rmtree(os.path.dirname(package.tmp_file))
            except:
                pass
            continue

        # Download package
        if (
            os.path.exists(os.path.join(temp_dir, package.dirname, last_modified))
            and os.path.exists(package.tmp_file)
            and os.path.getsize(package.tmp_file) == package.size
        ):
            package.downloaded = True
            logger.info(lightgrey(f"  already downloaded"))
        else:
            package.downloaded = download_package(package, retry)

        # Install package
        logger.info(lightgrey(f"  install"))

        extension: str = get_extension(package.tmp_file)
        if os.path.exists(install_dir):
            shutil.rmtree(install_dir)
        if extension == '.zip':
            import zipfile
            with zipfile.ZipFile(package.tmp_file, "r") as f:
                f.extractall(install_dir)

        else:
            if os.path.exists(install_dir):
                shutil.rmtree(install_dir)
            os.makedirs(install_dir)
            shutil.move(package.tmp_file, install_dir)

        package.installed = True
        open(os.path.join(install_dir, package.last_modified), 'w').close()
        try:
            shutil.rmtree(os.path.dirname(package.tmp_file))
        except:
            pass
        logger.info(lightgrey(f"  {package.name} installed"))

    for package in packages:
        if not package.skip and not package.installed:
            return False

    return True


logger: logging.Logger = logging.getLogger("logger_install")

def main():
    logger: logging.Logger = logging.getLogger("logger_install")
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.setLevel("WARNING")

    installed: bool = install_external_packages()
    if installed:
        print(lightgreen("All packages installed"))
    else:
        print(red("Error: missing package(s)"))


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
