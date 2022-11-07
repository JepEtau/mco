# mco

## Exigences et installations
(Se référer au dépôt [mco_manuel](https://github.com/JepEtau/mco_manuels) pour quelques informations supplémentaires concernant l'installation)

- Python **3.10** (< 3.11)
- Modules python
    * numpy
    * opencv-python
    * scikit-image

    ```sh
    $ cd scripts
    $ pip install -r requirements.txt
    ```
- mkvmerge: [MKVToolNix](https://mkvtoolnix.download)
- [FFmpeg](https://ffmpeg.org), version >= 5.1
- [nnedi3_weights.bin](https://github.com/dubhater/vapoursynth-nnedi3/blob/master/src/) à copier dans le répertoire `scripts`: https://github.com/dubhater/vapoursynth-nnedi3/tree/master/src


## Fichiers video d'entrée
A stocker dans les répertoires suivants:
- Edition 'k': [mkv/576p/k](./mkv/576p/k/README.md)
- Edition 's': [mkv/576p/s](./mkv/576p/s/README.md)
- Optionnel: édition 'a': [mkv/576p/a](./mkv/576p/a/README.md) qui sera utilisée ultérieurement

## Commandes
Exécuter les commandes suivantes dans le répertoire `scripts`:
```sh
$ python run.py --episode 1
```

[Plus de commandes...](./scripts/README.md)

# Clause de non responsabilité
Se référer au paragraphe 11 et 12 de la licence attachée au projet (GPL v2). Une traduction non officielle est disponible sur le site de l'[APRIL](https://www.april.org/gnu/gpl_french.html) à titre d'information

# Remerciements
- Projets:
    * Debian developers
    * FFMPEG
    * GIMP (gimp/app/core/gimpcurve.c)
    * lucide.dev
    * Microsoft (Visual Studio Code)
    * MKVToolNix
    * nnedi3 authors
    * NumPy
    * OpenCV
    * Python
    * Qt Group
    * Scikit-image
