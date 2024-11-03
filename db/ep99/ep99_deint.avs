SetFilterMTMode("DEFAULT_MT_MODE", MT_MULTI_INSTANCE)
SetFilterMTMode("FFVideoSource", MT_SERIALIZED)
SetFilterMTMode ("QTGMC", MT_MULTI_INSTANCE)

FFVideoSource("ep.mkv", cache=false)
AssumeTFF()
trim(0, 0)

ConvertToYUY2(interlaced=true)
# ColorYUV(levels="TV->PC")
Colormatrix(mode="Rec.601->Rec.709", clamp=0, interlaced=true)
QTGMC( \
    preset="Slower", \
    TR0=2, TR1=2, \
    EdiMode="EEDI3+NNEDI3", \
    Denoiser="dfttest", \
    EdiThreads=4 \
)

SelectEven()
ConvertToYUV422()
ConvertBits(bits=10)
AssumeFPS(25)

# aWarpSharp2()

Prefetch(4)
