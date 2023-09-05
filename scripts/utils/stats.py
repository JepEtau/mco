# -*- coding: utf-8 -*-

from pprint import pprint
import sys
from img_toolbox import IMG_BORDER_LOW_RES
from img_toolbox.filters import calculate_geometry_parameters
from img_toolbox.utils import (
    FINAL_FRAME_HEIGHT,
    INITIAL_FRAME_HEIGHT,
    INITIAL_FRAME_WIDTH,
)
import numpy as np
from shot.consolidate_shot import consolidate_shot
from utils.common import K_ALL_PARTS_ORDERED
from utils.pretty_print import *


def display_stats(db, k_ep:str, k_part:str=''):
    verbose = False

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
            'fit_to_width': list(),

            # Crop after resize
            'crop_2': {
                'list': list(),
                'max': {'value': 0, 'shot_no': 0, 'shot_start': 0},
            }
        }


        # Stabilize
        stabilize = {
            'enabled_list': list(),
            'disabled_list': list(),
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
        for shot in shots[:]:
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
                print_lightcyan("  ================================== SHOT =======================================")
                pprint(shot)
                print_lightcyan("  ===============================================================================")

            geometry_values = calculate_geometry_parameters(shot=shot,
                img=None, simulate=True)

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
            if verbose:
                pprint(shot['geometry'])
                pprint(geometry_values)
            try:
                shot_geometry = shot['geometry']['shot']
            except:
                shot_geometry = shot['geometry']['default']
                pass

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

                width_resized = int(np.float64(width * np.float32(height)) / FINAL_FRAME_HEIGHT)
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

                if width_resized != geometry_resized_width['target']:
                    if geometry_values['pad_error'] is not None:
                        geometry_resized_width['erroneous_shots'].append(shot['no'])
                        print_red("erroneous geometry:")
                        pprint(geometry_values)

                if shot_geometry['fit_to_width']:
                    geometry_resized_width['fit_to_width'].append(shot['no'])

                # Crop width after resize
                if geometry_values['crop_2'] is not None:
                    geometry_resized_width['crop_2']['list'].append(shot['no'])
                    crop_value = geometry_values['crop_2'][2]
                    if crop_value > geometry_resized_width['crop_2']['max']['value']:
                        geometry_resized_width['crop_2']['max'].update({
                            'value': crop_value,
                            'shot_no': shot['no'],
                            'shot_start': shot['start'],
                        })


            # Stabilize
            if 'deshake' in shot.keys() and shot['deshake']['enable']:
                stabilize['enabled_list'].append(shot['no'])
            else:
                stabilize['disabled_list'].append(shot['no'])





        # Display statistics
        print_lightgreen("Statistics")
        print_lightgreen("===============================================================================")
        shot_count = len(shots)

        # Curves
        print_lightgreen(f"\ncurves:", end=' ')
        print(f"{curves_count}/{shot_count}")

        # Geometry
        print_lightgreen(f"\ngeometry:", end=' ')
        print(f"{geometry_crop_count}/{shot_count}")
        if geometry_crop_count > 0:
            print_lightcyan(f"  crop area:")
            for k in ['top', 'bottom', 'left', 'right']:
                print(lightgrey(f"    {k}:\tmin:"), f"{min(geometry_crop[k])}",
                      lightgrey(f",\tmax:"), f"{max(geometry_crop[k])}")

            print_lightcyan(f"  cropped image:")
            for k in ['width', 'height']:
                print(f"    {k}:")
                for m in ['min', 'max']:
                    print(lightgrey(f"        {m}:"), f"{geometry_crop[k][m]['value']}",
                        lightgrey(f"shot no."), f"{geometry_crop[k][m]['shot_no']} ({geometry_crop[k][m]['shot_start']})")

            print_lightcyan(f"  resized image (fit to width ignored), width:")
            print(lightgrey(f"    target:"), f"{geometry_resized_width['target']}")
            for m in ['min', 'max']:
                print(lightgrey(f"    {m}:"), f"{geometry_resized_width[m]['value']}",
                      lightgrey(f"shot no."), f"{geometry_resized_width[m]['shot_no']} ({geometry_resized_width[m]['shot_start']})")

            print_lightcyan(f"  shots without geometry settings ({len(geometry_crop['undefined'])}):")
            print("    ", geometry_crop['undefined'])

            print_lightcyan(f"  shots using default geometry ({len(geometry_crop['default'])}):")
            print("    ", geometry_crop['default'])

            print_lightcyan(f"  erroneous shot dimensions ({len(geometry_resized_width['erroneous_shots'])}):")
            print("    ", geometry_resized_width['erroneous_shots'])

            print_lightcyan(f"  erroneous shot dimensions corrected by \'fit to width\' ({len(geometry_resized_width['fit_to_width'])}):")
            print("    ", geometry_resized_width['fit_to_width'])


        # Shots whiche are cropped after resize
        cropped_after_resize = geometry_resized_width['crop_2']
        print_lightcyan(f"  Cropped after resized ({len(cropped_after_resize['list'])}):")
        print(lightgrey(f"     max:"), f"{cropped_after_resize['max']['value']}",
            lightgrey(f"shot no."), f"{cropped_after_resize['max']['shot_no']} ({cropped_after_resize['max']['shot_start']})")


        # Stabilize
        print_lightgreen(f"\nstabilize (deshake):", end=' ')
        print(f"{len(stabilize['enabled_list'])}/{shot_count}")
        print_lightcyan(f"  Shots without deshake:")
        print("    ", stabilize['disabled_list'])



