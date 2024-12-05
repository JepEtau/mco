import cv2
import numpy as np
from parsers import (
    DsrRegion,
)
from utils.mco_types import Scene


def get_mask(
    scene: Scene,
    frame_no: int,
    shape: list[int, int] | tuple[int, int]
) -> np.ndarray | None:
    if scene['dsr'] is None:
        return None

    mask_img: np.ndarray | None = None
    regions: list[DsrRegion] = scene['dsr'].get(frame_no=frame_no)
    if regions is not None:
        h, w = shape[:2]
        mask_img = np.ndarray = np.zeros((h, w), dtype=np.uint8)
        region: DsrRegion
        for region in regions:
            if region.shape == 'circle':
                mask_img = cv2.circle(
                    img=mask_img,
                    center=region.center,
                    radius=region.axes[1],
                    color=255,
                    thickness=-1
                )

            elif region.shape == 'ellipse':
                mask_img = cv2.ellipse(
                    img=mask_img,
                    center=region.center,
                    axes=region.axes,
                    angle=region.angle,
                    startAngle=0,
                    endAngle=360,
                    color=255,
                    thickness=-1
                )

            else:
                raise NotImplementedError(f"Unsupported mask shape: {region.shape}")

    return mask_img



# elif False:
#     # no rotate
#     pil_image = PilImage.fromarray(img.reshape(in_shape))
#     pil_mask = ImageDraw.Draw(pil_image)
#     for region in regions:
#         region: DsrRegion
#         x0, y0 = region.center - region.axes // 2
#         x1, y1 = x0 + region.axes[0], y0 + region.axes[1]
#         pil_mask.ellipse(
#             xy=((x0, y0), (x1, y1)),
#             outline="green"
#         )
#         pil_image = pil_image.rotate(region.angle, expand=True)
#         break
#     # pil_image = pil_image.rotate(30, expand=True)

#     out_img: np.ndarray = np.array(pil_image)
#     img = np.ascontiguousarray(out_img)
# else:
#     # worse than cv2
#     region: DsrRegion = regions[0]
#     pil_mask = PilImage.new(
#         'F', list(region.axes + 10), color=0.
#     )
#     x0, y0 = 0,0
#     x1, y1 = x0 + region.axes[0], y0 + region.axes[1]
#     ImageDraw.Draw(pil_mask).ellipse(
#         xy=((x0, y0), (x1, y1)),
#         outline="white",
#         fill="white"
#     )
#     pil_mask = pil_mask.rotate(
#         region.angle,
#         # resample=PilImage.Resampling.BILINEAR,
#         expand=True
#     )
#     np_mask: np.ndarray = np.array(pil_mask, dtype=np.float32)

#     write_image(f"mask_{in_f_no:04}_pil.png", np_mask)
