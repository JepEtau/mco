from enum import Enum
import os
import numpy as np
from PIL import (
    Image as PilImage,
    ImageDraw,
    ImageFont,
)

from utils.images import Image
from utils.images_io import load_image
from utils.mco_types import Scene
from utils.tools import font_dir



_FONT_PATH: tuple[tuple[str]] = (
    ("Roboto/Roboto-Regular.ttf", "Roboto/Roboto-Italic.ttf"),
    ("Roboto/Roboto-Bold.ttf", "Roboto/Roboto-BoldItalic.ttf")
)


class WatermarkAlignment(Enum):
    LEFT = "left"
    CENTERED = "center"
    RIGHT = "right"



def get_font_size(font: ImageFont.FreeTypeFont, text: str) -> tuple[int, int]:
    # bounding box (in pixels): left, top, right, bottom
    bounding_box: tuple[int, int, int, int] = font.getbbox(text)
    return bounding_box[2] - bounding_box[0], bounding_box[3] - bounding_box[1]


def add_watermark(image: Image, scene: Scene) -> None:
    # Load and save image with dtype=uint8
    in_img: np.ndarray = load_image(image.in_fp)
    height, width = in_img.shape[:2]

    text: str = f"""{scene['src']['k_ed']}:{scene['src']['k_ep']}    {image.no}"""
    bold: bool = True
    italic: bool = False
    alignment: WatermarkAlignment = WatermarkAlignment.LEFT
    color: tuple[int, int, int] = (0, 240, 0)

    font_path = os.path.join(font_dir, _FONT_PATH[int(bold)][int(italic)])

    lines = text.split("\n")
    line_count, max_line = len(lines), max(lines, key=len)

    # Use a text as reference to get max size
    font = ImageFont.truetype(font_path, size=100)
    w_ref, h_ref = get_font_size(max_line)[0], get_font_size("[§]")[1]

    # Calculate font size to fill the specified image size
    w = int(width * 100.0 / w_ref)
    h = int(height * 100.0 / (h_ref * line_count))
    font_size = min(w, h)
    font = ImageFont.truetype(font_path, size=font_size)
    w_text, h_text = get_font_size(max_line)

    position_h: int = height - h_text - 20

    # Text color
    ink = color

    # Create a PIL image to add text
    pil_image = PilImage.fromarray(in_img)
    ImageDraw.Draw(pil_image).text(
        (50, position_h),
        text,
        font=font,
        anchor="mm",
        align=alignment.value,
        fill=ink,
    )

    img = np.array(pil_image)


