# TODO script
(1)

- audio/video synchro
    ep01: fr, en
    ep02: fr, en
    ep03: fr, en
    ep04: fr, en
    ep05: fr, en
    ep06: fr, en
    ep07: fr, en
    ep08:




- bug: when start of 1st shot of episode != end of precedemment:
    * insert black frames as silence
    * if avsync (precedemment) > 0, reduce the silence
    * if avsync is still > 0, remove video frames

- regression: stabilization does not work on lr images. g_debut, shot no.3: default mode is not static
- bug: stab: !!! ROI does not work for lowres img !!!
    -> modified, to validate
- bug: stab: !!! does ROI mask really work with gftt? !!!
    -> to investigate

- enhancement: avisynth to upscale/sharpen documentaire: implemented. To be validated
- enhancement: integrate color fix
- enhancement: integrate speckle noise
- enhancement: (?) add lhm method from chaiNNer

- enhancement: what about autocrop: use it in the chain or as a tool (video editor)?
- enhancement: Add FFmpeg stab. test on ep02: try on shots 7/10/22/30/32


(2)
- stab: use multiple software (cv2, ffmpeg) alg in the same shot: currently not implemented. Is this really needed?
- stab: use previous stabilized frame as the reference for the new segment to avoid possible artifact

(3)
- enhancement: stab: get mean/contrast to choose an algo rather than selecting between auto/contrast?
- refactoring of audio/generate.py: merge the 2 functions
- (?) smooth stabilization: to evaluate (g_fin)
- stats: list unused curves. reason: clean the db
- effects: verify when replacing shots (asuivre/precedemment)
- geometry: 'dst' should be used to find target geometry. Reason: when replacing shots from an part to another
- deshake to stabilize: list of transformations may be wrong due to the transformation applied to the first image. This may have an impact if smooth stabilisation is implemented


# TODO video editor
(1)
- add button to show the enhanced grey image used to stabilize
- add button to autocrop
- do not parse all shots when starting, reparse shot when selecting
- stab: gray image enhancement only after having applied the mask

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
- Add homography before stabilize?

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
- fadein: if stabilize, segment shall use 'middle' of shot as the ref. frame no
- fadein: fadein is always done on a the same image (= loop and fade-in). No need for someting else.
- stabilize: when table is disable, set qWidgetItem to disabled (text should be gray)
- fade_in/shot duration is not tracked in the hash code, this means that the generated shot video used by both fr/en has to be deleted when switch fr/en (will not impact any end user except me!)
- Multi-language: erroneous video shots when switching en<->fr. Because the same shot is used for both but duration may differ (constrained by the audio track). These shots are the first/last shot of each part. No one except those who switches the language will be impacted.
