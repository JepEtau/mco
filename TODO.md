# TODO script
(1)
- geometry: use stabilize padding value: already done? seems not

(2)
- create a pre_rgb filter to modify RGB with deshaked/replaced images only
- remove 'save images' after deinterlacing from ffv1 file unless last task is deinterlace
- verify negative values for crop values when deshake is disable

(3)
- Create "other filters": replace some images by white images
- effects: verify when replacing shots (asuivre/precedemment)
- geometry: 'dst' should be used to find target geometry. Reason: when replacing shots from an part to another
- add 'extract filter to deinterlace source  with yadif deinterlacer
- clean filters.py
- (?) smooth stabilization: to evaluate


# TODO video editor
(1)
- separate allowed/preview
- preview button for stabilize
- use transformation saved in a cache list
- parse single shot only if database already been parsed

(2)
- add loop mode
- update save button when loading a segment or after modifications: use a signal
- Save when closing is not working
- display unsaved shot in selection widget
- buttons (save, discard, ...) not working
- geometry: implement discard function for width: detect if modified
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
- 2xHFA2kCompact_net_g_74000