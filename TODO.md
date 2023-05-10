# TODO script
(1)
- use ROI for deshake
- Try removing stab before upscale when there is rainfall
- (?) Try SwinIR, model: https://github.com/Bubblemint864/AI-Models

(2)
- stats: list unused curves. reason: clean the db
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
- Add geometry error/fit_to_width in selection widget

(2)
- F5 to refresh current shot only
- curves: bug: mouseclick on graph creates a point if another widget is selected
- edit the curves library: remove/inspect curves without changing the curve selection. Reason: clean the db

(3)
- (?) reorder options in .ini files
- when no image loaded, reset all widgets / disable all widgets if images missing
- add buttons to show/hide widgets
- stabilize: when table is disable, set qWidgetItem to disable (text should be gray)
- (?)Replace not allowed when multiple shot selected


# TODO other

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
