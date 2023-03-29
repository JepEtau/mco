
SetFilterMTMode("DEFAULT_MT_MODE", MT_MULTI_INSTANCE)
FFMPEGSource2("A:\mco\inputs\s\s_ep12.mkv", cache=false, overwrite=true)
trim(38882, -1)

AssumeTFF()
QTGMC(preset="Slower", EdiThreads=2)
SelectEven()

aWarpSharp2()

ConvertToRGB24()
Prefetch(2)
