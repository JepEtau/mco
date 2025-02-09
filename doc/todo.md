## FIXED, to validate:


## HIGH priority
- chaining fp32 / fp16 models


## MIDDLE priority
- DPIR: allow noise parameter



## LOW priority and improvments
- inpaint: determine HtoD sync memory size ?
- add full verification in geometry
- add watermark to the final version

- temporal filter: add metadata to generated video




## Maybe an issue
- if 'en' target scene is a segment of a scene and this scene is also defined in fr target scenes


(won't fix)
- g_debut in lr
- crop after title overlay
~~- Add grain at the end?~~
    ~~noise=alls=14:allf=t+u~~
    ~~noise=c0s=14:c0f=t+u~~
    ~~ http://underpop.online.fr/f/ffmpeg/help/noise.htm.gz ~~
    -> *use davinci resolve*



## New archs / algorithms
https://github.com/rewaifu/resselt/

- sisr
    *~~ATD:         https://github.com/LabShuHangGU/Adaptive-Token-Dictionary~~
    * (RGT:         https://github.com/zhengchen1999/RGT)

- video
    * ~~AnimeSRv2~~
    * RVRT          https://github.com/JingyunLiang/RVRT
    * IART          https://github.com/kai422/IART
    * basicVSR++    https://github.com/ckkelvinchan/BasicVSR_PlusPlus
    * FTVSR         https://github.com/researchmm/FTVSR
    * EGVSR         https://github.com/Thmen/EGVSR
    * APISR         https://github.com/Kiteretsu77/APISR
    * CAVSR         https://github.com/aprBlue/CAVSR
    * handheldSR    https://github.com/Jamy-L/Handheld-Multi-Frame-Super-Resolution

- algorithms
    * ~~polyblur: https://github.com/teboli/polyblur~~
