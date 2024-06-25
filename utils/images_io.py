from concurrent.futures import ThreadPoolExecutor
import glob
import multiprocessing
import os
from pathlib import Path
from pprint import pprint
import cv2
import numpy as np

from .np_dtypes import np_to_float32
from .path_utils import absolute_path
CPU_COUNT: int = multiprocessing.cpu_count()


def load_image(filepath: Path | str) -> np.ndarray:
    return cv2.imdecode(
        np.fromfile(filepath, dtype=np.uint8),
        cv2.IMREAD_UNCHANGED
    )


def load_image_fp32(filepath: Path | str) -> np.ndarray:
    return np_to_float32(
        cv2.imdecode(
            np.fromfile(filepath, dtype=np.uint8),
            cv2.IMREAD_UNCHANGED
        )
    )


def write_image(filepath: Path | str, img: np.ndarray) -> None:
    extension = os.path.splitext(filepath)[1]
    # try:
    #     _, img_buffer = cv2.imencode(f".{extension}", img)
    #     with open(filepath, "wb") as buffered_writer:
    #         buffered_writer.write(img_buffer)
    # except Exception as e:
    #     raise RuntimeError(f"Failed to save image as {filepath}, reason: {type(e)}")
    _, img_buffer = cv2.imencode(f".{extension}", img)
    with open(filepath, "wb") as buffered_writer:
        buffered_writer.write(img_buffer)


def load_images(
    filepaths: list[Path | str],
    cpu_count: int = 4,
) -> list[np.ndarray]:
    imgs: list[np.ndarray] = []
    with ThreadPoolExecutor(max_workers=min(CPU_COUNT, cpu_count)) as executor:
        for img in executor.map(load_image_fp32, filepaths):
            imgs.append(img)
    return imgs



def write_images(
    filepaths: list[str],
    images: tuple[np.ndarray],
    cpu_count: int = 4,
) -> None:
    with ThreadPoolExecutor(max_workers=min(CPU_COUNT, cpu_count)) as executor:
        executor.map(write_image, filepaths, images)


def get_image_list(directory: str | Path, extension: str = '.png') -> list[str]:
    directory = os.path.normpath(
        os.path.realpath(absolute_path(str(directory)))
    )
    # fastest for simple filtering
    return [
        os.path.join(directory, f)
        for f in sorted(os.listdir(directory)) if f.endswith(extension)
    ]

    # +50%
    files: list[str] = glob.glob(
        f"*{extension}",
        root_dir=directory,
        dir_fd=None,
        recursive=False,
        include_hidden=False
    )
    return [os.path.join(directory, f) for f in sorted(files)]
