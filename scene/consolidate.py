from copy import deepcopy
import os
from pprint import pprint
import sys
from utils.hash import calc_hash
from utils.mco_types import ChapterGeometry, ChapterVideo, Effect, Scene, SceneGeometry
from parsers import (
    db,
    Filter,
    TASK_NAMES,
    ProcessingTask,
    VideoSettings,
    TaskName,
)
from utils.mco_utils import (
    get_cache_path,
    get_target_video,
    is_last_scene,
    nested_dict_set
)
from utils.p_print import *
from utils.path_utils import absolute_path
from video.concat_frames import get_video_filename


def consolidate_scene(
    scene: Scene,
    watermark: bool = False,
    evaluation: bool = False
) -> None:
    """This procedure is used to simplify a single scene and add
    properties to process it: removes unecessary property, add
    paths to input/output files, update frames no. depending on edition, etc.

    edition_mode: used to not consolidate geometry/curves and remove replace/stabilize/deshake
    """
    verbose: bool = False

    task_name: TaskName = scene['task'].name

    scene['src'].consolidate(task_name=task_name, watermark=False)
    primary_src_scene = scene['src'].primary_scene()

    if verbose:
        print(lightgreen("Consolidate scene:"))
        print(lightcyan("================================== Scene ======================================="))
        pprint(scene)
        print(lightcyan("-------------------------------------------------------------------------------"))


    # Cache directory
    scene['cache'] = get_cache_path(scene)
    # os.path.join(db['common']['directories']['cache'], k_ep, k_ch, "%03d" % (scene['no']))


    # Geometry
    #---------------------------------------------------------------------------
    k_ep: str = scene['dst']['k_ep']
    k_ed: str = scene['dst']['k_ed']
    k_ch: str = scene['dst']['k_ch']
    if k_ch in ['g_asuivre', 'g_documentaire']:
        # print("\t\t\tconsolidate_scene: get geometry from %s:%s:%s" % (k_ed, k_ep, k_ch[2:]))
        k_ep_dst = scene['dst']['k_ep']
        ch_geometry: ChapterGeometry | None
        width: int = 0
        try:
            ch_geometry = db[k_ep_dst]['video']['target'][k_ch[2:]]['geometry']
            width = ch_geometry.width
        except:
            pass
        # ch_geometry: ChapterGeometry = db[k_ep]['video'][k_ed][k_ch]['geometry']

        scene['geometry'] = SceneGeometry(
            chapter=ch_geometry
        )

    else:
        k_ed_src, k_ep_src, k_ch_src, scene_no_src = primary_src_scene['k_ed_ep_ch_no']
        if verbose:
            print(f"\t\t\tconsolidate_scene: get geometry for {k_ed}:{k_ep}:{k_ch}")

        if 'geometry' in primary_src_scene['scene']:
            scene['geometry'] = deepcopy(primary_src_scene['scene']['geometry'])

            # Target geometry: width defined
            chapter: ChapterVideo | None = None
            try:
                if k_ch in ('g_debut', 'g_fin'):
                    chapter = db[k_ch]['video']
                else:
                    chapter = db[k_ep]['video']['target'][k_ch]
            except:
                pass
            print(f"{k_ep}:{k_ch}")
            print(f"{k_ed_src}:{k_ep_src}:{k_ch_src}:{scene_no_src}")

            pprint(chapter['geometry'])
            scene['geometry'].chapter = deepcopy(chapter['geometry'])
            # Get default geometry for a scene
            # scene_geometry: SceneGeometry =


        # try:
        #     default_scene_src_geometry = db[k_ep_src]['video'][k_ed_src][k_ch_src]['geometry']
        #     default_scene_src_geometry['is_default'] = True
        # except:
        #     default_scene_src_geometry = {
        #         'keep_ratio': True,
        #         'fit_to_width': False,
        #         'crop': [0] * 4,
        #         'is_default': True
        #     }

        # # Get the customized geometry for a scene
        # try:
        #     scene_src_geometry = db[k_ep_src]['video'][k_ed_src][k_ch_src]['scenes'][scene_no_src]['geometry']['scene']
        #     scene_src_geometry['is_default'] = False
        # except:
        #     scene_src_geometry = None

        # if scene_src_geometry is not None:
        #     # Use the customized
        #     nested_dict_set(scene, scene_src_geometry, 'geometry', 'scene')
        #     scene['geometry']['scene']['is_default'] = False
        # else:
        #     # Use the default because no customized defined
        #     nested_dict_set(scene, default_scene_src_geometry, 'geometry', 'scene')
        #     try: scene['geometry']['scene']['is_default'] = True
        #     except: pass

    # Processing chain
    #---------------------------------------------------------------------------

    # Get filters used by this scene: use the filters from the first src scene
    # all src scenes MUST have the same filters. Assume that's the case
    scene['filters'] = deepcopy(primary_src_scene['scene']['filters'])

    # consolidate_scene_filters: add missing filters
    scene_filters = scene['filters']
    for t in TASK_NAMES:
        if t not in scene_filters:
            scene_filters[t] = Filter(task_name=t)

    deint_hashcode = scene_filters['initial'].hash

    # Replace
    replace_hash: str = ''
    frame_replace = scene['src'].get_frame_replace()
    if len(frame_replace.keys()) != 0:
        replace_hash = ','.join([f"{k}:{v}" for k, v in frame_replace.items()])

    # Upscale
    upscale_hashcode = calc_hash(';'.join([
        deint_hashcode,
        scene_filters['upscale'].sequence.replace('.pth', '')
    ]))

    # Store hashes
    scene_filters['lr'].hash = calc_hash(';'.join([deint_hashcode, replace_hash]))
    scene_filters['hr'].hash = upscale_hashcode
    scene_filters['upscale'].hash = upscale_hashcode

    # Update the scene task
    scene['task'].hashcode = scene_filters[task_name].hash

    if task_name == 'lr' and watermark:
        # if 'effects' in scene:
        #     scene['effects'] = Effects()
        # scene['effects'].append(Effect(name='watermark'))
        sequence: str = scene['filters'][task_name].sequence
        scene['filters'][task_name].sequence = (
            f"{sequence};watermark"
            if sequence
            else "watermark"
        )


    # Output
    #---------------------------------------------------------------------------

    # Output video settings
    _task_name: str = task_name
    if task_name == 'initial':
        _task_name = 'lr'

    vsettings: VideoSettings = db['common']['video_format'].get(_task_name, None)
    if vsettings is not None:
        scene['task'].video_settings = deepcopy(vsettings)
        vsettings = scene['task'].video_settings
        if task_name == 'hr':
            vsettings.pad = db['common']['video_format'][task_name].pad
            vsettings.metadata['HR'] = scene['task'].hashcode
    else:
        raise ValueError(f"VideoSettings not defined for task: {task_name}")

    # Output video filename
    _k_ed, _k_ep = primary_src_scene['k_ed_ep_ch_no'][:2]
    if k_ch in ('g_debut', 'g_fin'):
        cache_path: str = db[k_ch]['cache_path']
        basename = f"{k_ch}_{scene['no']:03}__{_k_ed}_{_k_ep}"
    else:
        cache_path: str = db[k_ep]['cache_path']
        basename = f"{k_ep}_{k_ch}_{scene['no']:03}__{_k_ed}"

    suffix: str = ""
    if task_name != "restored":
        if scene['task'].hashcode != '':
            suffix = f"_{scene['task'].hashcode}"
        suffix += f"_{task_name}"

    # Append the model name to evaluate models: only for upscale task
    if evaluation and task_name == 'upscale':
        sequence: str = scene_filters[task_name].sequence
        for t in (
            ':cuda', ':trt', ':fp16', ':fp32'
        ):
            sequence.replace(t, '')
        model_name=scene_filters['upscale'].sequence.split(',')[-1]
        suffix = f"{suffix}_{model_name}"

    scene['task'].video_file = absolute_path(
        os.path.join(
            cache_path,
            f"scenes_{task_name}",
            f"{basename}{suffix}.mkv"
        )
    )

    # Effects
    #---------------------------------------------------------------------------
    # pprint(scene)
    # sys.exit()
    if is_last_scene(scene) and 'effects' in scene:
        print(yellow("last scene"))
        ch_video: ChapterVideo = get_target_video(scene)
        ch_effect: Effect = (
            ch_video['effects'].primary_effect()
            if 'effects' in ch_video
            else None
        )
        scene_effect: Effect = scene['effects'].primary_effect()
        pprint(ch_effect)
        pprint(scene_effect)
        if ch_effect is not None and 'fadeout' in ch_effect.name:
            if scene_effect is not None and 'fadeout' in scene_effect.name:
                # Patch fadeout
                scene_effect.fade = min(
                    max(scene_effect.fade, ch_effect.fade),
                    scene['dst']['count'] + scene_effect.loop
                )
                # scene_effect.frame_ref = (
                #     scene['src'].first_frame_no() + scene['dst']['count']
                #     + scene_effect.loop - scene_effect.fade
                # )
            elif scene_effect is None:
                scene['effects'] = Effects([
                    Effect(
                        name='fadeout',
                        frame_ref=scene['dst']['count'] - ch_effect.fade,
                        fade= ch_effect.fade
                    )
                ])
            # verbose = True
    if verbose:
        print(lightcyan("TO"))
        pprint(scene)
        print(lightcyan("==============================================================================="))
        sys.exit()
