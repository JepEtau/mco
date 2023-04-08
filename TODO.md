# TODO: script
(1)
- multiple segments for deshake
- smooth stabilization
- deshake: keep parameters and add a new one to enable/disable

(2)
- replace: circular dependency is not verified
- change shot_start to shot no. in config files? or use middle of shot? Reason:  avisynth
- custom filter depending on shot. Reason: deshake or do not block filtering if no deshake parameters

(3)
- Try SwinIR (g_reportage/reportage)
- effects: verify when replacing shots (asuivre/precedemment)
- geometry: 'dst' should be used to find target geometry. Reason: when replacing shots from an part to another
- clean filters.py
- replace "get_or_create_src_shot" function by "get_src_shot" and generate a warning
- parser_consolidate_audio_video is not used anymore: why?
- deshake: read from/write to ssd: no, fuck low memory, buy a new pc!
- (?) process single frame does not work anymore: repair and re-enable ?


# TODO: video editor
(1)
- verify if key is pressed before changing crop values (key event)
- geometry: implement discard function
- F5 to refresh current shot only
- Ctrl+F5 to refresh all shots
- Select shot rather than default if deshake is in filters with default crop 20
- Add rulers for deshakers

(2)
- display used filters
- stabilize widget/model
- curves: find shot from frame no and do not verify if it is the 1st frame.
- when saving, use middle of shot or shot_no? Reason: avisynth frame no

(3)
- edit the curves library: remove/inspect curves without changing the curve selection. Reason: clean the db

