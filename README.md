# MCO

## Exigences et installations
- Python **3.10** (< 3.11)
- Modules Python
- mkvmerge: [MKVToolNix](https://mkvtoolnix.download)
- [FFmpeg](https://ffmpeg.org)
- [AviSynth](https://avisynth.nl)
- Filtres et plugin AviSynth
- [FFmpeg](https://ffmpeg.org)
- [Real-CUGAN](https://github.com/bilibili/ailab/tree/main/Real-CUGAN)
- [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN)
- [ESRGAN](https://github.com/JoeyBallentine/ESRGAN)
- Modèles pour Real-ESRGAN, ESRGAN
- (optionnel: [nnedi3_weights.bin](https://github.com/dubhater/vapoursynth-nnedi3/blob/master/src/))
<br/><br/>

## Fichiers video d'entrée
A stocker dans les répertoires suivants:
- Edition 'f': [inputs/k](./inputs/k/README.md)
- Edition 'k': [inputs/k](./inputs/k/README.md)
- Edition 's': [inputs/s](./inputs/s/README.md) (ep 1, 2, 11, 12)
- Edition 's0': [inputs/s0](./inputs/s0/README.md) (ep 1)
- Edition 'b': [inputs/b](./inputs/b/README.md) (ep 01 audio)
<br/><br/>

## Commandes
Exécuter les commandes suivantes dans le répertoire `scripts` pour générer l'ensemble de la vidéo en version finale:
```sh
python run.py --episode 1
```

[Plus de commandes...](./scripts/README.md)
<br/><br/>

# Clause de non responsabilité
Se référer au paragraphe 11 et 12 de la licence attachée au projet (GPL v2). Une traduction non officielle est disponible sur le site de l'[APRIL](https://www.april.org/gnu/gpl_french.html) à titre d'information.
<br/><br/>

# Remerciements
- Auteurs des projets:
    * Debian
    * FFmpeg
    * GIMP (gimp/app/core/gimpcurve.c)
    * lucide.dev
    * Microsoft (Visual Studio Code), Windows 11
    * MKVToolNix
    * nnedi3
    * NumPy
    * OpenCV
    * Python
    * Qt Group
    * Scikit-image
    * AviSynth
    * Scripts/plugins AviSynth
    * Real-CUGAN
    * Real-ESRGAN
    * ESRGAN
    * Modèles pour Real-ESRGAN, ESRGAN
