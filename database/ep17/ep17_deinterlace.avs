FFMPEGSource2("A:\mco\inputs\k\k_ep17.mkv", cache=false, overwrite=true)
trim(34469, -1)
QTGMC(preset="Slower", \
    TR0=2, TR1=2, \
    EdiMode="EEDI3+NNEDI3", \
    Denoiser="dfttest")
SelectEven()
# aWarpSharp2()
ConvertToRGB24()