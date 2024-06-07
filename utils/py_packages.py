
from dataclasses import dataclass
from importlib import metadata
import re
import requests
import subprocess
import time
from urllib.parse import unquote
from .logger import logger
from .p_print import *


@dataclass
class PyPackage:
    pretty_name: str
    name: str
    version: str = ""
    index_url: str = ""
    extra: str = ""
    wheel: str = ""
    url: str = ""
    size: int = 0
    supported: bool = True
    installed: bool = False
    installed_version: str = ""
    uninstall_before: bool = False



def update_pip() -> bool:
    pip_command: str = "python -m pip install --upgrade pip"
    try:
        subprocess.run(
            pip_command.split(' '),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=20,
            check=True
        )
    except:
        return False
    return True



def update_package_info(package: PyPackage, retry: int = 3) -> None:
    installed_version: str = ""
    try:
        installed_version = metadata.metadata(package.name).json['version']
        logger.info(f"[I] {package.pretty_name}: {installed_version}")
        package.installed_version = installed_version
    except:
        logger.info(f"[I] Package {package.pretty_name} is not installed")



def update_package_url(package: PyPackage, retry: int = 3) -> bool:
    timeout: float = 5
    _retry: int = retry
    if package.index_url:
        regex: re.Pattern = re.compile(rf".*Downloading\s*(https:\/\/.*\/.*\.whl)")
    else:
        regex: re.Pattern = re.compile(rf".*{package.name}.*(https:\/\/.*\/.*\.whl)\.metadata")

    already_installed_regex = re.compile(rf".*Requirement\s*already\s*satisfied:\s*{package.name}")
    url: str = ""

    start_time: float = time.time()
    index_url: list[str] = ["--index-url", package.index_url] if package.index_url else []
    version = f"=={package.version}" if package.version != '' else ''
    pip_command: list[str] = [
        "python",
        "-m", "pip", "download",
        "--no-deps",
        "--no-cache-dir",
        "--upgrade" if version != '' else '',
        f"{package.name}{version}",
        *index_url,
        "--progress-bar=off",
        "-v"
    ]
    pip_command = list([x for x in pip_command if x != '' and x is not None])
    # print(' '.join(pip_command))
    while _retry > 0 and url == '' and not package.installed and package.supported:
        sub_process = subprocess.Popen(
            pip_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )

        start_time = time.time()
        while (
            (time.time() - start_time) < timeout + (retry - _retry) * 5
            and sub_process.poll() is None
        ):
            try:
                line = sub_process.stdout.readline().decode('utf-8').strip()
            except:
                break
            if _retry < retry:
                print(line)

            if (result := re.search(regex, line)):
                sub_process.terminate()
                url = result.group(1)
                break

            if (result := re.search(already_installed_regex, line)):
                sub_process.terminate()
                package.installed = True
                break

            if "No matching distribution found" in line:
                sub_process.terminate()
                package.supported = False
                logger.warning(f"[W] {package.pretty_name} is not supported on this platform")
                break

        if url == '' or package.installed:
            if sub_process.poll() is None:
                sub_process.terminate()
            while sub_process.poll() is None and (time.time() - start_time) > 2:
                time.sleep(0.5)

            if not package.installed and package.supported:
                _retry -= 1
                timeout += (retry - _retry) * 5
                logger.warning(f"retry: {_retry}, new timeout: timeout")

    package.url = url
    if package.url == '' and not package.installed and package.supported:
        logger.error(red(f"[E] Failed  to fetch url for {package.name}"))

    elif package.installed:
        logger.info(f"[I] {package.pretty_name} already installed")

    elif package.url != '':
        package.wheel = unquote(package.url.split('/')[-1])
        package.version = unquote(package.wheel.split('-')[1])
        response: requests.Response
        try:
            response = requests.get(package.url, stream=True)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            if str(e).startswith('404'):
                logger.error(f"File {package.url} not found")
            return False
        package.size=int(response.headers.get('Content-length', 0))

    return True
