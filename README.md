
# MCO / MCoG: restoration

## Cheat sheet

### Installation
```sh
conda create -n m python==3.12.7
conda activate mco
pip install -r requirements.txt
python install.py
```


### Tasks

- Parse
```sh
python parse_db.py --chapter g_debut
python parse_db.py --chapter g_debut --en
python parse_db.py --episode 1
```

- Audio
```sh
python audio.py --chapter g_debut
python audio.py --chapter g_debut --en
python audio.py --chapter g_fin
python audio.py --episode 1
```

- Simulate in lowres
```sh
python lr.py --watermark --chapter g_debut
python lr.py --watermark --chapter g_fin
python lr.py --watermark --episode 1
```

- Simulate (1080p, no frame replace/upscale/deshake/color grading/geometry)
```sh
python sim.py --chapter g_debut
python sim.py --chapter g_fin
python sim.py --episode 1
```

- Upscale for comparisons
```sh
python upscale.py --chapter g_debut
python upscale.py --chapter g_fin
python upscale.py --episode 1
```

- Generate hr
```sh
python hr.py --chapter g_debut
python hr.py --chapter g_fin
python hr.py --episode 1
```

- Convert from DNxHD h264 video after stabilization for comparisons
```sh
python hr.py --chapter g_debut
python hr.py --chapter g_fin
python hr.py --episode 1
```

- Temporal filtering
```sh
python tf.py --chapter g_debut
python tf.py --chapter g_fin
python tf.py --episode 1
```

- Create symbolic links for color grading
```sh
python symlink.py --chapter g_debut
python symlink.py --chapter g_fin
python symlink.py --episode 1
```

- Validate geometry after color grading, print some stats
```sh
python geometry.py --chapter g_debut
python geometry.py --chapter g_fin
python geometry.py --episode 1
```

- Final
```sh
python final.py --chapter g_debut
python final.py --chapter g_fin
python final.py --episode 1
```
