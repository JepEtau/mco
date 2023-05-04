# -*- coding: utf-8 -*-

from pprint import pprint
import sys
from filters import IMG_BORDER_LOW_RES
from filters.utils import (
    FINAL_FRAME_HEIGHT,
    INITIAL_FRAME_HEIGHT,
    INITIAL_FRAME_WIDTH,
)
import numpy as np
from shot.consolidate_shot import consolidate_shot
from utils.common import K_ALL_PARTS_ORDERED
from utils.pretty_print import *


def display_stats(db, k_ep:str, k_part:str=''):


    k_parts = K_ALL_PARTS_ORDERED if k_part == '' else [k_part]
    for k_p in k_parts:

        # Curves
        curves_list = list()
        curves_count = 0

        # Geometry
        geometry_crop = {
            'top': list(),
            'bottom': list(),
            'left': list(),
            'right': list(),
            'width': {
                'min': {'value': INITIAL_FRAME_WIDTH * 2, 'shot_no': 0, 'shot_start': 0},
                'max': {'value': 0, 'shot_no': 0, 'shot_start': 0},
            },
            'height': {
                'min': {'value': INITIAL_FRAME_HEIGHT * 2, 'shot_no': 0, 'shot_start': 0},
                'max': {'value': 0, 'shot_no': 0, 'shot_start': 0},
            },
            'undefined': list(),
            'default': list()
        }
        geometry_crop_count = 0
        geometry_resized_width = {
            'min': {'value': INITIAL_FRAME_WIDTH * 2, 'shot_no': 0, 'shot_start': 0},
            'max': {'value': 0, 'shot_no': 0, 'shot_start': 0},
            'target': 0,
            'erroneous_shots': list(),
            'corrected_by_fit_to_width': list()
        }




        if k_p in ['g_debut', 'g_fin']:
            db_video = db[k_p]['video']
        elif k_ep == 'ep00':
            sys.exit("Erreur: le numéro de l'épisode est manquant")
        else:
            db_video = db[k_ep]['video']['target'][k_p]

        if db_video['count'] == 0:
            # Part is empty: precedemment in ep01, asuivre in ep39
            continue

        # Walk through target shots
        shots = db_video['shots']
        for shot in shots:
            print_lightgreen("    \t%s: %s\t(%d)\t<- %s:%s:%s   %d (%d)" % (
                "{:3d}".format(shot['no']),
                "{:5d}".format(shot['start']),
                shot['dst']['count'],
                shot['k_ed'],
                shot['k_ep'],
                shot['k_part'],
                shot['start'],
                shot['count']),
                flush=True)


            # Consolidate shot
            shot['last_task'] = 'final'
            consolidate_shot(db, shot=shot)

            if False:
                print_lightcyan("================================== SHOT =======================================")
                pprint(shot)
                print_lightcyan("===============================================================================")

            # Curves
            try:
                k_curves = shot['curves']['k_curves']
                curves_count += 1
                if k_curves is not None:
                    curves_list.append(k_curves)
                else:
                    curves_list.append('')
            except:
                curves_list.append('')

            # Geometry
            try:
                shot_geometry = shot['geometry']['shot']

                if min(shot_geometry['crop']) == 0:
                    # Crop not defined
                    geometry_crop['undefined'].append(shot['no'])
                else:

                    # Shots which used default geometry
                    if shot_geometry['is_default']:
                        geometry_crop['default'].append(shot['no'])

                    # Crop values
                    geometry_crop['top'].append(shot_geometry['crop'][0])
                    geometry_crop['bottom'].append(shot_geometry['crop'][1])
                    geometry_crop['left'].append(shot_geometry['crop'][2])
                    geometry_crop['right'].append(shot_geometry['crop'][3])
                    geometry_crop_count += 1

                    # Cropped image: width
                    width = INITIAL_FRAME_WIDTH * 2 - (shot_geometry['crop'][2] + shot_geometry['crop'][3])
                    if width < geometry_crop['width']['min']['value']:
                        geometry_crop['width']['min'].update({
                            'value': width,
                            'shot_no': shot['no'],
                            'shot_start': shot['start'],
                        })
                    elif width > geometry_crop['width']['max']['value']:
                        geometry_crop['width']['max'].update({
                            'value': width,
                            'shot_no': shot['no'],
                            'shot_start': shot['start'],
                        })

                    # Cropped image: height
                    height = INITIAL_FRAME_HEIGHT * 2 - (shot_geometry['crop'][0] + shot_geometry['crop'][1])
                    if height < geometry_crop['height']['min']['value']:
                        geometry_crop['height']['min'].update({
                            'value': height,
                            'shot_no': shot['no'],
                            'shot_start': shot['start'],
                        })
                    elif height > geometry_crop['height']['max']['value']:
                        geometry_crop['height']['max'].update({
                            'value': height,
                            'shot_no': shot['no'],
                            'shot_start': shot['start'],
                        })

                    # Resized image
                    if shot['no'] == 0:
                        geometry_resized_width['target'] = shot['geometry']['target']['w']

                    width_resized = int((width * np.float32(height)) / FINAL_FRAME_HEIGHT)
                    if width_resized < geometry_resized_width['min']['value']:
                        geometry_resized_width['min'].update({
                            'value': width_resized,
                            'shot_no': shot['no'],
                            'shot_start': shot['start'],
                        })
                    elif width_resized > geometry_resized_width['max']['value']:
                        geometry_resized_width['max'].update({
                            'value': width_resized,
                            'shot_no': shot['no'],
                            'shot_start': shot['start'],
                        })


                    if width_resized < geometry_resized_width['target']:
                        geometry_resized_width['erroneous_shots'].append(shot['no'])
                        if shot['geometry']['fit_to_width']:
                            geometry_resized_width['corrected_by_fit_to_width'].append(shot['no'])


            except:
                pass



        print_lightgreen("Statistics")
        print_lightgreen("===============================================================================")
        shot_count = len(shots)

        # Curves
        print_lightgreen(f"curves:", end=' ')
        print(f"{curves_count}/{shot_count}")

        # Geometry
        print_lightgreen(f"geometry:", end=' ')
        print(f"{geometry_crop_count}/{shot_count}")
        if geometry_crop_count > 0:
            print_lightcyan("crop area:")
            for k in ['top', 'bottom', 'left', 'right']:
                print(f"    {k}:\tmin: {min(geometry_crop[k])},\tmax: {max(geometry_crop[k])}")

            print_lightcyan("cropped image:")
            print(f"    width:")
            print(f"        min: {geometry_crop['width']['min']['value']}, shot no. {geometry_crop['width']['min']['shot_no']} ({geometry_crop['width']['min']['shot_start']})")
            print(f"        max: {geometry_crop['width']['max']['value']}, shot no. {geometry_crop['width']['max']['shot_no']} ({geometry_crop['width']['max']['shot_start']})")
            print(f"    height:")
            print(f"        min: {geometry_crop['height']['min']['value']}, shot no. {geometry_crop['height']['min']['shot_no']} ({geometry_crop['height']['min']['shot_start']})")
            print(f"        max: {geometry_crop['height']['max']['value']}, shot no. {geometry_crop['height']['max']['shot_no']} ({geometry_crop['height']['max']['shot_start']})")

            print_lightcyan("resized image (fit to width ignored), width:")
            print(f"    target: {geometry_resized_width['target']}")
            print(f"    min: {geometry_resized_width['min']['value']}, shot no. {geometry_resized_width['min']['shot_no']} ({geometry_resized_width['min']['shot_start']})")
            print(f"    max: {geometry_resized_width['max']['value']}, shot no. {geometry_resized_width['max']['shot_no']} ({geometry_resized_width['max']['shot_start']})")

            print_lightcyan(f"shots without geometry settings ({len(geometry_crop['undefined'])}):")
            print("    ", geometry_crop['undefined'])

            print_lightcyan(f"shots using default geometry ({len(geometry_crop['default'])}):")
            print("    ", geometry_crop['default'])

            print_lightcyan(f"erroneous shot dimensions ({len(geometry_resized_width['erroneous_shots'])}):")
            print("    ", geometry_resized_width['erroneous_shots'])

            print_lightcyan(f"erroneous shot dimensions corrected by \'fit to width\' ({len(geometry_resized_width['corrected_by_fit_to_width'])}):")
            print("    ", geometry_resized_width['corrected_by_fit_to_width'])

