# -*- coding: utf-8 -*-
import sys

from PySide6.QtCore import (
    Signal,
)
from pprint import pprint
from logger import log

class Controller_rgb():
    signal_load_curves = Signal(dict)
    signal_curves_library_modified = Signal(dict)
    signal_shot_per_curves_modified = Signal(list)

    def __init__(self):
        super(Controller_rgb, self).__init__()


    def event_rgb_graph_modified(self, rgb_channels):
        shot_no = self.current_frame['shot_no']
        self.model_database.set_shot_rgb_channels(
            shot=self.shots[shot_no],
            rgb_channels=rgb_channels)
        self.signal_reload_frame.emit()


    def event_curves_selection_changed(self, k_curves:str):
        log.info("select the new curves for this shot [%s]" % (k_curves))
        shot_no = self.current_frame['shot_no']
        shot = self.shots[shot_no]
        curves = self.model_database.get_shot_curves_selection(db=self.model_database.database(),
            shot=shot)

        # Update the modifications structure to update the selection widget
        if k_curves != self.shots[shot_no]['modifications']['curves']['initial']:
            log.info("selection has changed")
            self.shots[shot_no]['modifications']['curves']['new'] = k_curves
            # Modify the selected curves in the db
            self.model_database.set_curves_selection(db=self.model_database.database(),
                shot=shot,
                k_curves=k_curves)
        else:
            # Discard the current selected curves
            self.shots[shot_no]['modifications']['curves']['new'] = None
            self.model_database.discard_curves_selection(db=self.model_database.database(),
                shot=shot)

        # Get the new selected curves
        curves = self.model_database.get_shot_curves_selection(db=self.model_database.database(),
            shot=shot)

        # Refresh the list of shot for these curves
        shot_list = self.model_database.get_shots_per_curves(k_curves)
        self.signal_shot_per_curves_modified.emit(shot_list)

        self.signal_current_shot_modified.emit(shot['modifications'])
        self.set_modification_status('curves', True)
        self.signal_load_curves.emit(curves)
        self.signal_reload_frame.emit()


    def event_discard_rgb_curves_modifications(self, k_curves:str):
        k_ed = self.current_frame['k_ed']
        k_ep = self.current_frame['k_ep']
        self.model_database.discard_rgb_curves_modifications(k_curves, k_ed, k_ep)

        # Get the initial curves
        curves = self.model_database.get_curves(self.model_database.database(),
            k_ed=k_ed, k_ep=k_ep, k_curves=k_curves)

        # Send the list of curves
        self.signal_curves_library_modified.emit(self.model_database.get_library_curves(k_ed, k_ep))

        # Reload curves
        self.signal_load_curves.emit(curves)
        self.signal_reload_frame.emit()


    def event_save_rgb_curves_as(self, curves):
        # Save the curves in the curves library
        log.info("save the curves: %s -> %s" % (curves['k_curves_current'], curves['k_curves_new']))
        # if curves['k_curves_new'] == '':
        #     log.error("No name defined in the curves struct")
        #     return

        k_part = self.current_frame['k_part']
        k_ed = self.current_frame['k_ed']
        k_ep = self.current_frame['k_ep']
        self.model_database.append_curves_to_database(
            db=self.model_database.database(),
            k_ed=k_ed,
            k_ep=k_ep,
            k_part=k_part,
            curves=curves)
        self.signal_curves_library_modified.emit(self.model_database.get_library_curves(k_ed, k_ep))

        # Modify the current selection
        if curves['k_curves_new'] is not None:
            k_curves_new = curves['k_curves_new']
            self.event_curves_selection_changed(k_curves_new)


    def event_save_curves_selection_requested(self):
        log.info("save curves selection")
        # Save the curves selected for this shot
        shot_no = self.current_frame['shot_no']
        shot = self.shots[shot_no]

        if shot['modifications']['curves']['new'] is None:
            return

        # print("event_save_curves_selection_requested %s:%s:%s:%d" % (k_ed, k_ep, k_part, shot_no))
        self.model_database.save_shot_curves_selection(db=self.model_database.database(),
            shot=shot)

        # Update the modifications structure to update the selection widget
        k_new_curves = shot['modifications']['curves']['new']
        shot['modifications']['curves'] = {
            'initial': k_new_curves,
            'new': None,
        }
        self.signal_current_shot_modified.emit(shot['modifications'])
        self.set_modification_status('curves', False)
        self.signal_is_saved.emit('curves_selection')
