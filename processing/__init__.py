

supported_ffmpeg_filters : tuple[str] = (
    "hqdn3d",
    "unsharp",
    "cas",
    "edgedetect",
    "nlmeans",
    "bm3d",
    "atadenoise",
    "removegrain",
    "tmedian",
    "bilateral",
)

supported_cv2_filters : tuple[str] = (
    "dilation",
    "erosion",
    "opening",
    "closing",
    "cv2_bilateral",
)

supported_cuda_filters : tuple[str] = (
    # "dilation",
    # "erosion",
    # "opening",
    # "closing",
    "darker_thinner",
    "resize",
    "nlmeans_sk",
)


supported_filters: tuple[str] = (
    supported_ffmpeg_filters
    + supported_cv2_filters
    + supported_cuda_filters
)
