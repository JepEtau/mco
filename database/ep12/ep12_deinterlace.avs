FFMPEGSource2("A:\mco\inputs\s\s_ep12.mkv", cache=false)
AssumeTFF()
trim(38882, -1)
QTGMC(preset="Slower", TR0=2, TR1=2, \
    EdiMode="EEDI3+NNEDI3", \
    Denoiser="dfttest")
SelectEven()
# aWarpSharp2()
ConvertToRGB24()