# -*- coding: utf-8 -*-
import sys
from copy import deepcopy
from pprint import pprint

from utils.common import (
    K_ALL_PARTS_ORDERED,
    K_GENERIQUES,
    get_k_part_from_frame_no,
    get_shot_from_frame_no_new,
)

from utils.common import (
    K_ALL_PARTS_ORDERED,
    get_k_part_from_frame_no,
    get_shot_from_frame_no_new,
)
from utils.get_filters import get_filters_from_shot
from utils.get_curves import get_lut_from_curves


def consolidate_target_shots(db, k_ed, k_ep, k_part:str=''):
    # This function is used to consolidate target shots so that
    # the process function can take these shots for the generation
    # It is used to replace the 'src' structure by the input shot
    # and merge it into this target shot

    verbose = False

    # Process part(s)
    k_parts = K_ALL_PARTS_ORDERED if k_part == '' else [k_part]
    for k_p in k_parts:

        if k_p in ['g_debut', 'g_fin']:
            db_video = db[k_p]['target']['video']
            k_ep_src_main = db[k_p]['target']['video']['src']['k_ep']
        elif k_ep == 'ep00':
            sys.exit("Erreur: le numéro de l'épisode est manquant")
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

                # Get the shot
                shot_src = get_shot_from_frame_no_new(db,
                    shot['src']['start'],
                    k_ed=k_ed_src,
                    k_ep=k_ep_src,
                    k_part=k_part_src)

                if verbose:
                    print("++++++++++++++++++++++++++  shot_src : %s:%s:%s ++++++++++++++++++++++++++" % (k_ed_src, k_ep_src, k_part_src))
                    pprint(shot_src)
                    print("")

                # Verify that this shot can be replaced
                if ((shot['src']['start'] + shot['src']['count']) > (shot_src['start'] + shot_src['count'])
                    and 'effects' not in shot.keys()):
                    print("Error: cannot generate shot as the source has not enough frames src: start=%d" % (shot['src']['start']))
                    print("target:")
                    pprint(shot)

                # Let's update the dst structure of the target shot
                # TODO: remove this after full validation
                # if (shot['start'] != shot['src']['start']
                # or shot['count'] != shot['src']['count']):
                #     pprint(shot)
                #     sys.exit("differences between src and shot")

                shot['dst'].update({
                    'start': shot['start'],
                    'count': shot['count'],
                })

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
    # print("")


    if 'layer' not in shot.keys() or shot['layer'] == 'fgd':

        db_video = db[k_ep][k_ed][k_part]['video']
        shot_no = shot['no']

        # Input and dimensions
        shot.update({
            'input': db['editions'][k_ed]['inputs'][k_ep],
            'dimensions': deepcopy(db['editions'][k_ed]['dimensions']),
        })

        # Foreground
        # if 'shots' in db_video.keys():
        #     print("***********************************")
        #     pprint(db_video['shots'][shot_no])
        #     print("***********************************")
        #     pprint(shot)
        #     print("***********************************")
        #     shot.update(deepcopy(db_video['shots'][shot_no]))

        shot['ref'] = shot['start']

        # Patch start with offset ...
        # TODO: correct this!!!!
        # try:
        #     offsets = db_video['offsets']
        #     for i in range(len(offsets)):
        #         if offsets[i]['start'] <= shot['start'] <= offsets[i]['end']:
        #             shot['start'] = shot['start'] + offsets[i]['offset']
        #             break
        # except:
        #     # print("warning: no offset defined in %s:%s:%s" % (k_ed, k_ep, k_part))
        #     pass


        # Remove unused tasks
        if 'bgd' in shot['tasks']:
            shot['tasks'].remove('bgd')

        # Remove stitching
        for t in ['stitching', 'stabilize']:
            if t not in shot.keys():
                try: shot['tasks'].remove(t)
                except: pass


    elif 'layer' in shot.keys() and shot['layer'] == 'bgd':

        print("%s.consolidate_shot: %s:%s:%s" % (__name__, k_ed, shot['dst']['k_ep'], shot['dst']['k_part']))
        pprint(shot)
        print("")

        k_ed = shot['layers']['bgd']
        db_video = db[k_ep][k_ed][k_part]['video']

        shot['ref'] = shot['start']
        shot['k_ed'] = k_ed
        if True:
            # Patch start with offset
            offsets = db_video['offsets']
            for i in range(len(offsets)):
                if offsets[i]['start'] <= shot['start'] <= offsets[i]['end']:
                    shot['start'] = shot['start'] + offsets[i]['offset']
                    break

        # pprint(db[k_ep][k_ed_bgd][k_part]['video'])
        # pprint(shot)
        # sys.exit()

        # Background, use foreground shot details to
        # update the properties
        # shot.update(deepcopy(db[k_ep][db['editions']['fgd']][k_part]['video']['shots'][shot_no]))
        shot['offsets'] = db_video['offsets']

        # Remove unused tasks
        for t in ['stitching', 'sharpen', 'rgb']:
            if t in shot['tasks']:
                shot['tasks'].remove(t)


    else:
        sys.exit("Did not detected FGD/BGD in shot structure")


    # Get filters used by this shot
    shot['filters'] = get_filters_from_shot(db, shot)

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
                'custom': db[k_ep][k_ed][k_part]['video']['geometry'],
            })

    elif k_part in ['g_asuivre', 'g_reportage']:
        # pprint(shot)
        # k_ed_ref = db[k_part]['common']['video']['reference']['k_ed']
        k_ep_dst = shot['dst']['k_ep']
        k_ep_src = shot['k_ep']
        k_ed_src = shot['k_ed']
        # print("get geometry from part %s:%s:%s" % (k_ed, k_ep, k_part[2:]))
        shot['geometry'] = {
            'part':  db[k_ep_dst][k_ed][k_part[2:]]['video']['geometry'],
            'custom': db[k_ep][k_ed_src][k_part]['video']['geometry'],
        }

    else:
        # print("TODO: consolidate_shot: update when replacing the shots in episode")
        k_ep_dst = shot['dst']['k_ep']
        k_part_dst = shot['dst']['k_part']
        shot['geometry'] = {
            'part':  db[k_ep_dst][k_ed][k_part_dst]['video']['geometry'],
        }
        if k_ep != k_ep_dst or k_part != k_part_dst:
            shot['geometry'].update({
                'custom': db[k_ep][k_ed][k_part]['video']['geometry'],
            })


    # RGB correction: calculate the lut from the curves
    if shot['curves'] is not None:
        k_ep_or_g = k_part if k_part in K_GENERIQUES else k_ep
        shot['curves']['lut'] = get_lut_from_curves(db,
                                    k_ep_or_g,
                                    shot['curves']['k_curves'])

    # print("%s.consolidate_shot: end" % (__name__))
    # pprint(shot)
    # sys.exit()
