# -*- coding: utf-8 -*-
import sys
from copy import deepcopy
from pprint import pprint

from utils.common import (
    K_ALL_PARTS_ORDERED,
    K_GENERIQUES,
    get_k_part_from_frame_no,
    get_or_create_src_shot,
    get_src_shot_from_frame_no,
)
from utils.get_filters import get_filters_from_shot
from utils.get_curves import get_lut_from_curves


def consolidate_target_shots(db, k_ep, k_part:str=''):
    # This function is used to consolidate target shots so that
    # the process function can take these shots for the generation
    # It is used to replace the 'src' structure by the input shot
    # and merge it into this target shot

    verbose = True

    # Process part(s)
    k_parts = K_ALL_PARTS_ORDERED if k_part == '' else [k_part]
    for k_p in k_parts:

        if k_p in ['g_debut', 'g_fin']:
            db_video = db[k_p]['target']['video']
            k_ep_src_main = db[k_p]['target']['video']['src']['k_ep']
            # pprint(db_video)
            # print("k_ep_src_main: %s" % (k_ep_src_main))
        elif k_ep == 'ep00':
            sys.exit("Erreur: consolidate_target_shots: le numéro de l'épisode est manquant")
        else:
            db_video = db[k_ep]['target']['video'][k_p]
            k_ep_src_main = k_ep


        if db_video['count'] == 0:
            # Empty part
            continue

        # Walk through shots
        shots = db_video['shots']
        for shot in shots:

            # Select the shot used for the generation
            if verbose:
                print("\n++++++++++++++++++++++++++ target ++++++++++++++++++++++++++")
                pprint(shot)
                print("")
                # sys.exit()

            if 'src' in shot.keys() and shot['src']['use']:
                # This shot has to de modified with the shot specified in the 'src'
                k_ed_src = shot['src']['k_ed']
                k_ep_src = shot['src']['k_ep']

                # Find the part of this src
                k_part_src = get_k_part_from_frame_no(db,
                    k_ed=k_ed_src,
                    k_ep=k_ep_src,
                    frame_no=shot['src']['start'])

                # Get the src shot: it must have been defined previously, if not, use the create function?
                try:
                    shot_src = get_src_shot_from_frame_no(db,
                        shot['src']['start'],
                        k_ed=k_ed_src,
                        k_ep=k_ep_src,
                        k_part=k_part_src)
                    if shot_src is None:
                        sys.exit("TODO: replace by get_or_create_src_shot")
                except:
                    print("Warning: consolidate_target_shots: create a src shot because not defined in config file %s:%s:%s, k_p=%s" % (k_ed_src, k_ep_src, k_part_src, k_p))
                    shot_src = get_or_create_src_shot(db,
                        shot['src']['start'],
                        k_ed=k_ed_src,
                        k_ep=k_ep_src,
                        k_part=k_part_src)
                    if shot_src is None:
                        sys.exit("TODO: replace by get_or_create_src_shot")

                if verbose:
                    print("++++++++++++++++++++++++++  shot_src : %s:%s:%s ++++++++++++++++++++++++++" % (k_ed_src, k_ep_src, k_part_src))
                    pprint(shot_src)
                    print("")

                # Verify that this shot can be replaced
                if ((shot['src']['start'] + shot['src']['count']) > (shot_src['start'] + shot_src['count'])
                    and 'effects' not in shot.keys()):

                    if shot['dst']['k_part'] == 'episode':
                        # Do not verify for precedemment/asuivre as what is important is the total nb of frames,
                        # so only episode
                        print("Error: cannot generate shot as the source has not enough frames src: start=%d" % (shot['src']['start']))
                        print("target:")
                        pprint(shot)
                        print("source:")
                        pprint(shot_src)
                        sys.exit()

                # Let's update the dst structure of the target shot
                # TODO: remove this after full validation
                # if (shot['start'] != shot['src']['start']
                # or shot['count'] != shot['src']['count']):
                #     pprint(shot)
                #     sys.exit("differences between src and shot")

                # shot['dst'].update({
                #     'start': shot['start'],
                #     'count': shot['count'],
                # })

                if 'count' not in shot['dst'].keys():
                    shot['dst']['count'] = shot['count']
                if 'start' not in shot['dst'].keys():
                    shot['dst']['start'] = shot['start']

                # Replace all values in target shot except:
                # src, dst, (geometry), effects
                for k in shot_src.keys():
                    if k in ['src', 'dst', 'no', 'geometry', 'effects']:
                        continue
                    shot[k] = shot_src[k]

                shot.update({
                    'k_ed': k_ed_src,
                    'k_ep': k_ep_src,
                    'k_part': k_part_src,
                })

            else:
                shot.update({
                    'k_ed': k_ed,
                    'k_ep': k_ep_src_main,
                    'k_part': k_p,
                })

            # Add a flag which is used by concatenation functions
            if shot == shots[-1]:
                shot['last'] = True

            if verbose:
                print("+++++++++++++++++++++ consolidated target shot ++++++++++++++++++++++++")
                pprint(shot)
                print("")
                print("=================================================================================")
                # sys.exit()


            if verbose:
                print("\t\t%s: %s\t(%d)\t<- %s:%s:%s   %d (%d)" % (
                    "{:3d}".format(shot['no']),
                    "{:5d}".format(shot['start']),
                    shot['dst']['count'],
                    shot['k_ed'],
                    shot['k_ep'],
                    shot['k_part'],
                    shot['start'],
                    shot['count']),
                    flush=True)



def consolidate_shot(db, shot) -> None:
    """This procedure is used to simplify a single shot and add
    properties to process it: removes unecessary property, add
    paths to input/output files, update frames no. depending on edition, etc.

    Args:
        db: the global database
        shot: a single shot to consolidate

    Returns:
        None

    """
    # k_ed, k_ep and k_part are the source keys for this shot
    # [dst][k_ep] and [dst][k_part] are the destination (i.e. target)
    k_ep = shot['k_ep']
    k_ed = shot['k_ed']
    k_part = shot['k_part']

    # print("%s.consolidate_shot: %s:%s:%s" % (__name__, k_ed, shot['dst']['k_ep'], shot['dst']['k_part']))
    # pprint(shot)
    # print("------------------------------------------------------------------------------------------------------")

    # Input and dimensions
    shot.update({
        'input': db[k_ep][k_ed][k_part]['video']['input'],
        'dimensions': db['editions'][k_ed]['dimensions'],
    })

    # Frame ref is used for deinterlace, calculate it: use the offset array
    shot['ref'] = shot['start']
    if k_part in K_GENERIQUES:
        k_ep_target = db[k_part]['target']['video']['src']['k_ep']
        k_ed_ref = db[k_ep]['target']['video']['k_ed_ref']
    else:
        # pprint(db[k_ep]['target']['video'])
        # pprint(shot)
        # k_ed_target = db[k_ep]['target']['video']['src']['k_ed']
        k_ed_ref = db[k_ep]['target']['video']['k_ed_ref']
        # if shot['k_ep'] != shot['dst']['k_ep']:
        k_ep_target = shot['dst']['k_ep']

    if ((k_ed != k_ed_ref or k_ep != k_ep_target)
        and k_part == shot['dst']['k_part']):
        # Apply offset only if part is different:
        # when replacing episode<->asuivre or episode<->precedemment or asuivre <-> precedemment
        print("\t\t\tapply offset for %s: target:%s:%s:%s ref:%s:%s:%s" % (
            k_part,
            k_ed, k_ep_target, shot['dst']['k_part'],
            k_ed_ref, k_ep, k_part))
        try:
            offsets = db[k_ep][k_ed][k_part]['video']['offsets']
            # print("%s:%s:%s, offsets=" % (k_ed_src, k_ep, k_part), offsets)
            for offset in offsets:
                if offset['start'] <= shot['start'] <= offset['end']:
                    # shot['ref'] = shot['start'] + offset['offset']
                    shot['start'] = shot['start'] - offset['offset']
                    break
        except:
            print("offsets are not defined in %s:%s for part %s" % (k_ed, k_ep, k_part))
    # else:
    #     print("\t\t\tdisable offset for %s" % (k_part))


    # Get filters used by this shot
    shot['filters'] = get_filters_from_shot(db, shot)
    # pprint(shot)

    # Geometry
    # print("consolidate_shot: get geometry for %s:%s:%s" % (k_ed, k_ep, k_part))
    if k_part in ['g_debut', 'g_fin']:
        # Get the geometry for the part wich is the target
        # print("----------- target -------------")
        # pprint(db[k_part]['target']['video'])
        k_ep_src = db[k_part]['target']['video']['src']['k_ep']
        k_ed_src = db[k_part]['target']['video']['src']['k_ed']
        shot['geometry'] = {
            'part': db[k_ep_src][k_ed_src][k_part]['video']['geometry'],
        }
        # Add a different geometry because it is not the same k_ed:k_ep
        if k_ed != k_ed_src or k_ep != k_ep_src:
            shot['geometry'].update({
                'shot': db[k_ep][k_ed][k_part]['video']['geometry'],
            })

    elif k_part in ['g_asuivre', 'g_reportage']:
        print("TODO: consolidate_shot: verify geometry for :%s" % (k_part))
        # pprint(shot)
        k_ep_dst = shot['dst']['k_ep']
        k_ep_src = shot['k_ep']
        k_ed_src = shot['k_ed']

        if 'video' in db[k_part]['common'].keys():
            k_ed_dst = db[k_part]['common']['video']['reference']['k_ed']
            # print("get geometry from part %s:%s:%s for %s:%s:%s" % (
            #     k_ed, k_ep, k_part[2:], k_ed_src, k_ep_dst, k_part))
            # pprint(db[k_ep_dst])
            shot['geometry'] = {
                'part':  db[k_ep_dst][k_ed][k_part[2:]]['video']['geometry'],
                'shot': db[k_ep][k_ed_dst][k_part]['video']['geometry'],
            }
        else:
            print("warning: no geometry/video defined in %s for %s:%s:%s" % (k_part, k_ed_src, k_ep_dst, k_part))
    else:
        # print("TODO: consolidate_shot: update when replacing the shots in episode")
        k_ep_dst = shot['dst']['k_ep']
        k_part_dst = shot['dst']['k_part']
        k_ed_src = shot['src']['k_ed']
        k_ep_src = shot['src']['k_ep']
        try:
            shot['geometry'] = {
                'part':  db[k_ep_dst][k_ed][k_part_dst]['video']['geometry'],
            }
        except:
            print("info: no geometry defined for %s:%s:%s" % (k_ed, k_ep_dst, k_part_dst))
        if k_ep != k_ep_dst or k_part != k_part_dst:
            shot['geometry'].update({
                'shot': db[k_ep][k_ed][k_part]['video']['geometry'],
            })


    # RGB correction: calculate the lut from the curves
    if shot['curves'] is not None:
        shot['curves']['lut'] = get_lut_from_curves(db,
            k_ed_src,
            k_ep_src,
            k_part,
            shot['curves']['k_curves'])
