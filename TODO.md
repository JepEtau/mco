# TODO script
(1)

(2)
- (?) smooth stabilization: to evaluate (g_fin)
- create "other filters": replace some images by white images
- stabilize: when 2 segments are separated by some frames, the first image of the 2nd segment is not aligned with previous frames (g_fin, shot no. 0)

(3)
- add_borders is inserted at the wrong place if using s0
- verify negative values for crop values when deshake is disable
- effects: verify when replacing shots (asuivre/precedemment)
- geometry: 'dst' should be used to find target geometry. Reason: when replacing shots from an part to another
- clean filters.py


# TODO video editor
(1)
- Add luma value in curves
- Add other rgb filters
- geometry: add 'minimum crop'
- stabilize widget: discard
- stabilize widget: get real frame no if step==sharpen
- stabilize widget: too complicated
- stabilize widget: set "save putton' to enabled if segment removed
- move guidelines to main window
- Get transformations matrix and save them in frame struct
- stabilize all selected shots (keep transformation matrix only)
- add buttons to show/hide widgets
- add save 'target' in geometry widget

(2)
- Save when closing is not working
- parse single shot only if database already been parsed
- add loop mode
- disable all widgets if images missing
- update save button when loading a segment or after modifications: use a signal
- display unsaved shot in selection widget
- buttons (save, discard, ...) not working
- edit the curves library: remove/inspect curves without changing the curve selection. Reason: clean the db
- when no image loaded, reset all widgets

(3)
- if no progressive images saved, use ffv1 file to fill buffer of images
- change selection widget to a standard widget (common)
- F5 to refresh current shot only
- Ctrl+F5 to refresh all shots
- display filters for the shot
- (?)Replace not allowed when multiple shot selected


# TODO other
- create a script to remove previous images
- list models that are already tested