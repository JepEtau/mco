import math
import cv2
import numpy as np
from parsers import (
    DsrPatch,
)
from utils.mco_types import Scene
from utils.p_print import red


def generate_dsr_mask(
    scene: Scene,
    frame_no: int,
    shape: list[int, int] | tuple[int, int]
) -> np.ndarray | None:
    if scene['dsr'] is None:
        return None

    mask_img: np.ndarray | None = None
    patches: list[DsrPatch] = scene['dsr'].get(frame_no=frame_no)

    if patches is not None:
        h, w = shape[2:] if len(shape) == 4 else shape[:2]
        mask_img: np.ndarray = np.zeros((h, w), dtype=np.uint8)
        patch: DsrPatch
        for patch in patches:
            # print(region)
            # print(f"dsr shape: ({h}, {w})")
            patch: DsrPatch = patch.get(size=(w, h))
            # print(region)
            if patch.shape == 'circle':
                mask_img = cv2.circle(
                    img=mask_img,
                    center=patch.center,
                    radius=patch.axes[1],
                    color=255,
                    thickness=-1
                )

            elif patch.shape == 'ellipse':
                mask_img = cv2.ellipse(
                    img=mask_img,
                    center=patch.center,
                    axes=patch.axes,
                    angle=patch.angle,
                    startAngle=0,
                    endAngle=360,
                    color=255,
                    thickness=-1
                )

            elif patch.shape == 'line':
                length, angle = patch.axes[0], math.radians(patch.angle)
                dx = math.cos(angle) * length / 2
                dy = math.sin(angle) * length / 2
                # QGraphicsItem: "Assigning a negative value will rotate the item counter-clockwise.""
                x, y = patch.center
                if angle > 0:
                    x1, y1 = x - dx, y - dy
                    x2, y2 = x + dx, y + dy
                else:
                    x1, y1 = x + dx, y + dy
                    x2, y2 = x - dx, y - dy
                mask_img = cv2.line(
                    img=mask_img,
                    pt1=(x1, y1),
                    pt2=(x2, y2),
                    thickness=patch.axes[1],
                    color=255,
                )

            else:
                print(red(f"Unsupported mask shape: {patch.shape}"))

    return mask_img
