FFMPEGSource2("A:\mco\inputs\f\f_ep03.mkv", cache=false)
AssumeTFF()
trim(0, -1)
QTGMC(preset="Slower", TR0=2, TR1=2, \
    EdiMode="EEDI3+NNEDI3", \
    Denoiser="dfttest")
SelectEven()
ConvertToRGB24()

