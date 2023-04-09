
SetFilterMTMode("DEFAULT_MT_MODE", MT_MULTI_INSTANCE)

FFMPEGSource2("A:\mco\inputs\f\f_ep01.mkv", cache=false, overwrite=true)
trim(5643, -83)
AssumeTFF()
# QTGMC(preset="Slower", EdiThreads=2)
QTGMC(preset="Slower", EdiThreads=2)
SelectEven()
aWarpSharp2()

ConvertToRGB24()
# ImageWriter(file="frames\f_%05da.png", type="png")
Prefetch(2)

