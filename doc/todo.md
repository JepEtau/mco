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

status:
    module
    integrated
    tested
    done


- sisr
    * ~~ATD~~               https://github.com/LabShuHangGU/Adaptive-Token-Dictionary
    * ~~RGT~~               https://github.com/zhengchen1999/RGT
    * MST++                 https://github.com/caiyuanhao1998/MST-plus-plus
        Spectral Recovery Challenge
    * TTSR                  https://github.com/researchmm/TTSR


- video
    * ~~basicVSR++~~        https://github.com/ckkelvinchan/BasicVSR_PlusPlus
        no support, missing source code for 2x
        but still good

    * ~~FTVSR (4x)~~        https://github.com/researchmm/FTVSR
        basé sur mmedit... grrr derriere IART
        slow according to TMP vsr
        to old
        no valid comparisons with other

    * ~~EGVSR~~             https://github.com/Thmen/EGVSR
        not clear enough, old

    * ~~APISR~~             https://github.com/Kiteretsu77/APISR
        sisr, tester modèles? beurk

    * ~~handheldSR~~        https://github.com/Jamy-L/Handheld-Multi-Frame-Super-Resolution
        reported as slow af

    * ~~AnimeSRv2~~
        __done__

    * RVRT (1x, 4x)         https://github.com/JingyunLiang/RVRT
        __integrated__

    * IART (4x)             https://github.com/kai422/IART
        use SPyNet still
        __integrated__

    * CAVSR                 https://github.com/aprBlue/CAVSR
        n'utilise pas SPyNet mais autre chose...
        better than basicvsr++, ftvsr
        __integrated__

    * EvTexture (4x)        https://github.com/dachunkai/evtexture
        __integrated__

    * PSRT-recurrent        https://github.com/XPixelGroup/RethinkVSRAlignment
        SPyNet mais intéressant
        __integrated__

    * TMP                   https://github.com/xtudbxk/TMP
        __integrated__


    * CFDVSR                https://github.com/house-leo/cfdvsr
        non publié, auteur considère que mieux que les autres....

    * TTVSR                 https://github.com/researchmm/TTVSR
        inference function might be interesting

    * VQD-SR                https://github.com/researchmm/vqd-sr


- Optical Flow
    * unimatch (GMflow+)    https://github.com/autonomousvision/unimatch
        __integrated__

    * GMflow                https://github.com/haofeixu/gmflow
        __module__
        not possible to differentiate GMflow from unimatch

    * VideoFlow             https://github.com/XiaoyuShi97/VideoFlow
        /

    * FlowFormer++          https://github.com/XiaoyuShi97/FlowFormerPlusPlus
        /

    * FlowFormer            https://github.com/drinkingcoder/FlowFormer-Official
        /

    * Raft
        __integrated__



- algorithms
    * ~~polyblur: https://github.com/teboli/polyblur~~
