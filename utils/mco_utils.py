import os
from typing import Literal
from utils.mco_types import Scene
from utils.p_print import *
from parsers import Chapter, key
from parsers import db

def makedirs(
    episode,
    chapter: Chapter = '',
    type: Literal['video', 'concatenation'] = 'video'
):
    """ Create a directory that contains all video clips or the concatenation files
    """
    episode = key(episode)
    if episode in ['ep00', 'ep40']:
        return

    k = chapter if chapter in ['g_debut', 'g_fin'] else episode

    if type == 'video':
        directory = os.path.join(db[k]['cache_path'], 'video')

    elif type == 'video':
        directory = os.path.join(db[k]['cache_path'], "concatenation")

    os.makedirs(directory, exist_ok=True)
    return directory



def nested_dict_set(d: dict, o: object, *keys) -> None:
    nested_d = d
    for k in keys:
        if k == keys[-1]:
            break
        if k not in nested_d.keys():
            nested_d[k] = dict()
        nested_d = nested_d[k]
    nested_d[k] = o



def get_cache_path(scene: Scene) -> str:
    # Put all images in a single folder for start/end credits
    if scene['k_ch'] in ('g_debut', 'g_fin'):
        return os.path.join(
            db['common']['directories']['cache'],
            scene['k_ch'], f"{scene['no']:03}"
        )

    # If last task is geometry, use the dst structure
    if scene['last_task'] in ('geometry'):
        output_path: str = os.path.join(
            db['common']['directories']['cache'],
            scene['dst']['k_ep'],
            scene['dst']['k_ch'],
            f"{scene['no']:03}"
        )

    else:
        # Otherwise, use the src directory
        #  because these frames are used by multiple episodes
        output_path: str = os.path.join(
            db['common']['directories']['cache'],
            scene['k_ep'],
            scene['k_ch'],
            f"{scene['src']['no']:03}"
        )

    return output_path
