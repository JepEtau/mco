from enum import Enum
import os
import numpy as np
from PIL import (
    Image as PilImage,
    ImageDraw,
    ImageFont,
)

from scene.src_scene import SrcScene, SrcScenes
from utils.images import Image
from utils.images_io import load_image, write_image
from utils.mco_types import Scene, McoFrame
from utils.tools import font_dir
from parsers import db


_FONT_PATH: tuple[tuple[str]] = (
    ("Roboto/Roboto-Regular.ttf", "Roboto/Roboto-Italic.ttf"),
    ("Roboto/Roboto-Bold.ttf", "Roboto/Roboto-BoldItalic.ttf")
)


class WatermarkAlignment(Enum):
    LEFT = "left"
    CENTERED = "center"
    RIGHT = "right"



def add_watermark(frame: McoFrame | np.ndarray, no: int) -> np.ndarray | None:
    """Add edition, episode, scene no, frame no
    no is the frame no.
    """

    scene: Scene = frame.scene
    in_img: np.ndarray = frame.img

    if scene['task'].name == 'initial':
        text: str = f"""{scene['k_ed']}:{scene['k_ep']}:{scene['no']:03}{str(no).rjust(10)}"""
    else:
        src_scene: Scene = scene['src'].get_src_scene_from_frame_no(no)['scene']
        text: str = f"""{src_scene['k_ed']}:{src_scene['k_ep']}:{src_scene['no']:03}{str(no).rjust(10)}"""

    height: int = in_img.shape[0]
    font_size: int = 20
    bold: bool = False
    italic: bool = False
    alignment: WatermarkAlignment = WatermarkAlignment.LEFT
    color: tuple[int, int, int] = (0, 240, 0)

    font_path = os.path.join(font_dir, _FONT_PATH[int(bold)][int(italic)])

    lines = text.split("\n")
    line_count, max_line = len(lines), max(lines, key=len)

    # Use a text as reference to get max size
    font = ImageFont.truetype(font_path, size=font_size)

    # bounding box (in pixels): left, top, right, bottom
    bounding_box: tuple[int, int, int, int] = font.getbbox(text)
    h_text = bounding_box[3] - bounding_box[1]
    position_w = 50
    position_h: int = height - h_text - 5

    # Text color
    ink = color

    # Create a PIL image to add text
    pil_image = PilImage.fromarray(in_img)
    ImageDraw.Draw(pil_image).text(
        (position_w, position_h),
        text,
        font=font,
        anchor="ls",
        align=alignment.value,
        fill=ink,
    )
    if scene['task'].name in ('initial', 'lr'):
        _add_initial_scene_watermak(pil_image=pil_image, scene=scene, no=no)
    out_img: np.ndarray = np.array(pil_image)

    # Debug
    # print(f"img: {img.shape}, {img.dtype}. Htext={h_text}px position: (50, {position_h})")
    # write_image(frame.out_fp, out_img)

    return out_img



def _add_initial_scene_watermak(pil_image: PilImage.Image, scene: Scene, no: int) -> None:

    height: int = pil_image.height

    if scene['task'].name == 'initial':
        text: str = f"{scene['k_ed']}:{scene['k_ep']}:{scene['no']:03} {scene['count']}"
        color: tuple[int, int, int] = (0, 240, 0)
    else:
        src_scene: Scene = scene['src'].get_src_scene_from_frame_no(no)['scene']
        text: str = f"{src_scene['k_ed']}:{src_scene['k_ep']}:{src_scene['no']:03} {src_scene['count']}"
        color: tuple[int, int, int] = (255, 240, 0)

    font_size: int = 70
    bold: bool = True
    italic: bool = False
    alignment: WatermarkAlignment = WatermarkAlignment.LEFT


    font_path = os.path.join(font_dir, _FONT_PATH[int(bold)][int(italic)])

    lines = text.split("\n")
    line_count, max_line = len(lines), max(lines, key=len)

    # Use a text as reference to get max size
    font = ImageFont.truetype(font_path, size=font_size)

    # bounding box (in pixels): left, top, right, bottom
    bounding_box: tuple[int, int, int, int] = font.getbbox(text)
    h_text = bounding_box[3] - bounding_box[1]
    if scene['task'].name == 'lr':
        position_h: int = (height - h_text) // 2
    else:
        position_h: int = height - h_text - 5

    # Text color
    ink = color

    position_w = 100
    position_h: int = (height - h_text) // 2

    ImageDraw.Draw(pil_image).text(
        (position_w, position_h),
        text,
        font=font,
        anchor="ls",
        align=alignment.value,
        fill=ink,
    )
