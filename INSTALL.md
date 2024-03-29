# Installations
**Windows 11**

1.  [Arborescence](#Arborescence)
2.  [MCO](#MCO)
3.  [Python](#-Python)
4.  [Modules python](#Modules-python)
5.  [CUDA Toolkit](#CUDA-Toolkit)
6.  [Module python 'PyTorch'](#Module-python-'PyTorch')
7.  [FFMpeg](#FFMpeg)
8.  [MKVmerge](#MKVmerge)
9.  [AviSynth+](#AviSynth+)
10. [Filtres et Plugins Avisynth](#Filtres-et-Plugins-Avisynth)
11. [AnimeSR](#AnimeSR)
12. [Real-CUGAN](#Real-CUGAN)
13. [ESRGAN](#ESRGAN)
14. [Modèles](#Modèles)
<!-- 15. [Vérification de l'installation](#Vérification-de-l-installation)-->

<br/><br/>

## Arborescence
-----------------------------------------
```
D
├── mco
├── mco_3rd_party
```
remarque: ne pas créer le répertoire `mco` car il sera automatiquement créé juste après.
<br/>

## MCO
-----------------------------------------
- [mco](https://github.com/JepEtau/mco)
- Depuis un répertoire (nommé 'D' ci-dessus):
```bash
git clone https://github.com/JepEtau/mco.git
```
<br/>

## Conda
-----------------------------------------
- Miniconda: [Installation](https://docs.conda.io/en/latest/miniconda.html), "Latest Miniconda Installer Links"
- [Managing environments](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html)

```bash
conda create -n mco python=3.11
```

```bash
conda activate mco
```

<br/>


## Modules python
-----------------------------------------

Depuis le répertoire **`mco`**:
```bash
pip install -r requirements.txt
```

<!-- TODO: investigate (requirements for dnn_superres)
```
    pip uninstall opencv-python
    pip uninstall opencv-contrib-python
    pip install opencv-python-rolling==4.7.0.20230211
``` -->


<br/>

## CUDA Toolkit
-----------------------------------------
- Version 11.8
- Téléchargement depuis [NVDIA developper](https://developer.nvidia.com/cuda-11-8-0-download-archive):
    * Operating System: Windows
    * Architecture: x86_64
    * Version: 11
    * Installer Type: exe(local) ou exe(network)

<br/>

## Module python 'PyTorch'
-----------------------------------------
- Version 11.8
- Récupérer la ligne de commande depuis [PyTorch](https://pytorch.org/get-started/locally/)
- Exemple:
    * PyTorch: Stable (2.0.0)
    * OS: Windows
    * Package: Conda
    * Language: Python
    * Compute Platform: Cuda 11.8
- Commande générée à exécuter:
```
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

<br/>

## FFMpeg
-----------------------------------------
- [Téléchargement](https://ffmpeg.org/download.html), "release builds", version 6,  statique

- Installation dans le répertoire **`mco_3rd_party/ffmpeg-6.0-essentials_build`**

remarque: si une version différente ou un réépertoire différent est utilisé, le fichier [directories.ini](./database/directories.ini) devra être modifié

<br/>

## MKVmerge
-----------------------------------------
- [MKVToolNix](https://mkvtoolnix.download)
- Choisir "Installer (64-bits)"

<br/>

## AviSynth+
-----------------------------------------
- https://avs-plus.net/
- version x64


## Filtres et Plugins Avisynth
-----------------------------------------
- [AviSynth](http://avisynth.nl/index.php/Main_Page)
<br/>

**- Si vous n'utilisez pas AviSynth+ par ailleurs:**
- Avant de lancer l'installation, créer l'arboresence suivante (répertoires):
```
mco_3rd_party
├── avisynth_plugins
    ├── plugins
    ├── plugins+
    ├── plugins64
    ├── plugins64+
```
- Lors de l'installation, cocher l'option 'Customize Plugins Paths'. Puis choisir les répertoires créés ci-dessus
<br/>

**- Sinon, vous êtes à même de retrouver les répertoires de plugins**

- Mettre dans le répertoire **`plugins64+`** (choisir les versions x64 pour chaque plugin)
    * ffms2.dll [[FFmpegSource](http://avisynth.nl/index.php/FFmpegSource)]
    * QTGMC.avsi  [[QTGMC](http://avisynth.nl/index.php/QTGMC)]
    * masktools2.dll [[MaskTools2](http://avisynth.nl/index.php/MaskTools2)]
    * DePan.dll, DePanEstimate.dll, mvtools2.dll [[MVTools2](http://avisynth.nl/index.php/MVTools)]
    * nnedi3.dll [[Nnedi3](http://avisynth.nl/index.php/Nnedi3)] (Release_W7_AVX2)
    * RgTools.dll [[RgTools](http://avisynth.nl/index.php/RgTools)]
    * Zs_RF_Shared.avsi [[Zs_RF_Shared](http://avisynth.nl/index.php/Zs_RF_Shared)]
    * eedi3.dll [[EEDI3](http://avisynth.nl/index.php/Eedi3)]
    * aWarpsharpMT.dll [[AWarpSharp2](http://avisynth.nl/index.php/AWarpSharp2)]
    * dfttest.dll [[Dfttest](http://avisynth.nl/index.php/Dfttest)]

<br/>

## AnimeSR
-----------------------------------------
- [AnimeSR](https://github.com/TencentARC/AnimeSR)
- Dans le répertoire **`mco_3rd_party/animeSR`**

Depuis le répertoire **`mco_3rd_party`**:
```bash
# Clone
git clone https://github.com/TencentARC/AnimeSR.git

# Install dependent packages
cd AnimeSR
pip install -r requirements.txt

# Install AnimeSR
python setup.py develop
```
<br/>

## Real-CUGAN
-----------------------------------------
- [Real-CUGAN](https://github.com/bilibili/ailab)

Depuis le répertoire **`mco_3rd_party`**:
```bash
git clone https://github.com/bilibili/ailab.git
```
<br/>

## ESRGAN
-----------------------------------------
- [ESRGAN](https://github.com/JoeyBallentine/ESRGAN)

Depuis le répertoire **`mco_3rd_party`**:
```bash
git clone https://github.com/joeyballentine/ESRGAN.git
```

**Installation**
```bash
cd ESRGAN
pip install --user -r requirements.txt
```

<br/>
<!--
## ~~Real-ESRGAN~~
-----------------------------------------
**!!! Inutilisé: il n'est pas nécessaire de l'installer !!!**
- [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN)-->

<!--Depuis le répertoire **`mco_3rd_party`**:
```bash
git clone https://github.com/xinntao/Real-ESRGAN.git
```

**Installation**
```bash
cd Real-ESRGAN
pip install basicsr
pip install -r requirements.txt
python setup.py develop
```
<br/> -->



## Modèles
-----------------------------------------
[Model Database](https://upscale.wiki/wiki/Model_Database)
[OpenModelDB](https://openmodeldb.info/)

Créer l'arboresence suivante (répertoires):
```
mco_3rd_party
├── models
    ├── animesr
    ├── pytorch
    ├── real_cugan
    ├── scunet
```

- Dans le répertoire `animesr`
    * AnimeSR_v2.pth [[Google Drive](https://drive.google.com/drive/folders/1gwNTbKLUjt5FlgT6PQQnBz5wFzmNUX8g?usp=share_link)]

<br/>
<!--
- Dans le répertoire `dnn_superres`
    * EDSR_x2.pb [[github](https://github.com/Saafke/EDSR_Tensorflow/tree/master/models)]
    * FSRCNN_x2 [[github](https://github.com/Saafke/FSRCNN_Tensorflow/tree/master/models)] -->

- Dans le répertoire `pytorch`, depuis [OpenModelDB/](https://openmodeldb.info/)
    * 2x_LD-Anime_Skr_v1.0.pth [[Model Database](https://upscale.wiki/wiki/Model_Database#Anime_and_Cartoons)]
    * 1x_HurrDeblur_SuperUltraCompact_nf24-nc8_244k_net_g.pth
    * 2xESRGAN.pth [[Model Database](https://upscale.wiki/wiki/Model_Database#Pretrained_Models)]
    * realesr-animevideov3.pth
    * 2x_LD-Anime_Compact_330k_net_g.pth
    * 1x_BeaverIt.pth


<br/>

- Dans le répertoire `real_cugan`: [updated_weights.zip](https://github.com/bilibili/ailab/releases/tag/Real-CUGAN)
    * up2x-latest-conservative.pth
    * up2x-latest-denoise1x.pth
    * up2x-latest-denoise2x.pth
    * up2x-latest-denoise3x.pth
    * up2x-latest-no-denoise.pth

<br/>

- Dans le répertoire `scunet`:
    * [scunet_color_real_gan](https://github.com/cszn/KAIR/releases/download/v1.0/scunet_color_real_gan.pth)
    * [scunet_color_real_psnr.pth](https://github.com/cszn/KAIR/releases/download/v1.0/scunet_color_real_psnr.pth)

