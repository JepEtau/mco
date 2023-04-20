# TODO script
(1)
- create a pre_rgb filter to modify RGB with deshaked/replaced images only
- integrate animesr

(2)
- stabilize: when 2 segments are separated by some frames, the first image of the 2nd segment is not aligned with previous frames (g_fin, shot no. 0)
- (?) smooth stabilization: to evaluate (g_fin)

(3)
- verify negative values for crop values when deshake is disable
- remove k_ed_ref
- create "other filters": replace some images by white images
- effects: verify when replacing shots (asuivre/precedemment)
- geometry: 'dst' should be used to find target geometry. Reason: when replacing shots from an part to another
- (?) add 'extract' filter to deinterlace source  with yadif deinterlacer
- clean filters.py


# TODO video editor
(1)
- Get transformations matrix and save them in frame struct
- stabilize all selected shots (keep transformation matrix only)
- add buttons to show/hide widgets

(2)
- Add a pre_rgb step
- add loop mode
- disable all widgets if images missing
- parse single shot only if database already been parsed
- update save button when loading a segment or after modifications: use a signal
- Save when closing is not working
- display unsaved shot in selection widget
- buttons (save, discard, ...) not working
- add save 'target' in geometry widget
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
- retry animesr
- list models that are already tested