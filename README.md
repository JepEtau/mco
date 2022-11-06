# mco

## Exigences et installations

- Python 3.10
- Modules python
    * numpy
    * opencv-python
    * scikit-image

    ```sh
    $ cd scripts
    $ pip install -r requirements.txt
    ```
- mkvmerge: [MKVToolNix](https://mkvtoolnix.download)
- [FFmpeg](https://ffmpeg.org), version > 5.0
- [nnedi3_weights.bin](https://github.com/dubhater/vapoursynth-nnedi3/blob/master/src/) à copier dans le répertoire `scripts`: https://github.com/dubhater/vapoursynth-nnedi3/tree/master/src


## Fichiers video d'entrée
A stocker dans les répertoires suivants:
- Edition 'k': [mkv/576p/k](./mkv/576p/k/README.md)
- Edition 's': [mkv/576p/s](./mkv/576p/s/README.md)
- Edition 'a': [mkv/576p/a](./mkv/576p/a/README.md)

## Commandes
Exécuter les commandes suivantes dans le répertoire `scripts`:
```sh
$ python run.py --episode 1
```

[Plus de commandes ici](./scripts/README.md)
