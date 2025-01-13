

# ep01 s6 (pluie)
ep01_episode_006__j__resize+up2x-latest-denoise2x+resize+scunet_color_real_gan+darker_thinner
    celui qui conserve la pluie mais nez mal défini
    oversharping mais pluie ok

ep01_episode_006__j__scunet_color_real_gan+resize+2x_ModernSpanimationV2+resize+darker_thinner
    mieux défini mais pluie trop fine


ep01_episode_006__j__scunet_color_real_gan+resize+pro-conservative-up2x+resize+darker_thinner
    meilleur que denoise 2x

ep01_episode_006__j__resize+2x-DigitalFilmV5-Lite+resize+scunet_color_real_gan+darker_thinner
    bruité mais qui donne un aspect de pluie plus agréable
    finalemenent plus flou que pro_conservative

ep01_episode_006__j__resize+LDVDeNoise_35mm_Compact+resize+scunet_color_real_gan+darker_thinner
chaine cou mal définie


ep01_episode_006__j__pro-conservative-up2x+scunet_color_real_gan+darker_thinner
    nouvelle référence



- scunet avent upscale floute trop
- resize avant upscale floute et rend les traits mal définis
- pro_conservative avant denoise
- léger darker_thinner



# ep01 s63

ep01_episode_063__j__pro-conservative-up2x+scunet_color_real_gan+darker_thinner
    lignes doubles, lignes qui bavent

ep01_episode_063__j__resize+2x_Pooh_V4_Candidate_2_422k+resize+scunet_color_real_gan+darker_thinner
    aliasing, color shift
    trop de grain

ep01_episode_063__j__resize+LDVDeNoise_35mm_Compact+resize+gaussian_noise+scunet_color_real_gan+darker_thinner
le meilleur

ep01_episode_063__j__2x_Pooh_V4_Candidate_2_422k+scunet_color_real_gan+darker_thinner_0.6_0.
    meilleur que s'il y a un resize avant

ep01_episode_063__j__resize+LDVDeNoise_35mm_Compact+resize+scunet_color_real_gan+darker_thinner_1.0_0.2
    reference même si double ligne sur yeux

- darker_thinner=1.0:0.2;


# ep01 s161
ep01_episode_161__j__resize+LDVDeNoise_35mm_Compact+resize+scunet_color_real_gan+darker_thinner
    flou, trop de traits perdus

ep01_episode_161__j__resize+2x_Pooh_V4_Candidate_2_422k+resize+scunet_color_real_gan+darker_thinner
    trop sharp: vagues artificielles


ep01_episode_161__j__pro-conservative-up2x+scunet_color_real_gan+darker_thinner_1.0_0.1
    meilleur

- darker thiner: trop fins
- resize avant pro_conservative floute et rend les traits mal définis


# ep01 s023
ep01_episode_023__j__resize+LDVDeNoise_35mm_Compact+resize+scunet_color_real_gan+darker_thinner_1.0_0.2
    temporal artifacts

ep01_episode_023__j__pro-conservative-up2x+scunet_color_real_gan+darker_thinner_1.0_0.1
    trop de détails


ep01_episode_023__j__resize+2x-DigitalFilmV5-Lite+resize+scunet_color_real_gan+darker_thinner_0.6_0.+unsharp
    reference

ep01_episode_023__j__resize+pro-conservative-up2x+resize+scunet_color_real_gan+darker_thinner_0.6_0
    trop de défauts temporels même après tf

ep01_episode_023__j__2x_Pooh_V4_Candidate_2_422k+scunet_color_real_gan+darker_thinner_1_0.
    trop d'artefacts temporels

- ajouter +0.2 en brightness n'améliore pas


- resize avant digitalfilm enlève mieux les défauts sans trop enlever les détails: celà permet d'éviter des artéfacts temporels


- scène 4: f=d: darker 0.6 -> 0.8 risque d'artéfacts de couleurs (s129 à tester?)


# ep01 s9
ld_anime skr > dv5
scunet+pooh

resize/pooh/resize moins bon que sans resize

scunet avant ld est meilleur qu'après

2x_Pooh_V4_Candidate fait très artificiel même si l'affiche est nettement meilleure

- 1x_Anime1080Fixer_SuperUltraCompact est très intéressant
