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
