# TODO

- determine HtoD sync memory size
- do not use inpaint shape for HtoD/DtoH transfers
- create oblong shape
- replace mask dtype to torch.bool


# Issues

## Fixed, to validate:


## High priority
- Add grain at the end?
    noise=alls=14:allf=t+u
    noise=c0s=14:c0f=t+u
    http://underpop.online.fr/f/ffmpeg/help/noise.htm.gz


## Middle priority
- temporal filter: add metadata to generated video
- chaining fp32 / fp16 models


## Improvments (low priority)
- add full verification in geometry
- add watermark to the final version

(won't fix)
- g_debut in lr
