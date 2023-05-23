# TODO script
(1)
- use ROI for deshake

(2)
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
- Add geometry error/fit_to_width in selection widget

(2)
- curves: bug: mouseclick on graph creates a point if another widget is selected
- edit the curves library: remove/inspect curves without changing the curve selection. Reason: clean the db
- F5 to refresh current shot only
- when no image loaded, reset all widgets / disable all widgets if images missing

(3)
- (?) reorder options in .ini files
- add buttons to show/hide widgets
- (?)Replace not allowed when multiple shot selected


22676_deshake = """enable=true;
	cv2_deshaker:start=22676:end=22754:ref=end:mode=horizontal+rotation+vertical:
		tracker=enable, inside,
		(0.0)(0.1199)(173.1199)(450.0),
		(1124.0)(1487.0)(1487.1199)(1124.1199);
	cv2_deshaker:start=22783:end=22805:ref=start:mode=horizontal+rotation+vertical;
	cv2_deshaker:start=22813:end=22871:ref=start:mode=rotation+vertical;
	"""

33966_deshake = """enable=true;
	cv2_deshaker:start=33966:end=33995:ref=middle:mode=horizontal+rotation+vertical:
		tracker=enable, inside,
		(0.0)(0.550)(232.500)(232.0),
		(650.0)(650.485)(1032.280)(1440.280)(1440.0);
	"""


# Models/Algo
* Cartoons:
    Fatality_DeBlur
    Focus + Focus_Moderate https://u.pcloud.link/publink/show?code=kZS4XhVZ1GKsTtkjdULdYn6z9pTHs7fdLvR7
    CelFrames 1.0
    1x_DeInterPaint (Deinterlacing)

* Realistic:
    omnisr
    4xNomos8kSC
    2xParimgCompact
    4xLSDIRCompactC3
    4xLSDIRCompactN
    4x_rybu
    4x-MultiUpscale-C3/C4/C5/T1 (and DetailScale)

* Temporal denoising
    https://github.com/JingyunLiang/VRT
    https://github.com/m-tassano/fastdvdnet
    TempFormer: https://www.youtube.com/watch?v=LA747HTukTQ
    https://dasongli1.github.io/publication/grouped-shift-net/
    https://github.com/JingyunLiang/RVRT

* SR
    https://github.com/IceClear/StableSR.git

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
- fadein: if stabilize, segment shall use 'middle' of shot as the ref. frame
- fadein: fadein is always done on a the same image. No need for someting else.
- stabilize: when table is disable, set qWidgetItem to disable (text should be gray)

