
# SetFilterMTMode("DEFAULT_MT_MODE", MT_MULTI_INSTANCE)
FFMPEGSource2("A:\mco\inputs\f\f_ep01.mkv", cache=false)
AssumeTFF()
# trim(5643, -83)
QTGMC(preset="Slower")
SelectEven()
aWarpSharp2()
ConvertToRGB24()
# Prefetch(2)

