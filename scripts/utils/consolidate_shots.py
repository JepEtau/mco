# -*- coding: utf-8 -*-
import sys
from copy import deepcopy
from pprint import pprint

from utils.common import K_ALL_PARTS_ORDERED, get_k_part_from_frame_no, get_shot_from_frame_no_new



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
                shot_src['last'] = True

            if verbose:
                print("+++++++++++++++++++++ consolidated target shot ++++++++++++++++++++++++")
                pprint(shot)
                print("")
                print("=================================================================================")
                # sys.exit()


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


    sys.exit()