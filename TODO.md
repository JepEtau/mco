# TODO: script
(1)
- FFmpeg filter:
    * (?) use concatenate for all cases -> save images before
    * use ffv1 for FFmpeg filter except if images already exists: because of bufsize limitation and writing/reading ffv1 file is faster than reading images
- geometry: change 'part' by 'target', 'fit_to_part' by 'fit_to_width'

(2)
- replace:
    * Circular dependency is not verified

(3)
- effects: verify when replacing shots (asuivre/precedemment)
- (?) custom filter depending on shot
- (?) process single frame does not work anymore: repair and re-enable ?
- replace "get_or_create_src_shot" function by "get_src_shot" and generate a warning
- clean filters.py
- deshake: read from/write to ssd
- parser_consolidate_audio_video is not used anymore: why?


# TODO: video editor
(1)
- geometry widget/model to rework


(2)
- stabilize widget/model
- curves: find shot from frame no and do not verify if it is the 1st frame. when saving, use middle of shot?

(3)
- edit the curves library: remove/inspect curves without changing the curve selection

