## Commandes

```
$  python run.py --help
usage: run.py [-h] [--episode EPISODE] [--edition {k,a,s}] [--part {g_debut,precedemment,episode,g_asuivre,asuivre,g_reportage,reportage,g_fin}]
              [--vfilter {deinterlace,pre_upscale,upscale,denoise,bgd,combine,sharpen,rgb,final}] [--afilter {extract,final}] [--study] [--frames] [--compare] [--force]
              [--simulate] [--parse_only]

Main tool

options:
  -h, --help            show this help message and exit
  --episode EPISODE     Numéro d'épisode de 1 à 39. Ignoré pour la génération des génériques.
  --edition {k,a,s}     Utilise uniquement cette edition
  --part {g_debut,precedemment,episode,g_asuivre,asuivre,g_reportage,reportage,g_fin}
                        Partie à traiter
  --vfilter {deinterlace,pre_upscale,upscale,denoise,bgd,combine,sharpen,rgb,final}
                        Applique les filtres video jusqu'à celui spécifié ici
  --afilter {extract,final}
                        Applique les filtres audio jusqu'à celui spécifié ici
  --study               Utilisé pour les études des trames, des filtres, etc.
  --frames              Utilisé pour les études des trames, des filtres, etc.
  --compare             debug: utilisé pour comparer les éditions (non fonctionnel)
  --force               debug: force
  --simulate            debug: do not générate a/v files, generate concatenation files only
  --parse_only          debug: parse only the database

```

Exemples:
- Pour vérifier le montage audio/video, l'extraction brute des trames est seulement nécessaire
```
$ python run.py --episode 1 --vfilter deinterlace
```


## Emplacement des fichiers
- Fichiers d'entrée
```
└── mkv
    └── 576p
          ├── k : répertoire contenant les vidéo de l'edition 'k'
          ├── s : répertoire contenant les vidéo de l'edition 's'
          └── a : répertoire contenant les vidéo de l'edition 'a'
```

- Fichiers générés
```
├── cache
│   ├── ep01
│   │   ├── audio           : fichiers audio pour l'épisode (extrait, │inalisé)
│   │   ├── concatenation   : fichiers pour la concaténation des images/video
│   │   ├── video           : fichiers video
│   │   ├── ...
│   │   ├── ep01_audio_video.mkv : concatenation des fichiers audio/video │ans│génériques de début/fin
│   │   ├── ep01_full.mkv   : concatenation de tous les fichiers audio/video
│   │   └── ep01.mkv        : fichier final (avec les chapitres)
│

```

