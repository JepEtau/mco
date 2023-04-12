# -*- coding: utf-8 -*-
import sys
sys.path.append('../scripts')
from PySide6.QtCore import (
    Signal,
)
from copy import deepcopy
from utils.pretty_print import *
from pprint import pprint
from logger import log

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

        # Modify target width
        if element == 'target' and parameter == 'width':
            if k_part in ['g_asuivre', 'g_reportage']:
                sys.exit(print_red("bug: target width shall never be modified when editing %s" % (k_part)))

            if event_type == 'set':
                geometry = self.model_database.get_target_geometry(k_ep=k_ep, k_part=k_part).copy()
                if value == 'auto':
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
                    geometry['crop'][0] = max(0, min(crop_top + value, 400))

                elif parameter == 'crop_bottom':
                    geometry['crop'][1] = max(0, min(c_bottom - value, 400))

                elif parameter == 'crop_left':
                    geometry['crop'][2] = max(0, min(c_left + value, 400))

                elif parameter == 'crop_right':
                    geometry['crop'][3] = max(0, min(c_right + value, 400))

            elif parameter in ['keep_ratio', 'fit_to_width']:
                nested_dict_set(geometry, value, parameter)
            else:
                sys.exit(print_red("event_geometry_modified: error : unrecognized parameter [%s]" % (parameter)))

            if element == 'shot':
                self.model_database.set_shot_geometry(shot=shot, geometry=geometry)
            else:
                self.model_database.set_default_shot_geometry(shot=shot, geometry=geometry)

        self.signal_reload_frame.emit()
        return


    def event_geometry_discard_requested(self):
        log.info("discard modifications requested")
        k_part = self.current_selection['k_part']
        k_ep = self.current_frame['k_ep']
        self.model_database.discard_target_geometry_modifications(k_ep=k_ep, k_part=k_part)
        self.signal_reload_frame.emit()


    def event_save_geometry_requested(self):
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

        self.model_database.save_geometry_database(k_ep=k_ep, k_part=k_part)
        self.signal_is_saved.emit('geometry')





    def get_frame_from_index(self, index):
        """ returns the replace frame unless there is no replacemed frame or
        the initial flag is set to True
        framelist contains all path for each frame of this playlist
        """
        # log.info("get_frame: get_frame from index. %d" % (index))
        # print_lightgreen("playlist: nb of frames: %d" % (len(self.playlist_frames)))
        if len(self.playlist_frames) == 0:
            return None

        frame = self.playlist_frames[index]
        frame_no = frame['frame_no']
        shot_no = frame['shot_no']
        # new shot:
        shot = self.shots[shot_no]

        if not self.preview_options['replace']['is_enabled']:

            try: del frame['replace']
            except: pass
        else:

            # print_green("\tshot no. %d, frame no. %d" % (shot_no, frame_no))
            new_frame_no = self.model_database.get_replace_frame_no(shot, frame_no)
            if new_frame_no == -1:
                frame = self.playlist_frames[index]
                try: del frame['replace']
                except: pass
            else:
                frame = self.playlist_frames[index + (new_frame_no - frame_no)]
                frame['replace'] = frame_no

        # If shot is different
        if self.current_frame is None or frame['shot_no'] != self.current_frame['shot_no']:
            is_shot_changed = True
            frame['reload_parameters'] = True
        else:
            is_shot_changed = False
            frame['reload_parameters'] = False

        # Update curves and load it into the graph
        frame['curves'] = self.model_database.get_shot_curves_selection(
            db=self.model_database.database(), shot=shot)
        if is_shot_changed:
            try:
                self.signal_load_curves.emit(frame['curves'])
                shot_list = self.model_database.get_shots_per_curves(frame['curves']['k_curves'])
                self.signal_shot_per_curves_modified.emit(shot_list)
            except:
                self.signal_load_curves.emit(None)
                self.signal_shot_per_curves_modified.emit(None)
        elif self.current_frame is None:
            self.signal_load_curves.emit(None)

        # Load current geometry
        k_part_src = shot['dst']['k_part'][2:] if shot['dst']['k_part'] in ['g_asuivre', 'g_reportage'] else shot['dst']['k_part']
        target_geometry = self.model_database.get_target_geometry(k_ep=shot['dst']['k_ep'], k_part=k_part_src)
        frame['geometry'].update({
            'target': target_geometry,
            'default': self.model_database.get_default_shot_geometry(shot=shot),
            'shot': self.model_database.get_shot_geometry(shot=shot),

            # Used when the width of the cropped img  for the shot < width of the cropped img of the part
            # is updated by the generate function
            'error': False,
        })
        # print_yellow("db_target_geometry_initial")
        # pprint(self.model_database.db_target_geometry_initial)
        # print_yellow("db_target_geometry")
        # pprint(self.model_database.db_target_geometry)
        # pprint(frame['geometry'])

        # Load new stabilize settings
        if is_shot_changed:
            settings = self.model_database.get_shot_stabilize_settings(shot=shot)
            self.signal_stabilize_settings_refreshed.emit(settings)

        # Purge image from the previous frame
        self.purge_current_frame_cache()

        # Set current frame
        self.current_frame = frame

        # Generate the image for this frame
        # now = time.time()
        options = self.preview_options
        if options is not None:

            try:
                if frame['cache_initial'] is None:
                    # The original has not yet been loaded
                    frame['cache_initial'] = cv2.imread(frame['filepath'], cv2.IMREAD_COLOR)
            except:
                frame['cache_initial'] = None
                return None

            if target_geometry['w'] == -1:
                print_lightcyan("calculate target geometry %s:%s" % (frame['k_ep'], frame['k_part']))
                # Calculate width
                geometry = calculate_geometry_parameters(shot=frame, img=frame['cache_initial'])
                target_geometry['w'] = geometry['resize']['w']
                self.model_database.set_target_geometry(
                    k_ep=frame['k_ep'], k_part=frame['k_part'],
                    geometry=target_geometry)

            frame['geometry_values'] = calculate_geometry_parameters(shot=frame, img=frame['cache_initial'])
            frame['geometry']['error'] = True if frame['geometry_values']['pad_error'] is not None else False

            index, img = generate_image(self.current_frame, preview_options=options)
            self.set_current_frame_cache(img=img)
        # print("\t%dms" % (int(1000 * (time.time() - now))))
        # else:
            # Cannot generate the image because no preview option is defined
            # The preview options will be updated by the window UI



        if is_shot_changed:
            self.signal_shot_changed.emit()

        return self.current_frame

