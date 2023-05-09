# -*- coding: utf-8 -*-
import sys


from filters.python_geometry import IMG_BORDER_HIGH_RES
from filters.filters import calculate_geometry_parameters
from copy import deepcopy

from pprint import pprint
from logger import log
from utils.pretty_print import *

from PySide6.QtCore import (
    Signal,
)

from filters.utils import FINAL_FRAME_WIDTH
from utils.nested_dict import nested_dict_set


class Controller_geometry():

    def __init__(self):
        super(Controller_geometry, self).__init__()


    def event_geometry_modified(self, event:dict):
        """event:
            - element       'shot', 'target'
            - type          'select', 'remove', 'set', 'discard'
            - parameter     'crop_top', 'crop_right', 'crop_left', 'crop_down', 'width', 'shot'
            - value         int, str
        """
        k_ep = self.current_frame['k_ep']
        k_part = self.current_frame['k_part']
        shot = self.current_shot()
        crop_min = 0
        try:
            stabilize_settings = self.model_database.get_shot_stabilize_settings(shot=shot)
            if stabilize_settings['enable']:
                crop_min = -IMG_BORDER_HIGH_RES
            # print(f"event_geometry_modified, crop_min={crop_min}")
        except:
            pass

        # print_green("\nevent_geometry_modified for %s:%s" % (k_ep, k_part))
        # print(event)
        element = event['element']
        event_type = event['type']
        parameter = event['parameter']
        value = event['value']


        # Select between shot and default shot
        if element == 'shot' and event_type == 'select' and parameter == 'shot':
            if value == 'default_shot':
                # Remove shot geometry
                self.model_database.remove_shot_geometry(shot=shot)
            elif value == 'shot':
                # Use custom geometry, copy from default
                self.model_database.set_shot_geometry(shot=shot,
                    geometry=deepcopy(self.model_database.get_default_shot_geometry(shot)))
            self.set_modification_status('geometry', True)

        # Modify target width
        if element == 'target' and parameter == 'width':
            if k_part in ['g_asuivre', 'g_reportage']:
                sys.exit(print_red("bug: target width shall never be modified when editing %s" % (k_part)))

            if event_type == 'set':
                geometry = self.model_database.get_target_geometry(k_ep=k_ep, k_part=k_part).copy()
                if value == 'auto':
                    # TODO: remove auto
                    # This will have to be calculated from shot
                    geometry['w'] = -1
                else:
                    geometry['w'] = min(FINAL_FRAME_WIDTH, max(geometry['w'] + value, 800))
                self.model_database.set_target_geometry(k_ep=k_ep, k_part=k_part, geometry=geometry)

            elif event_type == 'discard':
                self.model_database.discard_target_geometry_modifications(k_ep=k_ep, k_part=k_part)


        # Modify shot properties: crop, etc.
        if element in ['default_shot', 'shot'] and event_type == 'set':
            # Modify parameter
            if element == 'shot':
                geometry=deepcopy(self.model_database.get_shot_geometry(shot))
            else:
                geometry=deepcopy(self.model_database.get_default_shot_geometry(shot))

            if 'crop' in parameter:
                if geometry is not None:
                    crop_top, c_bottom, c_left, c_right = geometry['crop']
                else:
                    geometry = {'crop':  [0, 0, 0, 0]}
                    crop_top, c_bottom, c_left, c_right = geometry['crop']

                if parameter == 'crop_top':
                    geometry['crop'][0] = max(crop_min, min(crop_top + value, 400))

                elif parameter == 'crop_bottom':
                    geometry['crop'][1] = max(crop_min, min(c_bottom - value, 400))

                elif parameter == 'crop_left':
                    geometry['crop'][2] = max(crop_min, min(c_left + value, 400))

                elif parameter == 'crop_right':
                    geometry['crop'][3] = max(crop_min, min(c_right + value, 400))

            elif parameter in ['keep_ratio', 'fit_to_width']:
                print_purple(f"\n\n\nparameter: {parameter}, element={element}")
                nested_dict_set(geometry, value, parameter)
            else:
                sys.exit(print_red("event_geometry_modified: error : unrecognized parameter [%s]" % (parameter)))

            if element == 'shot':
                self.model_database.set_shot_geometry(shot=shot, geometry=geometry)
            else:
                self.model_database.set_default_shot_geometry(shot=shot, geometry=geometry)
            self.set_modification_status('geometry', True)

        # Refresh all frames of this shot
        self.refresh_geometry_for_each_frame(shot=shot)

        self.signal_reload_frame.emit()
        return


    def refresh_geometry_for_each_frame(self, shot):
        # log.info(f"{shot['k_ed']}:{shot['k_ep']}:{shot['k_part']}:{shot['no']}, refresh geometry for each frame")
        # target_geometry = self.model_database.get_target_geometry(k_ep=shot['k_ep'], k_part=shot['k_part'])
        if len(self.frames[shot['no']]) == 0:
            # No images
            print_orange(f"refresh geometry: no frames. {shot['k_ed']}:{shot['k_ep']}:{shot['k_part']}:{shot['no']}")
            return

        if shot['dst']['k_part'] in ['g_asuivre', 'g_reportage']:
            k_part_src = shot['dst']['k_part'][2:]
        else:
            k_part_src = shot['dst']['k_part']
        target_geometry = self.model_database.get_target_geometry(k_ep=shot['dst']['k_ep'], k_part=k_part_src)

        default_shot_geometry = self.model_database.get_default_shot_geometry(shot=shot)
        shot_geometry = self.model_database.get_shot_geometry(shot=shot)

        stabilize_settings = self.model_database.get_shot_stabilize_settings(shot=shot)
        # TODO what to do if is erroneous?
        try:
            is_stabilize_enabled = stabilize_settings['enable']
        except:
            is_stabilize_enabled = False

        virtual_shot = {
            'geometry': {
                'shot': deepcopy(shot_geometry) if shot_geometry is not None else None,
                'default': deepcopy(default_shot_geometry) if default_shot_geometry is not None else None,
                'target': target_geometry,
            },
            'last_task': shot['last_task'],
        }
        print_purple("virtual_shot")
        pprint(virtual_shot)

        frame = self.frames[shot['no']][0]
        shot_geometry_values = calculate_geometry_parameters(shot=virtual_shot, img=frame['cache_initial'])
        is_geometry_erroneous = False if shot_geometry_values['pad_error'] is None else True
        pprint(shot_geometry_values)

        for frame in self.frames[shot['no']]:
            # if shot['dst']['k_part'] in ['g_asuivre', 'g_reportage']:
            #     k_part_src = shot['dst']['k_part'][2:]
            # else:
            #     k_part_src = shot['dst']['k_part']

            # target_geometry = self.model_database.get_target_geometry(k_ep=shot['dst']['k_ep'], k_part=k_part_src)
            nested_dict_set(frame, {
                'target': target_geometry,
                'default': default_shot_geometry,
                'shot': shot_geometry,
                # Used when the width of the cropped img  for the shot < width of the cropped img of the part
                # is updated by the generate function
                'error': False,
            }, 'geometry')
            frame['geometry_values'] = shot_geometry_values

            # TODO is this flag useful?
            frame['geometry']['error'] = is_geometry_erroneous


    def event_geometry_discard_requested(self):
        log.info("discard modifications requested")
        shot = self.current_shot()
        self.model_database.discard_default_shot_geometry_modifications(shot)
        self.model_database.discard_shot_geometry_modifications(shot)
        self.refresh_geometry_for_each_frame(shot=shot)
        self.signal_reload_frame.emit()
        self.set_modification_status('geometry', False)


    def event_geometry_save_requested(self):
        k_part = self.current_selection['k_part']
        db = self.model_database.database()
        if k_part in ['g_debut', 'g_fin']:
            k_ed = self.current_frame['k_ed']
            k_ep = self.current_frame['k_ep']
        else:
            k_ep = self.current_selection['k_ep']
            k_ed = self.current_frame['k_ed']
        # pprint(self.current_selection)
        shot = self.current_shot()

        self.model_database.save_shot_geometry_database(k_ep=k_ep, k_part=k_part)
        self.signal_is_saved.emit('geometry')
        self.set_modification_status('geometry', False)



    def event_geometry_discard_target_requested(self):
        log.info("discard modifications requested")
        k_part = self.current_selection['k_part']
        k_ep = self.current_frame['k_ep']
        self.model_database.discard_target_geometry_modifications(k_ep=k_ep, k_part=k_part)
        self.refresh_geometry_for_each_frame(shot=self.current_shot())
        self.signal_reload_frame.emit()


    def event_geometry_save_target_requested(self):
        k_part = self.current_selection['k_part']
        db = self.model_database.database()
        if k_part in ['g_debut', 'g_fin']:
            k_ed = self.current_frame['k_ed']
            k_ep = self.current_frame['k_ep']
        else:
            k_ep = self.current_selection['k_ep']
            k_ed = self.current_frame['k_ed']
        # pprint(self.current_selection)
        shot = self.shots[self.current_frame['shot_no']]

        self.model_database.save_target_geometry_database(k_ep=k_ep, k_part=k_part)
        self.signal_is_saved.emit('geometry')

