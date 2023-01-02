# MCO

## Modifications et progressions
- [Fiche d'avancement](./progress.md)
- [Fiche de modifications](./modifications.md) (pas forcément toujours à jour)

## Exigences et installations
(Se référer au dépôt [mco_manuel](https://github.com/JepEtau/mco_manuels) pour quelques informations supplémentaires concernant l'installation)

- Python **3.10** (< 3.11)
- Modules python
    * numpy
    * opencv-python
    * scikit-image

    ```sh
    cd scripts
    pip install -r requirements.txt
    ```
- mkvmerge: [MKVToolNix](https://mkvtoolnix.download)
- [FFmpeg](https://ffmpeg.org), version 5.1, à placer dans le répertoire `ffmpeg-5.1`
- [nnedi3_weights.bin](https://github.com/dubhater/vapoursynth-nnedi3/blob/master/src/) à copier dans le répertoire `scripts`: https://github.com/dubhater/vapoursynth-nnedi3/tree/master/src

Il est possible de modifier l'emplacement de certains répertoires en éditant le fichier [directories.ini](./database/directories.ini)
<br/><br/>

## Fichiers video d'entrée
A stocker dans les répertoires suivants:
- Edition 'k': [mkv/576p/k](./mkv/576p/k/README.md)
- Edition 's': [mkv/576p/s](./mkv/576p/s/README.md) (ep 1, 2, 11, 12)
- Optionnel: édition 'a': [mkv/576p/a](./mkv/576p/a/README.md) qui sera utilisée ultérieurement
<br/><br/>
- Etudes: édition 'f': [mkv/576p/d](./mkv/576p/d/README.md) qui sert juste pour des comparaisons
<br/><br/>

## Commandes
Exécuter les commandes suivantes dans le répertoire `scripts` pour générer l'ensemble de la vidéo en version finale:
```sh
python run.py --episode 1
```

Notes:
- 2022-11-27: Le générique de fin (1ere version)
```sh
python run.py --part g_debut
```
- 2022-11-07: Les paramètres de la base de donnée sont des paramètres non optimisés et ne comportent pas de nombreuses corrections: ils sont utilisés à des fins de tests. Il est donc recommandé d'exécuter la commande `python run.py --episode 1 --vfilter deinterlace` pour vérifier la correcte installation des outils.

[Plus de commandes...](./scripts/README.md)
<br/><br/>


# Implémentation et documentation
N'ayant qu'un temps limité, vu l'ampleur du projet, et que j'avais commencé ce projet pour mon usage personnel:
- J'utilise de nombreux anglicismes, ne maîtrisant pas les termes techniques en français (et ne voulant pas, c'est une véritable torture).
- De nombreux commentaires sont, soit en français, soit en anglais, soit en très mauvais anglais selon la température ambiante, la phase lunaire, mon humeur, le temps que j'ai à consacrer, etc.
- De même, l'implémentation est tantôt propre, tantôt pas pythonique pour un sou(ce n'est pas mon language de développement habituel). De nombreuses parties seraient à re-travailler, optimiser, mais je n'ai pas le temps.
- Je n'ai pas cherché à optimiser de nombreuses fonctions pour obtenir des résultats rapides. La plupart ne sont pas des fonctions critiques en terme de temps de processing.
<br/><br/>

# Clause de non responsabilité
Se référer au paragraphe 11 et 12 de la licence attachée au projet (GPL v2). Une traduction non officielle est disponible sur le site de l'[APRIL](https://www.april.org/gnu/gpl_french.html) à titre d'information.
<br/><br/>

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
