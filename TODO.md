# TODO: script
(1)
- simplify filters for video edition (deshake/replace): remove deshake, replace, rgb, geometry
- borders for deshake lres:8? hres:16? Reason: geometry shall not be modified if multiple deshake/stabilize

(2)
- (?) '--frames' argument: copy frames form cache to 'frames' directory. Reason: compare with other tools? If frame does not exist, ignore

(3)
- Create "other filters": replace some images by white images
- force save before pre_replace ? bug with g_reportage
- effects: verify when replacing shots (asuivre/precedemment)
- geometry: 'dst' should be used to find target geometry. Reason: when replacing shots from an part to another
- clean filters.py
- (?) custom filter depending on shot
- (?) smooth stabilization: to evaluate


# TODO: video editor
(1)
- stabilize: generate images

(2)
- All buttons: set disabledon
- add loop mode
- update save button when loading a segment or after modifications: use a signal
- Save when closing is not working
- display unsaved segment in selection widget
- buttons (save, discard, ...) not working
- geometry: implement discard function for width: detect if modified
- edit the curves library: remove/inspect curves without changing the curve selection. Reason: clean the db
- when no image loaded, reset all widgets

(3)
- change selection widget to a standard widget (common)
- F5 to refresh current shot only
- Ctrl+F5 to refresh all shots
- display filters for the shot

# TODO: other
- create a script to remove previous images
