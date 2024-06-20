SetFilterMTMode("DEFAULT_MT_MODE", MT_MULTI_INSTANCE)
SetFilterMTMode("FFMPEGSource2", MT_SERIALIZED)
SetFilterMTMode ("QTGMC", MT_MULTI_INSTANCE)

FFMPEGSource2("ep.mkv", cache=false)

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
ConvertToRGB24()

Prefetch(4)
