A:\mco\external\ffmpeg\ffmpeg.exe ^
-i M:\inputs\b\b_ep01_full.mkv ^
-filter_complex "[0:v]nnedi=weights=external/nnedi3/nnedi3_weights.bin:nsize=s8x6:nns=n128:qual=slow:etype=s:pscrn=new3[outv]" ^
-map [outv] ^
-preset slow ^
-c:v hevc_nvenc ^
-profile:v main ^
-pix_fmt yuv420p ^
-b_ref_mode disabled ^
-tag:v hvc1 ^
-g 30 ^
-preset p7 ^
-tune hq ^
-rc constqp ^
-qp 17 ^
-rc-lookahead 20 ^
-spatial_aq 1 ^
-aq-strength 15 ^
-b:v 0 ^
M:\inputs\b\b_ep01_deint.mkv

