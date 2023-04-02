# TODO
(1)
- geometry is not working: rework this ASAP
- rework consolidate shot: geometry for g_asuivre/g_reportage
- rgb/geometry: error when processing shot
- Add step_no in mkv filename if vfilter is specified
- use file hash for rgb step
- (?) g_fin : fadeout is not done


(2)
- replace:
    * when in memory mode, do not flush images but replace images (copy)
    * Circular dependency is not verified
- Do not save pre_upscaled images if not specified in filters
- FFmpeg filter:
    * (?) use concatenate for all cases -> save images before
    * use ffv1 for FFmpeg filter except if images already exists.

(3)
- effects: verify when replacing shots (asuivre)
- (?) custom filter depending on shot
- (?) process single frame does not work anymore: repair and re-enable ?
- replace "get_or_create_src_shot" function by "get_src_shot" and generate a warning
- clean filters.py


(video editor)
- geometry does not work
- curves: find shot from frame no and do not verify if it is the 1st frame. when saving, use middle of shot?
- stabilize: modify widget
