SetFilterMTMode("DEFAULT_MT_MODE", MT_MULTI_INSTANCE)
SetFilterMTMode("FFVideoSource", MT_SERIALIZED)
SetFilterMTMode ("QTGMC", MT_MULTI_INSTANCE)

FFVideoSource("ep.mkv", cache=false)

AssumeTFF()
trim(0, 0)

QTGMC( \
    preset="Slower", \
    TR0=2, TR1=2, \
    EdiMode="EEDI3+NNEDI3", \
    Denoiser="dfttest", \
    EdiThreads=4 \
)

SelectEven()

Prefetch(4)
