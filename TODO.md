# TODO script
(1)
- use ROI for deshake
- stats: list unused curves. reason: clean the db
- add shot no. in ini files

(2)
- (?) use ROI when zooming in/out
- (?) smooth stabilization: to evaluate (g_fin)

(3)
- effects: verify when replacing shots (asuivre/precedemment)
- geometry: 'dst' should be used to find target geometry. Reason: when replacing shots from an part to another
- deshake to stabilize: list of transformations may be wrong due to the transformation applied to the first image. This may have an impact if smooth stabilisation is implemented
- (?) manual offsets to deshake
- clean filters.py


# TODO video editor
(1)
- Undo on geometry
- Add geometry error/fit_to_width in selection widget


(2)
- F5 to refresh current shot only
- (?) Fit to width does not work correctly
- curves: bug: mouseclick on graph creates a point if another widget is selected
- save when closing the application is not working
- selection widget: display unsaved shot in selection widget
- buttons (save, discard, ...) not working for some widgets (which ones?)
- edit the curves library: remove/inspect curves without changing the curve selection. Reason: clean the db

(3)
- (?) reorder options in .ini files
- when no image loaded, reset all widgets / disable all widgets if images missing
- add buttons to show/hide widgets
- stabilize: when table is disable, set qWidgetItem to disable (text should be grey)
- change selection widget to a standard widget (common)
- (?)Replace not allowed when multiple shot selected


# TODO other
- create a script to remove previous unused images

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
        ~~moviepy~~                 <-- not needed


# Known issues, but won't correct
- add_borders is inserted at the wrong place if using s0
- initial image dimensions is declared as constants: stats are erroneous with s0
- when saving/discarding, the widget automatically disable save/discard buttons without validation from the controller (i.e. assume saving is done and correct)
