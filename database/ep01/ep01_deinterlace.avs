
#~ SetFilterMTMode("DEFAULT_MT_MODE", MT_MULTI_INSTANCE)
#~ AssumeTFF()
#~ QTGMC(preset="Slower", EdiThreads=2)
#~ SelectEven()
#~ aWarpSharp2()
#~ ConvertToRGB24()
#~ # ImageWriter(file="frames\f_%05da.png", type="png")
#~ Prefetch(2)

SetFilterMTMode("DEFAULT_MT_MODE", MT_MULTI_INSTANCE)
FFMPEGSource2("A:\mco\inputs\f\f_ep01.mkv", cache=false, overwrite=true)
trim(5643, -83)
AssumeTFF()
QTGMC(preset="Slower", EdiThreads=2)
SelectEven()
aWarpSharp2()

#~ mdata = DePanEstimate(last)
#~ DePanStabilize(last, data=mdata)

#~ dull   = last
#~ sharp  = dull.LimitedSharpenFaster(ss_x=1.25, ss_y=1.25, strength=150, overshoot=1)
#~ Soothe(sharp, dull, keep=20)


ConvertToRGB24()
# ImageWriter(file="frames\f_%05da.png", type="png")
Prefetch(2)

