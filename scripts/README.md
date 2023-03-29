## Commandes

```
$  python run.py --help
usage: run.py [-h] [--episode EPISODE] [--part {g_debut,precedemment,episode,g_asuivre,asuivre,g_reportage,reportage,g_fin}] [--shot SHOT] [--shot_min SHOT_MIN] [--shot_max SHOT_MAX]
              [--vfilter {deinterlace,pre_upscale,upscale,sharpen,rgb,geometry,final}] [--afilter {extract,final}] [--study] [--frames] [--edition {s0,s,k,a,f,b,c}] [--force]
              [--simulate] [--parse_only] [--regenerate]

Main tool

options:
  -h, --help            show this help message and exit
  --episode EPISODE     Numéro d'épisode de 1 à 39. Ignoré pour la génération des génériques.
  --part {g_debut,precedemment,episode,g_asuivre,asuivre,g_reportage,reportage,g_fin}
                        Partie à générer
  --shot SHOT           debug: numéro du plan à processer
  --shot_min SHOT_MIN   debug: plans à générer: début. NON VERIFIE
  --shot_max SHOT_MAX   debug: plans à processer: fin. NON VERIFIE
  --vfilter {deinterlace,pre_upscale,upscale,sharpen,rgb,geometry,final}
                        debug: applique les filtres video jusqu'à celui spécifié ici (note: final=geometry
  --afilter {extract,final}
                        debug: applique les filtres audio jusqu'à celui spécifié ici
  --study               debug: utilisé pour les études des trames, des filtres, etc. NON VERIFIE
  --frames              debug: utilisé pour les études des trames, des filtres, etc.
  --edition {s0,s,k,a,f,b,c}
                        debug: utilise cette edition pour étude. Ne doit pas être spécifié pour la génération finale. NON VERIFIE
  --force               debug: force. NON VERIFIE
  --simulate            debug: génère les fichiers de concatenation uniquement
  --parse_only          debug: analyse les fichiers de configuration
  --regenerate          debug: regénère les fichier vidéo. NON VERIFIE
```

Exemples:
- Pour vérifier le montage audio/video, l'extraction brute des trames est seulement nécessaire
```
$ python run.py --episode 1 --vfilter deinterlace
```


## Emplacement des fichiers
- Fichiers d'entrée
```
└── inputs
    ├── k  : répertoire contenant les vidéos de l'edition 'k'
    ├── s  : répertoire contenant les vidéos de l'edition 's'
    ├── s0 : répertoire contenant les vidéos de l'edition 's0'
    └── b  : répertoire contenant l'audio de l'edition 'b' (ep01)
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

