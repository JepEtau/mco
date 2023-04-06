# TODO: script
(1)
- custom filter depending on shot: reason: deshake or do not block filtering if no deshake parameters

(2)
- replace:
    * Circular dependency is not verified

(3)
- effects: verify when replacing shots (asuivre/precedemment)
- (?) process single frame does not work anymore: repair and re-enable ?
- replace "get_or_create_src_shot" function by "get_src_shot" and generate a warning
- clean filters.py
- deshake: read from/write to ssd: no, fuck low memory pc, buy a new one!
- parser_consolidate_audio_video is not used anymore: why?
- Try SwinIR (g_reportage/reportage)


# TODO: video editor
(1)
- geometry widget/model: rework on going
- display used filters


(2)
- stabilize widget/model
- curves: find shot from frame no and do not verify if it is the 1st frame. when saving, use middle of shot?

(3)
- edit the curves library: remove/inspect curves without changing the curve selection

