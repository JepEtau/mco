

supported_ffmpeg_filters : tuple[str] = (
    "hqdn3d",
    "unsharp",
    "cas",
    "edgedetect",
    "bm3d",
    "atadenoise",
    "removegrain",
    "tmedian",
    "bilateral",
    "noise",
)

supported_cv2_filters : tuple[str] = (
    "dilation",
    "erosion",
    "opening",
    "closing",
    "cv2_bilateral",
    "cv2_nlmeans",
)

supported_cpu_filters : tuple[str] = (
    "nlmeans",
)

supported_cuda_filters : tuple[str] = (
    # "dilation",
    # "erosion",
    # "opening",
    # "closing",
    "darker_thinner",
    "resize",
    "resize_to",
    "gaussian_noise",
    "rotate90",
    "unsharp_mask",
)


supported_filters: tuple[str] = (
    supported_ffmpeg_filters
    + supported_cv2_filters
    + supported_cuda_filters
    + supported_cpu_filters
)


supported_encoder_filters : tuple[str] = (
    supported_ffmpeg_filters
    + supported_cpu_filters
)
