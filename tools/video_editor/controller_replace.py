# -*- coding: utf-8 -*-
import sys
sys.path.append('../scripts')
from PySide6.QtCore import (
    Signal,
)
from pprint import pprint
from logger import log

class Controller_replace():
    signal_replace_list_refreshed = Signal(dict)

    def __init__(self):
        super(Controller_replace, self).__init__()

    # Replace frames
    #---------------------------------------------------------------------------
    def is_replace_allowed(self) -> bool:
        shot = self.current_shot()
        if shot is None:
            return False
        is_allowed = self.model_database.is_replace_allowed(shot=shot)
        return is_allowed


    def refresh_replace_list(self):
        # List of frames to replace
        log.info("refresh list")
        list_replace = list()
        for frame in self.playlist_frames:
            frame_no = self.model_database.get_replace_frame_no(
                    shot=self.shots[frame['shot_no']],
                    frame_no=frame['frame_no'])
            if frame_no != -1:
                list_replace.append({
                    'shot_no': frame['shot_no'],
                    'src': frame_no,
                    'dst': frame['frame_no'],
                })
        # print_lightcyan("model video editor: refresh_replace_list")
        # pprint(list_replace)
        self.signal_replace_list_refreshed.emit(list_replace)


    def get_replace_frame_no_str(self, index) -> str:
        # print("get_replace_frame_no_str: %d" % (index))
        frame_no = self.playlist_frames[index]['frame_no']
        shot_no = self.playlist_frames[index]['shot_no']
        new_frame_no = self.model_database.get_replace_frame_no(shot_no, frame_no)
        # print("get_replace_frame_no: %d -> %d" % (frame_no, new_frame_no))
        if new_frame_no != -1:
            return str(new_frame_no)
        return ''


    def get_next_replaced_frame_index(self, index):
        # TODO: replace this: use the list_replace
        # print("find following replaced frame")

        # print("\tsearch in %d -> %d" % (frame_no + 1, self.playlist_properties['start'] + self.playlist_properties['count']))
        for i in range(index + 1, self.playlist_properties['count']):
            shot_no = self.get_shot_no_from_index(i)
            shot = self.shots[shot_no]
            frame_no = shot['start'] + i
            if self.model_database.get_replace_frame_no(shot, frame_no) != -1:
                return i

        # print("\tsearch in %d -> %d" % (self.playlist_properties['start'], frame_no-1))
        for i in range(0, index-1):
            shot_no = self.get_shot_no_from_index(i)
            shot = self.shots[shot_no]
            frame_no = shot['start'] + i
            if self.model_database.get_replace_frame_no(shot_no, frame_no) != -1:
                return i
        return -1


    def event_frame_replaced(self, replace:dict):
        action = replace['action']
        frame_no = replace['dst']
        log.info("replace %d" % (frame_no))
        print("shot no= %d" % (self.current_frame['shot_no']))
        # pprint(self.playlist_frames)
        shot_src = self.current_shot()
        shot_no = shot_src['no']
        index = frame_no - self.frames[shot_no][0]['frame_no']

        if action == 'replace':
            log.info("replace: shot_no=%d, frame_no=%d (index=%d) by %d" % (shot_no, frame_no, index, replace['src']))
            self.model_database.set_replaced_frame(
                shot=shot_src,
                frame_no=frame_no,
                new_frame_no=replace['src'])
            # update the frame as it is required to refresh the list of the widget_replace
            # print("index: %d" % )
            # self.frames[shot_no][index]['replaced_by'] = self.model_database.get_replace_frame_no(shot_src, frame_no)

        elif action == 'remove':
            log.info("remove: shot_no=%d, frame_no=%d (index=%d)" % (shot_no, frame_no, index))
            self.model_database.remove_replaced_frame(shot=shot_src, frame_no=frame_no)

            # update the frame as it is required to refresh the list of the widget_replace
            # self.frames[shot_no][index]['replaced_by'] = self.model_database.get_replace_frame_no(shot_src, frame_no)

        self.refresh_replace_list()
        self.signal_reload_frame.emit()


    def event_replace_discard_requested(self):
        log.info("discard modifications requested")
        self.model_database.discard_replace_modifications()
        self.refresh_replace_list()
        self.signal_reload_frame.emit()


    def event_replace_save_requested(self):
        self.model_database.save_replace_database()
        self.signal_is_saved.emit('replace')

