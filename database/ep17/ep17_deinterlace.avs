
SetFilterMTMode("DEFAULT_MT_MODE", MT_MULTI_INSTANCE)
FFMPEGSource2("A:\mco\inputs\k\k_ep17.mkv", cache=false, overwrite=true)
trim(34469, -1)

AssumeTFF()
QTGMC(preset="Slower", EdiThreads=2)
SelectEven()

aWarpSharp2()

ConvertToRGB24()
Prefetch(2)
