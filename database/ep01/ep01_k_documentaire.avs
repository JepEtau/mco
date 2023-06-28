FFMPEGSource2("A:\mco\cache\progressive\k_ep01_3e2c47c.mkv", cache=false)
trim(0, -1)
ConvertToYUV420()

spline36resize(Width*2, Height*2)
aWarpSharp2()


ConvertToRGB24()
