# mco

## Exigences et installations

- Python >= 3.10.2
- Modules python
    * numpy
    * opencv-python
    * scikit-image
    * PySide6

    ```sh
    $ cd tools
    $ pip install -r requirements.txt
    ```

## Commandes
- Viewer
    + Lecteur d'images stockées dans le répertoire `frames`
    + Exécuter la commande suivante dans le répertoire `tools`:
    ```sh
    $ python viewer.py
    ```
    + Raccourcis claviers
        * F5: Rafraichit la liste d'image
        * F: adapte la taille de l'image à l'écran
        * haut/bas/page up/page up: navigue dans la liste d'images
        * début: sélectionne la première image
        * fin: sélectionne la dernière image


- Curves Editor
    + Editeur de courbes RGB, utilise les images stockées dans le répertoire `frames`
    + Exécuter la commande suivante dans le répertoire `tools`:
    ```sh
    $ python curves_editor.py
    ```
    + Raccourcis claviers
        * R/G/B/A: sélectionne un des canaux RGBM
    + Courbes:
        clic gauche: crée un point
        clic droit: supprime le point selection

- Video Editor
    + Montage video: recadrage, remplacer les trames, aperçu final
    + Exécuter la commande suivante dans le répertoire `tools`:
    ```sh
    $ python video_editor.py
    ```
