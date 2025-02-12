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
    intégré
    testé
    done


- sisr
    *~~ATD:         https://github.com/LabShuHangGU/Adaptive-Token-Dictionary~~
    * (RGT:         https://github.com/zhengchen1999/RGT)

- video
    * ~~AnimeSRv2~~
        done

    * RVRT (1x, 4x)         https://github.com/JingyunLiang/RVRT
        intégré

    * IART (4x)             https://github.com/kai422/IART
        use SPyNet still

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
        sisr, tester modèles?

    * CAVSR                 https://github.com/aprBlue/CAVSR
        n'utilise pas SPyNet mais autre chose...
        better than basicvsr++, ftvsr

    * EvTexture (4x)        https://github.com/dachunkai/evtexture

    * handheldSR            https://github.com/Jamy-L/Handheld-Multi-Frame-Super-Resolution

    * PSRT-recurrent        https://github.com/XPixelGroup/RethinkVSRAlignment
        SPyNet mais intéressant

    * CFDVSR                https://github.com/house-leo/cfdvsr
        non publié, auteur considère que mieux que les autres....

    * TMP                   https://github.com/xtudbxk/TMP


- Optical Flow
    * unimatch (GMflow+)    https://github.com/autonomousvision/unimatch
        intégré

    * GMflow                https://github.com/haofeixu/gmflow
        module

    * VideoFlow             https://github.com/XiaoyuShi97/VideoFlow
        more video than the others

    * FlowFormer++          https://github.com/XiaoyuShi97/FlowFormerPlusPlus

    * FlowFormer            https://github.com/drinkingcoder/FlowFormer-Official

    * Raft
        intégré







- algorithms
    * ~~polyblur: https://github.com/teboli/polyblur~~
