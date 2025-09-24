

from warnings import warn
import cv2
import numpy as np

from parsers import (
    Warp,
)
from utils.p_print import *
from .homography import (
    detect_and_describe,
    filter_matches_by_distance,
    get_homography,
    match_keypoints_bf,
    match_keypoints_knn,
)


def warp_image(img: np.ndarray, ref_img: np.ndarray, warp: Warp) -> np.ndarray:

    feature_extractor: str = 'sift'
    # feature_extractor: str = 'akaze'    
    feature_matching = warp.matcher

    # print(f"shapes: {img.shape} / {ref_img.shape}")
    print(f"warp with: {warp}")
    current_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ref_gray = cv2.cvtColor(ref_img, cv2.COLOR_BGR2GRAY)

    clip_limit = 2
    tile_grid_size=(8, 8)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)

    ref_gray = clahe.apply(ref_gray)
    current_gray = clahe.apply(current_gray)

    # Add border to correctly detect the outer limits
    border = 20
    ref_gray_bordered = cv2.copyMakeBorder(
        ref_gray, top=border, bottom=border, left=border, right=border,
        borderType=cv2.BORDER_CONSTANT, value=[0, 0, 0]
    )
    current_gray_bordered = cv2.copyMakeBorder(
        current_gray, top=border, bottom=border, left=border, right=border,
        borderType=cv2.BORDER_CONSTANT, value=[0, 0, 0]
    )

    keypoints_ref, features_ref = detect_and_describe(image=ref_gray_bordered, extractor_method=feature_extractor)
    keypoints, features = detect_and_describe(image=current_gray_bordered, extractor_method=feature_extractor)
    max_disp: int = int(img.shape[0] * warp.max_distance_ratio)
    if feature_matching == 'bf':
        matches = match_keypoints_bf(
            keypoints, features, keypoints_ref, features_ref, method=feature_extractor,
            max_disp=max_disp
        )
    elif feature_matching == 'knn':
        matches = match_keypoints_knn(
            features, features_ref, ratio=warp.knn_ratio
        )
    else:
        warn(red(f"error: unknown feature matching: {feature_matching}"))        
    matches = filter_matches_by_distance(
        matches,
        keypoints,
        keypoints_ref,
        max_disp=max_disp
    )

    # Get homography
    M = get_homography(
        keypoints, keypoints_ref,
        features, features_ref,
        matches,
        reproj_threshold=3.0
    )
    if M is None:
        print(red("Error: get_homography returned None")) 
    (matches, H, status) = M

    # Apply the perspective transformation
    img: np.ndarray = np.ascontiguousarray(cv2.copyMakeBorder(
        img,
        top=border, bottom=border, left=border, right=border,
        borderType=cv2.BORDER_CONSTANT, value=[0, 0, 0]
    ))
    warped_img = cv2.warpPerspective(img ,H, (img.shape[1], img.shape[0]))
    warped_img = np.ascontiguousarray(
        warped_img[
            border:warped_img.shape[0] - border,
            border:warped_img.shape[1] - border,
            :
        ]
    )

    return warped_img
