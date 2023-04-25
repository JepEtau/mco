# TODO script
(1)

(2)
- (?) smooth stabilization: to evaluate (g_fin)
- create "other filters": replace some images by white images
- stabilize: when 2 segments are separated by some frames, the first image of the 2nd segment is not aligned with previous frames (g_fin, shot no. 0)

(3)
- effects: verify when replacing shots (asuivre/precedemment)
- geometry: 'dst' should be used to find target geometry. Reason: when replacing shots from an part to another
- clean filters.py


# TODO video editor
(1)
- curves: add loop mode
- curves: Add luma value in curves
- curves: Add other rgb filters to ajdust levels
- geometry: add 'minimum crop'
- stabilize widget: get real frame no if step==sharpen
- stabilize widget: too complicated
- stabilize widget: set "save putton' to enabled if segment removed
- move guidelines to main window
- Get transformations matrix and save them in frame struct
- stabilize all selected shots (keep transformation matrix only)
- add buttons to show/hide widgets

(2)
- Save when closing the application is not working
- stabilize widget: update save button when loading a segment or after modifications: use a signal
- selection widget: display unsaved shot in selection widget
- buttons (save, discard, ...) not working for some widgets (which ones?)
- edit the curves library: remove/inspect curves without changing the curve selection. Reason: clean the db
- when no image loaded, reset all widgets / disable all widgets if images missing

(3)
- change selection widget to a standard widget (common)
- F5 to refresh current shot only
- display filters for the shot
- (?)Replace not allowed when multiple shot selected


# TODO other
- create a script to remove previous images
- list models that are already tested


# Known issues, but won't correct
- add_borders is inserted at the wrong place if using s0
- when saving/discarding, the widget automatically disable save/discard buttons without validation from the controller (i.e. assume saving is done and correct)
