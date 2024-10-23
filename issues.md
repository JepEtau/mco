# Fixed, to validate:
- DNxHD tags not working (hr)
- temporal filter: add metadata to generated video
- final extract as rgb48 when modifying frames. currently some effects are made in fp32 so why not converting to fp32?
    * scene: overlay, loop, fadeout, fadein,
    * src_scene: blend, title, zoom_in, loop_and_fadeout


# High priority
- frame replace / hr: exception when last frame is replaced (g_fin:007)

- Add grain at the end?
    noise=alls=14:allf=t+u
    noise=c0s=14:c0f=t+u
    http://underpop.online.fr/f/ffmpeg/help/noise.htm.gz

# Middle priority
- chaining fp32 / fp16 models


# Improvments (low priority)
- add full verification in geometry
- add watermark to the final version

(won't fix)
- g_debut in lr
