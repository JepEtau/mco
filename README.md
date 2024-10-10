
# MCO / MCoG: restoration


## Installation
- Install miniconda
- Create a conda environment
```sh
conda create -n m python==3.11.8
```

- Activate the environment
```sh
conda activate mco
```

- **Install python packages**
```sh
pip install -r requirements.txt
```
- To upgrade packages (if needed): `pip install -r requirements.txt --upgrade`

- **Install external tools**
```sh
python install.py
```

## Usage
- Activate the conda env
- Run a python script
- Options available for every script
    - `--help`: print the help message and available options
    - `--episode`: episode no.
    - `--chapter`: process a specific chapter, may be ignored to process all chapters. Translation for english users.
        - g_debut: opening credits
        - precedemment: previously
        - episode: episode
        - g_asuivre: title of the 'to follow' chapter
        - asuivre: to follow
        - g_documentaire: title of the 'documentary' chapter
        - documentaire: 'documentary'
        - g_fin: end credits
    - `--en`: english edition
    - `--debug`: print the log


## 0. Verification: check database for corruption
Examples:

- Episode:
```sh
python parse_db.py --episode 1
```
- Opening credits:
```sh
python parse_db.py --chapter g_debut
```
- Episode: for english edition
```sh
python parse_db.py --episode 1 --en
```


## 1. Generate audio tracks
Examples:
- Opening/Ending credits:
    ```sh
    python process_audio.py --chapter g_debut
    python process_audio.py --chapter g_fin
    ```

- Episode:
    ```sh
    python process_audio.py --episode 1
    ```

Notes:
- The audio tracks of the opening/end credits are automatically generated when generating the audio of an episode
- It is possible to overwrite the previously generated audio tracks by appending `--force` to the command line


## (Generate Low Resolution video)
- Opening/Ending credits
    ```sh
    python generate_lr.py --chapter g_debut
    python generate_lr.py --chapter g_fin
    ```

- Episode
    ```sh
    python generate_lr.py --episode 1
    ```

## 2. Upscale
- Credits
    ```sh
    python upscale.py --chapter g_debut
    ```

- Episode
    ```sh
    python generate_lr.py --episode 1
    ```

Note: g_asuivre not yet supported


## (Simulate final version)
Like lr but:
- resize to 1080p (1440x1080)
- add some effects (overlay)

simulate_final.py

What is not done:
- NN upscale
- stabilization
- temporal filtering
- color grade
- final crop/resize
