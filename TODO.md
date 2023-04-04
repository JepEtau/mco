# TODO
(1)
- rework consolidate shot: geometry for g_asuivre/g_reportage
- (?) g_fin : fadeout is not done
- when in memory mode, do not flush images but replace images (copy)


(2)
- replace:
    * Circular dependency is not verified
- FFmpeg filter:
    * (?) use concatenate for all cases -> save images before
    * use ffv1 for FFmpeg filter except if images already exists.

(3)
- effects: verify when replacing shots (asuivre/precedemment)
- (?) custom filter depending on shot
- (?) process single frame does not work anymore: repair and re-enable ?
- replace "get_or_create_src_shot" function by "get_src_shot" and generate a warning
- clean filters.py


(video editor)
- geometry widget/model to rework
- curves: find shot from frame no and do not verify if it is the 1st frame. when saving, use middle of shot?
- stabilize: rework
- curves selection: library edition

