# TODO script
(1)
- avisynth to upscale reportage
- Add FFmpeg stab
ep02: shot 7/10/22/30/32

(2)
- use multiple stab alg in the same shot: currently not working
- use previous stabilized frame as the reference for the new segment to avoid an artifact
- add filter info as watermark
- stats: list unused curves. reason: clean the db
- (?) smooth stabilization: to evaluate (g_fin)

(3)
- effects: verify when replacing shots (asuivre/precedemment)
- geometry: 'dst' should be used to find target geometry. Reason: when replacing shots from an part to another
- deshake to stabilize: list of transformations may be wrong due to the transformation applied to the first image. This may have an impact if smooth stabilisation is implemented
- (?) manual offsets to deshake
- clean filters.py


# TODO video editor
(1)
- add button to show the enhanced grey image used to stabilize
- stabilize: add options when changing stab algo

(2)
- Add geometry error/fit_to_width in selection widget
- curves: bug: mouseclick on graph creates a point if another widget is selected
- edit the curves library: remove/inspect curves without changing the curve selection. Reason: clean the db
- F5 to refresh current shot only
- when no image loaded, reset all widgets / disable all widgets if images missing

(3)
- (?) reorder options in .ini files
- add buttons to show/hide widgets
- (?)Replace not allowed when multiple shot selected


# Models/Algo
* Cartoons:
    Fatality_DeBlur
    Focus + Focus_Moderate https://u.pcloud.link/publink/show?code=kZS4XhVZ1GKsTtkjdULdYn6z9pTHs7fdLvR7
    CelFrames 1.0
    1x_DeInterPaint (Deinterlacing)

* Temporal denoising
    https://github.com/JingyunLiang/VRT
    https://github.com/m-tassano/fastdvdnet
    TempFormer: https://www.youtube.com/watch?v=LA747HTukTQ
    https://dasongli1.github.io/publication/grouped-shift-net/
    https://github.com/JingyunLiang/RVRT


# TODO other
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
    Real-CUGAN
        torch>=1.0.0
        numpy
        opencv-python
        ~~moviepy~~                 <-- not needed


# Known issues, but won't correct
- add_borders is inserted at the wrong place if using s0
- initial image dimensions is declared as constants: stats are erroneous with s0
- fadein: if stabilize, segment shall use 'middle' of shot as the ref. frame
- fadein: fadein is always done on a the same image. No need for someting else.
- stabilize: when table is disable, set qWidgetItem to disabled (text should be gray)

