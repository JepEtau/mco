# TODO script
(1)
- avisynth to upscale reportage
- Add FFmpeg stab. test on ep02: shot 7/10/22/30/32
- Add day no in the filename to improve sorting in explorer: WARNING, this breaks compatibility!!!
- Add english language
- Use TypedDict and documentation to improve readibility/understanding

(2)
- use multiple stab software (cv2, ffmpeg) alg in the same shot: currently not implemented. Is this really needed?
- use previous stabilized frame as the reference for the new segment to avoid an artifact

(3)
- (?) smooth stabilization: to evaluate (g_fin)
- stats: list unused curves. reason: clean the db
- effects: verify when replacing shots (asuivre/precedemment)
- geometry: 'dst' should be used to find target geometry. Reason: when replacing shots from an part to another
- deshake to stabilize: list of transformations may be wrong due to the transformation applied to the first image. This may have an impact if smooth stabilisation is implemented
- (?) manual offsets to deshake
- clean filters.py

- Modify install.md for scunet:
    https://github.com/cszn/KAIR/releases/download/v1.0/scunet_color_real_gan.pth
    https://github.com/cszn/KAIR/releases/download/v1.0/scunet_color_real_psnr.pth


# TODO video editor
(1)
- add button to show the enhanced grey image used to stabilize
- add button to autocrop
- do not parse all shots when starting, reparse shot when selecting

(2)
- stabilize: add options to select stab algo
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
* stabilize:
- Add stitching before stabilize?

* Temporal denoising
    https://github.com/JingyunLiang/VRT
    https://github.com/m-tassano/fastdvdnet
    https://github.com/JingyunLiang/RVRT
* Removing moving objects
    https://github.com/zllrunning/video-object-removal

*Upscale
    https://github.com/hyw-dev/SpatiotemporalResampling

# TODO other
- experiment script to identify the same frames of a shot:
    * will it work before stabilization?
    * how to verify that it gives good result?
        - small changes ep01 shot no. 157
        - raining: e01 shot no. 23/27/120/121
        - small artifacts: ep 046
        - image is distorted:  ep01 046
    * not replacing is better than wrong replacement
- list python modules (to clean the environment)
    AnimeSR
        basicsr         <- required
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

- https://github.com/Kiyamou/VapourSynth-RealCUGAN-ncnn-Vulkan, try syncgap
- https://forum.videohelp.com/threads/409432-Best-%28not-super-slow%29-upscalers-for-1995-2010-Animes-%28Like-Naruto-etc%29/page3


# Known issues, but won't correct
- add_borders is inserted at the wrong place if using s0
- initial image dimensions is declared as constants: stats are erroneous with s0
- fadein: if stabilize, segment shall use 'middle' of shot as the ref. frame
- fadein: fadein is always done on a the same image. No need for someting else.
- stabilize: when table is disable, set qWidgetItem to disabled (text should be gray)

