

FFMPEGSource2("A:\mco\inputs\s\s_ep11.mkv", cache=false, overwrite=true)
trim(33659, -1)

AssumeTFF()
QTGMC(preset="Slower")
SelectEven()

aWarpSharp2()

ConvertToRGB24()

