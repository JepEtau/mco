# Fixed, to validate:
- DNxHD tags not working (hr)
- temporal filter: add metadat to generated video
- final extract as rgb48 when modifying frames. currently some effects are made in fp32 so why not converting to fp32?
    * scene: overlay, loop, fadeout, fadein,
    * src_scene: blend, title, zoom_in, loop_and_fadeout


# High priority
- frame replace / hr: last frame is replaced (g_fin:007)


# Middle priority
- chaining fp32 / fp16 models


# Improvments (low priority)
- add full verification in geometry
- add watermark to the final version

(won't fix)
- g_debut in lr
