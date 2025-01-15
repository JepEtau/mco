copy /b "VTS_01_1.VOB"+"VTS_01_2.VOB"+"VTS_01_3.VOB"+"VTS_01_4.VOB"+"VTS_01_5.VOB"+"VTS_01_6.VOB"+"VTS_01_7.VOB"+"VTS_01_8.VOB" "output.vob"


cls; python .\pynference.py --input D:\mco\cache\progressive\f_ep01_c37d117.mkv --output A:\video\output\ep01_2.46_80_2x-LD-Anime-Compact.mkv --model A:\ml_models\2x-LD-Anime-Compact.pth --ss 2:46 -t 80 --trt --fp16



cls; python .\pynference.py --input D:\mco\cache\progressive\f_ep01_c37d117.mkv --output A:\video\output\ep01_2.46_80_2x_Pooh_V4_Candidate_2_422k.mkv --model A:\ml_models\2x_Pooh_V4_Candidate_2_422k.pth --ss 2:46 -t 80 --trt --fp16

cls; python .\pynference.py --input D:\mco\cache\progressive\f_ep01_c37d117.mkv --output A:\video\output\ep01_2.46_80_2x_Pooh_V4_Candidate_2_422k.mkv --model A:\ml_models\2x_Pooh_V4_Candidate_2_422k.pth --ss 2:46 -t 80 --trt --fp16




cls; python .\pynference.py --input A:\mco\inputs\j\j_ep01.mkv --output A:\mco\outputs\j_ep01_2x-LD-Anime-Compact.mkv --model A:\ml_models\2x-LD-Anime-Compact.pth --trt --fp16


cls; python .\pynference.py --input A:\mco\inputs\j\j_ep01.mkv --output A:\mco\outputs\j_ep01_downscale_2x-LD-Anime-Compact_upscale.mkv --model A:\ml_models\2x-LD-Anime-Compact.pth --trt --fp16 --initial_scale 0.5 --final_resize 1440x960


# qtgmc vs nnedi vs yadif
cls; python .\pynference.py --input D:\mco\cache\progressive\f_ep01_c37d117.mkv --output A:\video\output\ep01_2.46_80_2x_Pooh_V4_Candidate_2_422k.mkv --model A:\ml_models\2x_Pooh_V4_Candidate_2_422k.pth --ss 2:46 -t 80 --trt --fp16


cls; python .\pynference.py --input D:\mco\cache\progressive\f_ep01_nnedi_be1a5da.mkv --output A:\video\output\ep01_2.46_80_nnedi_2x_Pooh_V4_Candidate_2_422k.mkv --model A:\ml_models\2x_Pooh_V4_Candidate_2_422k.pth --ss 2:46 -t 80 --trt --fp16


cls; python .\pynference.py --input D:\mco\cache\progressive\f_ep01_yadif_ab6a8cc.mkv --output A:\video\output\ep01_2.46_80_yadif_2x_Pooh_V4_Candidate_2_422k.mkv --model A:\ml_models\2x_Pooh_V4_Candidate_2_422k.pth --ss 2:46 -t 80 --trt --fp16




# Compare models for Japanese edition

cls; python .\pynference.py --input A:\mco\inputs\j\j_ep01.mkv --output A:\mco\outputs\j_ep01_3.32_80_pro-conservative-up2x.mkv --model A:\ml_models\real_cugan\pro-conservative-up2x.pth --trt --fp16 --ss 3:32 --t 80

cls; python .\pynference.py --input A:\mco\inputs\j\j_ep01.mkv --output A:\mco\outputs\j_ep01_3.32_80_2x_Pooh_V4_Candidate_2_422k.mkv --model A:\ml_models\2x_Pooh_V4_Candidate_2_422k.pth --trt --ss 3:32 --t 80 --fp16


cls; python .\pynference.py --input A:\mco\inputs\j\j_ep01.mkv --output A:\mco\outputs\j_ep01_3.32_80_2x-LD-Anime-Compact.mkv --model A:\ml_models\2x-LD-Anime-Compact.pth --trt --ss 3:32 --t 80 --fp16


cls; python .\pynference.py --input A:\mco\inputs\j\j_ep01.mkv --output A:\mco\outputs\j_ep01_3.32_80_pro-denoise3x-up2x.mkv --model A:\ml_models\real_cugan\pro-denoise3x-up2x.pth --trt --fp16 --ss 3:32 --t 80


cls; python .\pynference.py --input A:\mco\inputs\j\j_ep01.mkv --output A:\mco\outputs\j_ep01_3.32_80_scunet_color_real_gan.mkv --model A:\ml_models\scunet_color_real_gan.pth --cuda --ss 3:32 --t 100 --fp16

python .\pynference.py --input A:\mco\outputs\j_ep01_3.32_80_scunet_color_real_gan.mkv --output A:\mco\outputs\j_ep01_3.32_80_scunet_color_real_gan_2x-LD-Anime-Compact.mkv --model A:\ml_models\2x-LD-Anime-Compact.pth --trt --fp16


cls; python .\pynference.py --input A:\mco\inputs\j\j_ep01.mkv --output A:\mco\outputs\j_ep01_3.32_80_2x_NGE_RealPLKSR.mkv --model A:\ml_models\2x_NGE_RealPLKSR.pth --trt --fp16 --ss 3:32 --t 80


cls; python .\pynference.py --input A:\mco\inputs\j\j_ep01.mkv --output A:\mco\outputs\j_ep01_3.32_80_2x-Futsuu-Anime.mkv --model A:\ml_models\2x-Futsuu-Anime.pth --trt --fp16 --ss 3:32 --t 80



cls; python .\pynference.py --input A:\mco\outputs\j_ep01_3.32_80_2x-LD-Anime-Compact.mkv --output A:\mco\outputs\j_ep01_3.32_80_2x-LD-Anime-Compact_scunet_color_real_gan.mkv --model A:\ml_models\scunet_color_real_gan.pth --cuda


cls; python .\pynference.py --input A:\mco\inputs\j\j_ep01.mkv --output A:\mco\outputs\j_ep01_3.32_80_2x_Pooh_V4_Candidate_1_396k.mkv --model A:\ml_models\2x_Pooh_V4_Candidate_1_396k.pth --trt --ss 3:32 --t 80 --fp16


cls; python .\pynference.py --input A:\mco\inputs\j\j_ep01.mkv --output A:\mco\outputs\j_ep01_3.32_80_pro-no-denoise-up2x.mkv --model A:\ml_models\real_cugan\pro-no-denoise-up2x.pth --trt --fp16 --ss 3:32 --t 80


cls; python .\pynference.py --input A:\mco\inputs\j\j_ep01.mkv --output A:\mco\outputs\j_ep01_3.32_80_2x_LD-Anime_Skr_v1.0.mkv --model A:\ml_models\2x_LD-Anime_Skr_v1.0.pth --trt --fp16 --ss 3:32 --t 80

cls; python .\pynference.py --input A:\mco\outputs\j_ep01_3.32_80_2x_LD-Anime_Skr_v1.0.mkv --output A:\mco\outputs\j_ep01_3.32_80_2x_LD-Anime_Skr_v1.0_scunet_color_real_gan.mkv --model A:\ml_models\scunet_color_real_gan.pth --cuda --fp16



cls; python .\pynference.py --input D:\mco\cache\progressive\f_ep01_c37d117.mkv --output A:\video\output\ep01_2.26_80_2x_Pooh_V4_Candidate_2_422k.mkv --model A:\ml_models\2x_Pooh_V4_Candidate_2_422k.pth --ss 2:26 -t 80 --trt --fp16



cls; python .\pynference.py --input A:\mco\inputs\j\j_ep01.mkv --output A:\mco\outputs\j_ep01_3.32_80_2x_LD-Anime_Skr_v1.0.mkv --model A:\ml_models\2x_LD-Anime_Skr_v1.0.pth --trt --fp16 --ss 3:32 --t 80


cls; python .\pynference.py --input D:\mco\cache\progressive\j_ep01_7e784ec.mkv --output A:\mco\outputs\j_ep01_xxxx_scunet_color_real_gan.mkv --model A:\ml_models\scunet_color_real_gan.pth --cuda --fp16


cls; python .\pynference.py --input A:\mco\outputs\j_ep01_3.32_80_scunet_color_real_gan.mkv --output A:\mco\outputs\j_ep01_3.32_80_scunet_color_real_gan_2x-DigitalFilmV5-Lite.mkv --model A:\ml_models\2x-DigitalFilmV5-Lite.pth  --trt --fp16



cls; python .\pynference.py --input A:\mco\inputs\j\j_ep01.mkv --output A:\mco\outputs\j_ep01_3.32_80_2x-DigitalFilmV5-Lite.mkv --model A:\ml_models\2x-DigitalFilmV5-Lite.pth --trt --ss 3:32 --t 100 --fp16


cls; python .\pynference.py --input A:\mco\outputs\j_ep01_xxxx_scunet_color_real_gan.mkv --output A:\mco\outputs\j_ep01_xxxx_scunet_color_real_gan_2x-DigitalFilmV5-Lite.mkv --model A:\ml_models\2x-DigitalFilmV5-Lite.pth --trt --fp16



cls; python .\pynference.py --input D:\mco\cache\progressive\j_ep01_7e784ec.mkv --output A:\mco\outputs\j_ep01_xxxx_2x-DigitalFilmV5-Lite.mkv --model A:\ml_models\2x-DigitalFilmV5-Lite.pth --trt --fp16


cls; python .\pynference.py --input A:\mco\outputs\j_ep01_xxxx_2x-DigitalFilmV5-Lite.mkv --output A:\mco\outputs\j_ep01_xxxx_2x-DigitalFilmV5-Lite_scunet_color_real_gan.mkv --model A:\ml_models\scunet_color_real_gan.pth --cuda --fp16


# jp editions: ep01

cls; python .\pynference.py --input D:\mco\cache\progressive\j_ep01_7e784ec_vob.mkv --output A:\mco\outputs\j_ep01_7e784ec_vob_scunet_color_real_gan.mkv --model A:\ml_models\scunet_color_real_gan.pth --cuda --fp16 --ss 3:06 --t 1:40
cls; python .\pynference.py --input A:\mco\outputs\j_ep01_7e784ec_vob_scunet_color_real_gan.mkv --output A:\mco\outputs\j_ep01_7e784ec_vob_scunet_color_real_gan_2x-DigitalFilmV5-Lite.mkv --model A:\ml_models\2x-DigitalFilmV5-Lite.pth --trt --fp16


cls; python .\pynference.py --input D:\mco\cache\progressive\j_ep01_7e784ec_mpg.mkv --output A:\mco\outputs\j_ep01_7e784ec_mpg_scunet_color_real_gan.mkv --model A:\ml_models\scunet_color_real_gan.pth --cuda --fp16 --ss 0:54 --t 1:30
cls; python .\pynference.py --input A:\mco\outputs\j_ep01_7e784ec_mpg_scunet_color_real_gan.mkv --output A:\mco\outputs\j_ep01_7e784ec_mpg_scunet_color_real_gan_2x-DigitalFilmV5-Lite.mkv --model A:\ml_models\2x-DigitalFilmV5-Lite.pth --trt --fp16


# jp editions: ep06
cls; python .\pynference.py --input D:\mco\cache\progressive\j_ep06_7e784ec_vob.mkv --output A:\mco\outputs\j_ep06_7e784ec_vob_scunet_color_real_gan.mkv --model A:\ml_models\scunet_color_real_gan.pth --cuda --fp16 --ss 3:06 --t 1:40
cls; python .\pynference.py --input A:\mco\outputs\j_ep06_7e784ec_vob_scunet_color_real_gan.mkv --output A:\mco\outputs\j_ep06_7e784ec_vob_scunet_color_real_gan_2x-DigitalFilmV5-Lite.mkv --model A:\ml_models\2x-DigitalFilmV5-Lite.pth --trt --fp16


cls; python .\pynference.py --input D:\mco\cache\progressive\j_ep06_7e784ec_mpg.mkv --output A:\mco\outputs\j_ep06_7e784ec_mpg_scunet_color_real_gan.mkv --model A:\ml_models\scunet_color_real_gan.pth --cuda --fp16 --ss 0:54 --t 1:30
cls; python .\pynference.py --input A:\mco\outputs\j_ep06_7e784ec_mpg_scunet_color_real_gan.mkv --output A:\mco\outputs\j_ep06_7e784ec_mpg_scunet_color_real_gan_2x-DigitalFilmV5-Lite.mkv --model A:\ml_models\2x-DigitalFilmV5-Lite.pth --trt --fp16



ffmpeg -ss 0:22:58.760 -i D:\mco\cache\progressive\k_ep17_c37d117.mxf  -t 10.64 -c:v copy D:\mco\cache\g_doc\k_ep17_g_doc.mxf -y


ffmpeg -ss 0:23:00 -i A:\mco\inputs\b\b_ep01_video.mkv  -t 2:50 -c:v hevc_nvenc -profile:v main -pix_fmt yuv420p -b_ref_mode disabled -tag:v hvc1 -g 30 -preset p7 -tune hq -rc constqp -qp 17 -rc-lookahead 20 -spatial_aq 1 -aq-strength 15 -b:v 0 -an -sn b_ep01_doc.mkv -y


1378,76
22:58.76
266 -> 10,64



ffmpeg -i N:\cache\ep01\upscale\episode\ep01_episode_009__f_009_scunet_color_real_gan+2x_LD-Anime_Skr_v1.0+1x_Anime1080Fixer_SuperUltraCompact+darker_thinner_0.8_0.3_REF.mkv -i N:\cache\ep01\upscale\episode\ep01_episode_009__f_009_2x_Pooh_V4_Candidate_2_422k+scunet_color_real_gan+1x_Anime1080Fixer_SuperUltraCompact.mkv -filter_complex [0:v][1:v]blend=all_mode='overlay':all_opacity=0.7[outv] -map [outv] -vcodec hevc_nvenc -profile:v main -b_ref_mode disabled -tag:v hvc1 -g 30 -preset p7 -tune hq -rc constqp -qp 17 -rc-lookahead 20 -spatial_aq 1 -aq-strength 15 -b:v 0 -pix_fmt yuv420p -color_range limited -y N:\cache\ep01\upscale\episode\blended.mkv


cls; ffmpeg -i N:\cache\ep01\upscale\episode\ep01_episode_009__f_009_scunet_color_real_gan+2x_LD-Anime_Skr_v1.0+1x_Anime1080Fixer_SuperUltraCompact+darker_thinner_0.8_0.3_REF.mkv -i N:\cache\ep01\upscale\episode\ep01_episode_009__f_009_2x_Pooh_V4_Candidate_2_422k+scunet_color_real_gan+1x_Anime1080Fixer_SuperUltraCompact.mkv -filter_complex "[0:v]format=yuva444p,colorchannelmixer=aa=0.5[in0];[1:v]format=yuva444p,colorchannelmixer=aa=0.5[in1];[in0][in1]overlay[outv]" -map [outv] -vcodec hevc_nvenc -profile:v main -b_ref_mode disabled -tag:v hvc1 -g 30 -preset p7 -tune hq -rc constqp -qp 17 -rc-lookahead 20 -spatial_aq 1 -aq-strength 15 -b:v 0 -pix_fmt yuv420p -color_range limited -y N:\cache\ep01\upscale\episode\blended_0.5.mkv



cls; ffmpeg -i N:\cache\ep01\upscale\episode\ep01_episode_020__f_020_2x_Pooh_V4_Candidate_2_422k+scunet_color_real_gan+1x_Anime1080Fixer_SuperUltraCompact.mkv -i N:\cache\ep01\upscale\episode\ep01_episode_020__f_020_scunet_color_real_gan+2x_LD-Anime_Skr_v1.0+1x_Anime1080Fixer_SuperUltraCompact+darker_thinner_0.8_0.3.mkv -filter_complex "[0:v]format=yuva444p,colorchannelmixer=aa=0.5[in0];[1:v]format=yuva444p,colorchannelmixer=aa=0.5[in1];[in0][in1]overlay[outv]" -map [outv] -vcodec hevc_nvenc -profile:v main -b_ref_mode disabled -tag:v hvc1 -g 30 -preset p7 -tune hq -rc constqp -qp 17 -rc-lookahead 20 -spatial_aq 1 -aq-strength 15 -b:v 0 -pix_fmt yuv420p -color_range limited -y N:\cache\ep01\upscale\episode\020_blended_0.5.mkv
