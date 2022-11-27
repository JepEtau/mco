# Modifications

**2022-11-27**
- Le générique de fin (1ere version)
```sh
python run.py --part g_fin
```
- Le générique de début est en cours d'étude (i.e. quel plan de quelle édition/plan à utiliser, filtres à améliorer sur certains plans pour éviter l'efft d'escalier
- Le génerique de reportage: filtrage pas trop prononcé (conservation de grain), sinon le
courbes RGB approximatives. Le recadrage ne sera définitif qu'après le reportage de l'ép.1
```sh
python run.py --episode 1 --part g_reportage
```
- Les paramètres a/v de l'épisode 1 ont été vérifiés
```sh
python run.py --episode 1 --vfilter deinterlace
```

**2022-11-07**
- Les paramètres de la base de donnée sont des paramètres non optimisés et ne comportent pas de nombreuses corrections: ils sont utilisés à des fins de tests. Il est donc recommandé d'exécuter la commande `python run.py --episode 1 --vfilter deinterlace` pour vérifier la correcte installation des outils.
