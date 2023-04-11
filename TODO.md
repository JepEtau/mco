# TODO: script
(1)
- verify img quality: deinterlaced vs deinterlaced/ffv1
- Create "other filters": replace some images by white images

(2)
- change shot_start to shot no. in config files? or use middle of shot? Reason:  avisynth
- custom filter depending on shot. Reason: deshake or do not block filtering if no deshake parameters

(3)
- smooth stabilization
- force save before pre_replace ? bug with g_reportage
- effects: verify when replacing shots (asuivre/precedemment)
- geometry: 'dst' should be used to find target geometry. Reason: when replacing shots from an part to another
- clean filters.py
- replace "get_or_create_src_shot" function by "get_src_shot" and generate a warning: patched it verify before removing it
- parser_consolidate_audio_video is not used anymore: why?
- (?) process single frame does not work anymore: repair and re-enable ?


# TODO: video editor
(1)
- curves: save when closing is not working
- verify if key is pressed before changing crop values (key event)
- stabilize widget/model
- Add rulers when stabilize widget is selected
- buttons (save, discard, ...) not working

(2)
- geometry: implement discard function for width: detect if modified
- filter selection: change combobox to radio buttons and disable the unused ones
- curves: find shot from frame no and do not verify if it is the 1st frame.
- when saving, use middle of shot or shot_no? Reason: avisynth frame no
- edit the curves library: remove/inspect curves without changing the curve selection. Reason: clean the db

(3)
- F5 to refresh current shot only
- Ctrl+F5 to refresh all shots
- display filters for the shot

# TODO: other
- create a script to remove previous images
