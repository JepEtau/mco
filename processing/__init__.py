

supported_ffmpeg_filters : tuple[str] = (
    "hqdn3d",
    "unsharp",
    "cas",
    "edgedetect",
)

supported_cv2_filters : tuple[str] = (
    "dilation",
    "erosion",
    "opening",
    "closing",
)

supported_cuda_filters : tuple[str] = (
    # "dilation",
    # "erosion",
    # "opening",
    # "closing",
    "darker_thinner",
    "resize",
    "nlmeans",
)


supported_filters: tuple[str] = (
    supported_ffmpeg_filters
    + supported_cv2_filters
    + supported_cuda_filters
)
