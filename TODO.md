# TODO script
(1)
- use ROI when zooming in/out
- deshake to stabilize: list of transformations may be wrong due to the transformation applied to the first image
- stabilize: when segments are erroneous, do not stabilize

(2)
- (?) smooth stabilization: to evaluate (g_fin)


(3)
- effects: verify when replacing shots (asuivre/precedemment)
- geometry: 'dst' should be used to find target geometry. Reason: when replacing shots from an part to another
- clean filters.py


# TODO video editor
(1)
- reorder .ini files
- video editor shall never write hash codes

- curves: add loop mode
- curves: Add luma value in curves
- curves: Add other rgb filters to ajdust levels
- geometry: add 'minimum crop'
- stabilize widget: verify if "save putton' to enabled if segment removed

(2)
- save when closing the application is not working
- stabilize widget: update save button when loading a segment or after modifications: use a signal
- selection widget: display unsaved shot in selection widget
- buttons (save, discard, ...) not working for some widgets (which ones?)
- edit the curves library: remove/inspect curves without changing the curve selection. Reason: clean the db
- when no image loaded, reset all widgets / disable all widgets if images missing

(3)
- add buttons to show/hide widgets
- stabilize: when table is disable, set qWidgetItem to disable (text should be grey)
- change selection widget to a standard widget (common)
- F5 to refresh current shot only
- display filters for the shot
- (?)Replace not allowed when multiple shot selected


# TODO other
- create a script to remove previous images
- list models that are already tested
- list python modules (to clean the environment)
    AnimeSR
        basicsr
        facexlib
        ffmpeg-python
        numpy
        opencv-python
        pillow
        psutil
        torch
        torchvision
        tqdm
    ESRGAN
        opencv_python
        numpy
        torch
        rich
        typer
    Real-ESRGAN
        basicsr>=1.4.2
        facexlib>=0.2.5
        gfpgan>=1.3.5
        numpy
        opencv-python
        Pillow
        torch>=1.7
        torchvision
        tqdm
    Real-CUGAN
        torch>=1.0.0
        numpy
        opencv-python
        ~~moviepy~~                 <-- no needed


# Known issues, but won't correct
- add_borders is inserted at the wrong place if using s0
- when saving/discarding, the widget automatically disable save/discard buttons without validation from the controller (i.e. assume saving is done and correct)
