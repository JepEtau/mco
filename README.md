
# Exigences
- Windows 11
- RAM: minimum 16GB (32GB recommandés)
- SSD ou HDD: taille des vidéo d'entrée + 300GB par épisode (génération)
- Carte Graphique NVIDIA (CUDA)
- Editions F, K, S (en partie, voir ci-dessous), B (optionnel)
- Quelques heures par épisode (selon le CPU et la carte graphique)
<br/><br/>

# Installations
[Etapes](./INSTALL.md)
<br/><br/>


# Fichiers video d'entrée
A stocker dans les répertoires suivants:
- Edition 'f': [inputs/f](./inputs/f/README.md)
- Edition 'k': [inputs/k](./inputs/k/README.md)
- Edition 's': [inputs/s](./inputs/s/README.md) (épisode no. 2, 11, 12)
- Edition 'b': [inputs/b](./inputs/b/README.md) (épisode no. 1 (audio))

EN: for the english version, 'f' is the only required edition
<br/><br/>


# Utilisation
Une fois les installations et les fichiers d'entrée ajoutés à ce projet, exécuter la commande suivante pour tester l'installation des modules python:
```bash
# FR
python run.py --episode 1 --parse_only
# EN
python run.py --episode 1 --parse_only --lang en
```

Pour tester le montage video, utilisation des trames désentrelacées:
```bash
# FR
python run.py --episode 1 --parse_only
# EN
python run.py --episode 1 --parse_only --lang en
```

EN: To avoid using the `--lang en` argument every time, create an empty file named `en` in the `./database` directory

**Pour générer la version finale de l'épisode 1**<br/>
(2023-06-29: ne fonctionne pas correctement, dev. en cours)
```sh
python run.py --episode 1
```

[Plus de commandes...](./usage.md)
<br/><br/>


# Clause de non responsabilité
Se référer au paragraphe 11 et 12 de la licence attachée au projet (GPL v2). Une traduction non officielle est disponible sur le site de l'[APRIL](https://www.april.org/gnu/gpl_french.html) à titre d'information.
<br/><br/>


# Credits
* [AnimeSR](https://github.com/TencentARC/AnimeSR)
* [AviSynth+](https://avs-plus.net/) and Scripts/Plugins
* [ESRGAN (joeyballentine)](https://github.com/JoeyBallentine/ESRGAN)
* [FFmpeg](https://ffmpeg.org)
* [GIMP](https://www.gimp.org) (gimp/app/core/gimpcurve.c)
* [Lucide](https://lucide.dev)
* [MKVToolNix](https://mkvtoolnix.download)
* [nnedi3](https://github.com/dubhater)
* [NumPy](https://numpy.org/)
* [NVIDIA](https://www.nvidia.com)
* [OpenCV](https://opencv.org/)
* [Python](https://www.python.org/)
* [PySoundFile](https://pysoundfile.readthedocs.io)
* [Qt Group](https://www.qt.io), [PySide 6](https://pypi.org/project/PySide6)
* [Real-CUGAN](https://github.com/bilibili/ailab)
* [Visual Studio Code](https://code.visualstudio.com/)
* [chaiNNer](https://github.com/chaiNNer-org/chaiNNer)
