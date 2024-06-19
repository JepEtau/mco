SetFilterMTMode("DEFAULT_MT_MODE", MT_MULTI_INSTANCE)
SetFilterMTMode("FFMPEGSource2", MT_SERIALIZED)
SetFilterMTMode ("QTGMC", MT_MULTI_INSTANCE)

FFMPEGSource2("A:\mco\inputs\f\f_ep36.mkv", cache=false)

AssumeTFF()
trim(0, -1)

QTGMC(preset="Slower", \
    TR0=2, TR1=2, \
    EdiMode="EEDI3+NNEDI3", \
    Denoiser="dfttest", \
    EdiThreads=4)

SelectEven()
ConvertToRGB24()

Prefetch(4)
