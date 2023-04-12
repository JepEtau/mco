# TODO: script
(1)
- try TTA
- simplify filters for video edition (deshake/replace): remove deshake, replace, rgb, geometry

(2)
- (?) '--frames' argument: copy frames form cache to 'frames' directory. Reason: compare with other tools? If frame does not exist, ignore

(3)
- Create "other filters": replace some images by white images
- force save before pre_replace ? bug with g_reportage
- effects: verify when replacing shots (asuivre/precedemment)
- geometry: 'dst' should be used to find target geometry. Reason: when replacing shots from an part to another
- clean filters.py
- custom filter depending on shot. Reason: ?
- (?) smooth stabilization: to evaluate


# TODO: video editor
(1)
- stabilize widget/model
- Add rulers when stabilize widget is selected

(2)
- add loop mode
- modification flags do not work: geometry, curves(?), replace(?)
- curves: save when closing is not working
- verify if key is pressed before changing crop values (key event)
- buttons (save, discard, ...) not working
- geometry: implement discard function for width: detect if modified
- curves: find shot from frame no and do not verify if it is the 1st frame.
- edit the curves library: remove/inspect curves without changing the curve selection. Reason: clean the db
- when no image loaded, reset all widgets

(3)
- F5 to refresh current shot only
- Ctrl+F5 to refresh all shots
- display filters for the shot

# TODO: other
- create a script to remove previous images
