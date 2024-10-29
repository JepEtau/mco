


from copy import copy, deepcopy
import cv2
import numpy as np

from processing.detect_inner_rect import np_to_uint8
from utils.p_print import *

from parsers import (
    StabilizeSegment,
    StabilizeMode,
)


def apply_transformation(img: np.ndarray, x_y_theta: tuple[float]) -> np.ndarray:
    if x_y_theta == (0, 0, 0):
        return img
    t_x, t_y, t_theta = x_y_theta
    transformation_matrix = np.array(
        [
            [np.cos(t_theta), -np.sin(t_theta), t_x],
            [np.sin(t_theta), np.cos(t_theta), t_y]
        ],
        dtype=np.float32
    )
    h, w  = img.shape[:2]
    return cv2.warpAffine(img, transformation_matrix, (w, h))



def create_mask(
    shape: tuple[int, int],
    inside: bool,
    regions: list[np.ndarray],
    coord_factor: float = 1,
) -> np.ndarray:
    h, w = shape
    mask = np.empty((h, w, 1), dtype=np.float32)
    mask.fill(int(not inside))
    # TODO use percentages
    for region in regions:
        points = np.array(region, dtype=np.float32).reshape((-1, 1, 2))
        points *= coord_factor
        cv2.fillPoly(mask, [points.astype(int)], int(inside))

    # cv2.imwrite("mask.png", img_mask)
    return mask



def _stretch_intensity(
    img: np.ndarray,
    clip_hist_percent: int = 25
) -> np.ndarray:

    # Calculate grayscale histogram, simplified to 256 gradation
    hist = cv2.calcHist([img],[0],None,[256],[0,255])
    hist_size = len(hist)

    # Calculate cumulative distribution from the histogram
    accumulator: list[np.float32] = [hist[0]]
    for index in range(1, hist_size):
        accumulator.append(accumulator[index -1] + hist[index])

    # Locate points to clip
    maximum = accumulator[-1]
    clip_hist_percent *= maximum / 100.0
    clip_hist_percent /= 2.0

    # Locate left cut
    minimum_gray = 0
    while accumulator[minimum_gray] < clip_hist_percent:
        minimum_gray += 1

    # Locate right cut
    maximum_gray = hist_size -1
    while accumulator[maximum_gray] >= (maximum - clip_hist_percent):
        maximum_gray -= 1

    # Calculate alpha and beta values
    alpha = 1 / (maximum_gray - minimum_gray)
    beta = - minimum_gray * alpha

    return cv2.convertScaleAbs(img, alpha=alpha, beta=beta)



def _enhance_img(img: np.ndarray, method: str = 'none') -> np.ndarray:
    # Modify a gray image to improve keypoints detection
    # dtype must be uint8 for deshake

    if method == 'auto':
        img = _stretch_intensity(np_to_uint8(img))

    elif method == 'contrast':
        # Increase contrast
        img = cv2.convertScaleAbs(img, alpha=1.3, beta=0)
        img = cv2.normalize(img, img, 0, 1, cv2.NORM_MINMAX)
        img = np_to_uint8(img)

    return img





class SegmentStabilizer:
    def __init__(
        self,
        borders: int,
        max_corners: int = 300,
        quality_level: float = 0.01,
        min_distance: int = 30,
        block_size: int = 3,
        use_harris_detector: bool = True,
        k = 0.04,
    ) -> None:
        # Borders is padding which were already added to each image
        # so that deshaked image won't be shifted outside of this image
        self.borders: int = borders
        self.segment: StabilizeSegment = None
        self.tracker_mask: np.ndarray | None = None

        # self.shape: tuple[int, int, int] = (0, 0, 0)
        self.descriptor = None

        # Use previous transformation when failing in finding keypoints
        # or optical flow between 2 images
        self.prev_transformation: tuple[float] = (0., 0., 0.)

        # Create a dict which will be passed to cv2.goodFeaturesToTrack
        self.gftt: dict[str, int | float | bool] = dict(
            maxCorners=max_corners,
            qualityLevel=quality_level,
            minDistance=min_distance,
            blockSize=block_size,
            useHarrisDetector=use_harris_detector,
            k=k
        )
        self.lk_params: dict = {}


    def detect_keypoints(self,
        img: np.ndarray,
        inner_rect: tuple[int, int, int, int] | None
    ) -> tuple[np.ndarray, np.ndarray]:
        """Returns:
            - an enhanced image to be used for optical flow
            - a list of keypoints detected on this img
        """
        keypoints: np.ndarray
        mask: np.ndarray = None
        gray_img = cv2.cvtColor(np_to_uint8(img), cv2.COLOR_BGR2GRAY)
        enhanced = _enhance_img(gray_img)

        if inner_rect is not None:
            # is cv2 more performant than numpy?
            h, w = gray_img.shape[:2]
            mask = np.zeros((h, w, 1), dtype=int)
            x0, y0, w, h = inner_rect
            mask[y0:y0+h, x0:x0+w] = np.ones((h, w, 1), dtype=np.uint8)
            if self.segment.tracker.enable:
                mask *= self.tracker_mask

        elif self.segment.tracker.enable:
            mask = self.tracker_mask

        if self.descriptor is None:
            self.gftt['mask'] = mask
            keypoints = cv2.goodFeaturesToTrack(enhanced, **self.gftt)
        else:
            if mask is not None:
                enhanced *= mask
            kpts, _ = self.descriptor.detectAndCompute(enhanced, None)
            keypoints = np.array([kp.pt for kp in kpts], dtype=np.float32).reshape(-1, 1, 2)

        return enhanced, keypoints


    def stabilize_initial_img(
        self,
        img: np.ndarray,
        initial_transformation: tuple[float] | None,
        inner_rect: tuple[int, int, int, int] | None
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Apply transformation to the initial image of the segment
            and returns:
            - the stabilized image
            - the image which will be used for tracking
            - keypoints of this image
        """
        if initial_transformation is not None:
            print(lightgreen(f"\t\t\tapply last transformation to the initial img:"),
                  ', '.join([f"{t:.02f}" for t in initial_transformation]))
            img = apply_transformation(img, initial_transformation)
            self.prev_transformation = initial_transformation
        else:
            print(lightgreen("\tNo transformation applied to the initial image:"))
            self.prev_transformation = (0, 0, 0)

        img_for_tracking, keypoints = self.detect_keypoints(img, inner_rect)

        return img, img_for_tracking, keypoints


    @staticmethod
    def translation(flow: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        return np.median(flow[:,:,0].T), flow[:, :, 0].T


    def stabilize_img(
        self,
        img: np.ndarray,
        from_gray_img: np.ndarray,
        from_keypoints: np.ndarray,
        mode: StabilizeMode,
    ):
        """ Align a single frame with the previous
        input args
            img: image to stabilize
            img_for_tracking: enhanced gray image used to detect optical flow
            keypoints detected in previous image
            mode: stabilize using axes or rotation
        """
        gray_img = _enhance_img(
            cv2.cvtColor(np_to_uint8(img), cv2.COLOR_BGR2GRAY)
        )

        keypoints_to: np.ndarray = None
        success: bool = True
        try:
            keypoints_to, status, err = cv2.calcOpticalFlowPyrLK(
                prevImg=from_gray_img,
                nextImg=gray_img,
                prevPts=from_keypoints,
                nextPts=None,
                **self.lk_params
            )
        except Exception as e:
            print(red(f"exception: calcOpticalFlowPyrLK: {e}"))
            keypoints_to, status, err = cv2.calcOpticalFlowPyrLK(
                prevImg=from_gray_img,
                nextImg=gray_img,
                prevPts=from_keypoints,
                nextPts=None,
                **self.lk_params
            )
            success = False

        if success:
            if status is None:
                from_valid_kpts, to_valid_kpts = [], []
            else:
                from_valid_kpts, to_valid_kpts = from_keypoints[status==1], keypoints_to[status==1]


            # Estimate transformation matrix
            transformation = cv2.estimateAffinePartial2D(
                to_valid_kpts, from_valid_kpts)[0]
        else:
            print("[E] Failed calculating opticalflow")

        t_x, t_y, t_theta = 0., 0., 0.
        try:
            if transformation is not None:
                t_x = transformation[0][2]
                t_y = transformation[1][2]
                t_theta = np.mean(
                    [
                        np.arctan2(transformation[1][0], transformation[0][0]),
                        np.arctan2(-transformation[0][1], transformation[1][1])
                    ]
                )
                # scaling factor is ignored
            else:
                print("\ttransformation not found")

        except:
            print(red(f"exception: __stabilize_image: transformation not found, use previous"))
            print(f"\t{self.prev_transformation}")
            # Use translation of previous transformation
            t_x, t_y, _ = self.prev_transformation
            t_theta = 0

        if abs(t_x) > self.borders or abs(t_y) > self.borders:
            # When transformed, the image will be cropped
            raise UserWarning(red(f"erroneous calcOpticalFlowPyrLK: t_x={t_x}, t_y={t_y}"))
            print(f"{len(from_valid_kpts)} points, {len(to_valid_kpts)} points")
            # Currently apply previous transforamtion
            # TODO: crop the wrapped image
            t_x, t_y, t_theta = self.prev_transformation

        if mode & StabilizeMode.VERTICAL.value == 0:
            t_y = 0
        if mode & StabilizeMode.HORIZONTAL.value == 0:
            t_x = 0
        if mode & StabilizeMode.ROTATION.value == 0:
            t_theta = 0

        transformation = (t_x, t_y, t_theta)
        # Save this transformation for next image if needed
        self.prev_transformation = deepcopy(transformation)

        stabilized_img = apply_transformation(
            np.copy(img), transformation
        )

        return stabilized_img, transformation



    def stabilize(
        self,
        images: list[np.ndarray],
        segment: StabilizeSegment,
        initial_transformation: tuple[float, float, float] | None = None,
        inner_rects: tuple[tuple[float, float, float]] | None = None,
    ):
        """Stabilize a segment and returns:
          - list of stabilized images
          - first and last transformation: used to set the initial
              transformation of the next segment
          - list of transformations for this segment
        """
        print(lightgreen(f"initial_transformation: {initial_transformation}"))
        print(lightgreen(f"segment: {segment}"))
        print(lightgreen(f"inner_rects: {inner_rects}"))

        out_imgs: list[np.ndarray] = []

        self.descriptor = None
        print(lightgreen(f"extractor: {segment.extractor}"))
        if segment.extractor == 'sift':
            self.descriptor = cv2.SIFT_create(
                contrastThreshold=segment.contrast_threshold,
                edgeThreshold=segment.edge_threshold
            )
        elif segment.extractor == 'brisk':
            self.descriptor = cv2.BRISK_create()
        elif segment.extractor == 'gftt':
            self.descriptor = None
        else:
            raise ValueError(f"[E] descriptor {segment.extractor} is not supported")

        self.tracker_mask = None
        if segment.tracker.enable:
            self.tracker_mask = create_mask(
                segment.tracker,
                images[0].shape
            )

        # Deshake from the specified frame
        if segment.start_from == 'first':
            start_index = 0
        elif segment.start_from == 'last':
            start_index = len(images) - 1
        elif segment.start_from == 'middle':
            start_index = int(len(images) / 2)
        elif segment.start_from == 'frame':
            start_index = segment.ref
        else:
            raise ValueError(f"[E] \'{segment.start_from}\' is not a valid value")


        print(lightgreen(f"start_index: {start_index}"))

        transformations: list[tuple[float, float, float]] = []
        if (
            initial_transformation is not None
            and segment.start_from == 'middle'
        ):
            # Ignore the frame start no and use the previous segment last transformation
            raise ValueError("Error: stabilize, previous transformation will be ignored, correct the stabilization segments!")
            initial_transformation = None

        self.segment = segment
        has_inner_rect = True if inner_rects is not None and len(inner_rects) > 0 else False
        stabilized_img, img_for_tracking, from_keypoints = self.stabilize_initial_img(
            images[start_index],
            initial_transformation,
            inner_rect=inner_rects[start_index] if has_inner_rect else None
        )

        out_imgs.append(stabilized_img)
        transformations.append(initial_transformation)

        if segment.start_from in ('first', 'last'):
            from_start: bool = True if segment.start_from == 'first' else False
            if from_start:
                i_start, i_end, i_inc = 1, len(images), 1
            else:
                i_start, i_end, i_inc = start_index - 1, -1, -1

            for i in range(i_start, i_end, i_inc):
                # Stabilize an image using the prev as reference
                print(f"[I] stabilize frame {i}")
                stabilized, transformation = self.stabilize_img(
                    img=images[i],
                    from_gray_img=img_for_tracking,
                    from_keypoints=from_keypoints,
                    mode=segment.mode,
                )

                # Append or insert the stabilized img
                if from_start:
                    out_imgs.append(stabilized)
                    transformations.append(transformation)
                else:
                    out_imgs.insert(0, stabilized)
                    transformations.insert(0, transformation)

                # Detect the new keypoints
                if not segment.absolute:
                    img_for_tracking, from_keypoints = self.detect_keypoints(
                        img=stabilized,
                        inner_rect=inner_rects[i] if has_inner_rect else None
                    )

            if from_start:
                first_last_transformations: dict = dict(
                    first=None, last=copy(transformation)
                )
            else:
                first_last_transformations: dict = dict(
                    first=copy(transformation), last=None
                )

        else:
            i_start, i_end, i_inc = start_index + 1, len(images), 1
            for i in range(i_start, i_end, i_inc):
                print(f"[I] stabilize frame {i}")
                stabilized, transformation = self.stabilize_img(
                    img=images[i],
                    from_gray_img=img_for_tracking,
                    from_keypoints=from_keypoints,
                    mode=segment.mode,
                )
                out_imgs.append(stabilized)
                transformations.append(transformation)
                if not segment.absolute:
                    img_for_tracking, from_keypoints = self.detect_keypoints(
                        img=stabilized,
                        inner_rect=inner_rects[i] if has_inner_rect else None
                    )
            last_transformation = copy(transformation)

            stabilized, img_for_tracking, from_keypoints = self.stabilize_initial_img(
                img=images[start_index],
                initial_transformation=initial_transformation,
                inner_rect=inner_rects[i] if has_inner_rect else None
            )

            i_start, i_end, i_inc = start_index - 1, -1, -1
            for i in range(i_start, i_end, i_inc):
                print(f"[I] stabilize frame {i}")
                stabilized, transformation = self.stabilize_img(
                    img=images[i],
                    from_gray_img=img_for_tracking,
                    from_keypoints=from_keypoints,
                    mode=segment.mode,
                )
                out_imgs.insert(0, stabilized)
                transformations.insert(0, transformation)
                if not segment.absolute:
                    img_for_tracking, from_keypoints = self.detect_keypoints(
                        img=stabilized,
                        inner_rect=inner_rects[i] if has_inner_rect else None
                    )
            first_last_transformations: dict = dict(
                first=last_transformation, last=copy(transformation)
            )

        return out_imgs, first_last_transformations, transformations


