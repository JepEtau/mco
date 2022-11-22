# -*- coding: utf-8 -*-

import sys
sys.path.append('../scripts')
from pprint import pprint
from logger import log

from PySide6.QtCore import (
    QEvent,
    QObject,
    QPoint,
    QSize,
    Qt,
    Signal,
)
from PySide6.QtWidgets import (
    QApplication,
    QListWidgetItem,
    QWidget,
)

from curves_editor.ui.widget_curves_editor_ui import Ui_widget_curves_editor
from curves_editor.widget_rgb_curves import Widget_rgb_curves
from curves_editor.widget_curves_browser import Widget_curves_browser

from common.sylesheet import set_stylesheet

from utils.common import K_GENERIQUES, K_PARTS, K_ALL_PARTS
from curves_editor.model_curves_editor import Model_curves_editor

class Widget_curves_editor(QWidget, Ui_widget_curves_editor):
    signal_action = Signal(str)
    signal_directory_changed = Signal(dict)
    signal_filter_by_changed = Signal(dict)
    signal_select_image = Signal(str)
    signal_save_curves = Signal(dict)
    signal_backup_curves = Signal(dict)
    signal_set_shot_curves = Signal(dict)
    signal_reset_shot_curves = Signal(str)
    signal_reset_curves = Signal(str)
    signal_mark_shot_as_modified = Signal(str)
    signal_save_database = Signal(dict)

    def __init__(self, ui, model:Model_curves_editor):
        super(Widget_curves_editor, self).__init__()

        self.setupUi(self)
        self.model = model
        self.ui = ui

        # Setup and patch ui
        self.setAutoFillBackground(True)
        self.setWindowFlags(Qt.Tool)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setWindowModality(Qt.NonModal)

        self.list_images.setMinimumHeight(200)
        self.list_images.setAutoScroll(True)

        # Variables
        self.episodes_and_parts = dict()
        self.isAltModifierPressed = False
        self.previous_position = None

        self.current_shot_no = -1

        step_labels = self.model.get_step_labels()
        self.comboBox_step.clear()
        self.comboBox_step.addItem('')
        for s in step_labels:
            self.comboBox_step.addItem(s)

        # RGB curves graph
        self.widget_rgb_curves = Widget_rgb_curves(self.ui)
        self.layout_rgb_curves.replaceWidget(self.widget_rgb_curves_tmp, self.widget_rgb_curves)
        self.widget_rgb_curves_tmp.deleteLater()
        self.widget_rgb_curves.set_model(self.model)
        self.widget_rgb_curves.widget_rgb_graph.signal_graph_modified.connect(self.event_curves_modified)


        # Curves browser
        self.widget_curves_browser = Widget_curves_browser(self.ui, self.model)
        self.layout_curves_editor.replaceWidget(self.widget_curves_browser_tmp, self.widget_curves_browser)
        self.widget_curves_browser_tmp.deleteLater()
        self.widget_curves_browser.signal_save_curves_as[str].connect(self.event_save_curves_and_shot)
        self.widget_curves_browser.signal_select_curves[str].connect(self.select_curves)
        self.widget_curves_browser.signal_backup_curves[str].connect(self.backup_curves)

        # Events for widgets that are always visible
        self.combobox_episode.currentIndexChanged['int'].connect(self.event_episode_changed)
        self.combobox_part.currentIndexChanged['int'].connect(self.event_part_changed)
        self.comboBox_step.currentIndexChanged['int'].connect(self.event_step_changed)
        self.combobox_edition.currentIndexChanged['int'].connect(self.event_edition_changed)
        self.comboBox_filter_id.currentIndexChanged['int'].connect(self.event_filter_id_changed)

        self.list_images.itemSelectionChanged.connect(self.event_select_image)

        self.list_shots.setAutoScroll(True)
        # self.list_shots.itemClicked.connect(self.event_select_shot)
        self.list_shots.itemSelectionChanged.connect(self.event_select_shot)
        self.pushButton_reset_filter_by_shot.clicked.connect(self.event_reset_filter_by_shot)
        self.pushButton_filter_by_shot_todo.clicked.connect(self.event_filter_by_shot_todo)

        self.pushButton_reset_to_initial_curves.clicked.connect(self.event_reset_to_initial_curve)
        self.pushButton_reset_to_initial_curves.setEnabled(False)
        self.pushButton_remove_shot_curve.clicked.connect(self.event_remove_shot_curve)
        self.pushButton_save_database.clicked.connect(self.event_save_database)

        self.checkBox_fit_image_to_window.stateChanged['int'].connect(self.event_fit_image_to_window_changed)

        # Connect signals
        self.model.signal_selected_directory_changed[dict].connect(self.event_directory_changed)
        self.model.signal_refresh_framelist[list].connect(self.refresh_image_list)
        self.model.signal_display_frame[dict].connect(self.refresh_frame_properties)
        self.model.signal_refresh_frame_properties[dict].connect(self.refresh_frame_properties)
        self.model.signal_refresh_modified_shots[list].connect(self.event_refresh_modified_shots)
        self.model.signal_refresh_shotlist[list].connect(self.event_refresh_shotlist)

        self.list_images.verticalScrollBar().installEventFilter(self)
        self.list_images.installEventFilter(self)

        self.set_enabled(False)
        set_stylesheet(self)
        self.adjustSize()



    def set_enabled(self, enabled):
        log.info("set enabled: %s" % ('true' if enabled else 'false'))
        self.widget_curves_browser.set_enabled(enabled)
        self.widget_rgb_curves.set_enabled(enabled)

        self.pushButton_reset_to_initial_curves.setEnabled(enabled)
        self.pushButton_reset_to_initial_curves.setEnabled(enabled)
        self.pushButton_remove_shot_curve.setEnabled(enabled)
        self.pushButton_save_database.setEnabled(enabled)
        self.checkBox_fit_image_to_window.setEnabled(enabled)
        self.pushButton_change_preview_options.setEnabled(enabled)

        # Selection is always allowed
        self.combobox_edition.setEnabled(True)
        self.combobox_episode.setEnabled(True)
        self.comboBox_step.setEnabled(True)
        self.comboBox_filter_id.setEnabled(True)
        self.list_shots.setEnabled(True)
        self.pushButton_filter_by_shot_todo.setEnabled(True)
        self.pushButton_reset_filter_by_shot.setEnabled(True)


    def event_minimize(self):
        log.info("minimize button clicked")
        self.signal_action.emit('minimize')


    def event_exit(self):
        log.info("exit button clicked")
        self.signal_action.emit('exit')


    def closeEvent(self, event):
        self.signal_action.emit('exit')


    def get_preferences(self):
        k_ep = ''
        if (self.combobox_episode.currentText() != ' '
        and self.combobox_episode.currentText() != ''):
            k_ep = int(self.combobox_episode.currentText())
        preferences = {
            'tools': {
                'geometry': self.geometry().getRect(),
                'episode': k_ep,
                'part': self.combobox_part.currentText(),
                # 'fit_image_to_window': self.checkBox_fit_image_to_window.isChecked(),
            },
            'selected': {
                'k_ed': self.combobox_edition.currentText(),
                'step': self.comboBox_step.currentText(),
                'filter_id': self.comboBox_filter_id.currentText(),
                'shots': list()
            }
        }

        if preferences['selected']['filter_id'] != '':
            preferences['selected']['filter_id'] = int(preferences['selected']['filter_id'])

        # for c_str, c in self.checkbox_filter_id:
        #     if not c.isChecked():
        #         preferences['hide']['filter_id'].append(c_str)

        return preferences



    def set_initial_options(self, preferences:dict):
        log.info("set_initial_options")
        s = preferences['tools']
        # print("%s:set_initial_options: " % (__name__), s)

        # Episode
        self.refresh_combobox_episode()
        self.combobox_episode.blockSignals(True)
        saved_ep_no = s['episode']
        if saved_ep_no == 0:
            print("none selected")
            self.combobox_episode.setCurrentText(" ")
        else:
            index = self.combobox_episode.findText(str(saved_ep_no))
            self.combobox_episode.setCurrentIndex(index)
        self.combobox_episode.blockSignals(False)

        # Part
        self.refresh_combobox_part()
        self.combobox_part.blockSignals(True)
        self.combobox_part.setCurrentText(s['part'])
        if s['part'] in K_ALL_PARTS:
            index = self.combobox_part.findText(s['part'])
            self.combobox_part.setCurrentIndex(index)
        self.combobox_part.blockSignals(False)

        # Editions
        # Remove all from combobox after loading the folder
        self.combobox_edition.clear()

        # Filter ids
        self.comboBox_filter_id.clear()

        # Shots
        self.list_shots.clear()

        # Fit image to window
        # self.checkBox_fit_image_to_window.setChecked(s['fit_image_to_window'])

        # Filter by...
        # self.checkBox_filter_ids_all_none.blockSignals(True)
        # self.checkBox_steps_all_none.setChecked(True)
        # self.checkBox_filter_ids_all_none.blockSignals(False)

        # self.list_images.adjustSize()
        self.setMaximumSize(QSize(400, 100))
        self.adjustSize()

        # Geometry
        self.move(s['geometry'][0], s['geometry'][1])



    def refresh_browsing_folder(self, episodes_and_parts:dict):
        log.info("refresh combobox_episode")
        self.episodes_and_parts = episodes_and_parts
        if len(episodes_and_parts.keys()) > 0:
            self.refresh_combobox_episode()
            self.refresh_combobox_part()
            self.set_enabled(True)
            self.event_part_changed()
        else:
            self.refresh_combobox_episode()
            self.refresh_combobox_part()
            self.set_enabled(False)
            self.list_images.clear()


    def refresh_combobox_episode(self):
        episodes = sorted(list(self.episodes_and_parts.keys()))

        self.combobox_episode.blockSignals(True)
        self.combobox_episode.clear()

        for k_ep in episodes:
            if k_ep == ' ' or k_ep == '':
                self.combobox_episode.addItem(' ')
            else:
                self.combobox_episode.addItem(str(int(k_ep[2:])))

        self.combobox_episode.setEnabled(True)
        self.combobox_episode.blockSignals(False)



    def refresh_combobox_part(self, index=-1):
        self.combobox_part.blockSignals(True)

        # print("%s:refresh_combobox_part: " % (__name__))
        saved_part = self.combobox_part.currentText()

        self.combobox_part.clear()
        if index != -1:
            # index is the new selected episode
            selected_ep_str = self.combobox_episode.itemText(index)
        else:
            selected_ep_str = self.combobox_episode.currentText()

        # print("\tselected_ep_str: [%s]" % (selected_ep_str))
        # print("\tupdate combobox_part:")
        if len(self.episodes_and_parts.keys()) > 0:
            if selected_ep_str == ' ' or selected_ep_str == '':
                for k_p in K_GENERIQUES:
                    if k_p in self.episodes_and_parts[' ']:
                        self.combobox_part.addItem(k_p)
                        # print("\t[%s]" % (k_p))
            elif selected_ep_str != '':
                k_ep = 'ep%02d' % (int(selected_ep_str))
                for k_p in K_PARTS:
                    if k_p in self.episodes_and_parts[k_ep]:
                        self.combobox_part.addItem(k_p)
                        # print("\t[%s]" % (k_p))

        # Restore the previous part if exists
        i = self.combobox_part.findText(saved_part)
        new_index = i if i != -1 else 0
        self.combobox_part.setCurrentIndex(new_index)

        if self.combobox_part.count() > 0:
            self.combobox_part.setEnabled(True)
        else:
            self.combobox_part.setEnabled(False)
        self.combobox_part.blockSignals(False)


    def set_preview_options(self, mode:str):
        if mode == 'splitted':
            self.pushButton_change_preview_options.setText('splitted')
        elif mode == 'preview':
            self.pushButton_change_preview_options.setText('preview')
        else:
            self.pushButton_change_preview_options.setText('original')


    def event_directory_changed(self, values:dict):
        log.info("directory has been parsed, refresh browser: %s:%s" % (values['k_ep'], values['k_part']))
        print("\n%s:event_refresh:" % (__name__))
        # pprint(values)
        # print("---")

        # Episode
        k_ep = values['k_ep']
        ep_no_str = str(int(k_ep[2:])) if (k_ep != '' and  k_ep != ' ') else ''
        if self.combobox_episode.currentText() != ep_no_str:
            i = self.combobox_episode.findText(ep_no_str)
            self.combobox_episode.blockSignals(True)
            new_index = i if i != -1 else 0
            self.combobox_episode.setCurrentIndex(new_index)
            self.combobox_episode.blockSignals(False)

        # Part
        if self.combobox_part.currentText() != values['k_part']:
            i = self.combobox_part.findText(values['k_part'])
            self.combobox_part.blockSignals(True)
            new_index = i if i != -1 else 0
            self.combobox_part.setCurrentIndex(new_index)
            self.combobox_part.blockSignals(False)

        # Editions
        self.combobox_edition.blockSignals(True)
        self.combobox_edition.clear()
        self.combobox_edition.addItem('')
        for edition in values['editions']:
            self.combobox_edition.addItem(edition)
        i = self.combobox_edition.findText(values['selected']['k_ed'])
        new_index = i if i != -1 else 0
        self.combobox_edition.setCurrentIndex(new_index)
        self.combobox_edition.blockSignals(False)

        # Steps
        i = self.comboBox_step.findText(values['selected']['step'])
        self.comboBox_step.blockSignals(True)
        new_index = i if i != -1 else 0
        self.comboBox_step.setCurrentIndex(i)
        self.comboBox_step.blockSignals(False)

        # Filter ids
        self.comboBox_filter_id.blockSignals(True)
        self.comboBox_filter_id.clear()
        self.comboBox_filter_id.addItem('')
        for filter_id in values['filter_ids']:
            self.comboBox_filter_id.addItem("%03d" % (filter_id))
        i = self.comboBox_filter_id.findText(values['selected']['filter_id'])
        new_index = i if i != -1 else 0
        self.comboBox_filter_id.setCurrentIndex(new_index)
        self.comboBox_filter_id.blockSignals(False)


        # Shots
        self.list_shots.blockSignals(True)
        self.list_shots.clear()
        for no in values['shotnames']:
            self.list_shots.addItem(QListWidgetItem('%05d' % (no)))

        if len(values['selected']['shots']) != 0:
            # select partial
            for no in values['selected']['shots']:
                i = self.list_shots.findText('%05d' % (no))
                if i != -1:
                    _font = self.list_shots.item(i).font()
                    _font.setBold(True)
                    self.list_shots.item(i).setFont(_font)
        self.list_shots.blockSignals(False)

        filters = self.filter_by()
        self.signal_filter_by_changed.emit(filters)


    def event_refresh_shotlist(self, shotlist:list):
        self.list_shots.blockSignals(True)
        self.list_shots.clear()
        for no in shotlist:
            self.list_shots.addItem(QListWidgetItem("%03d" % (no)))
        self.list_shots.blockSignals(False)


    def event_refresh_modified_shots(self, shotlist:list):
        """ Refresh the list of shot to indicates that this shot is modified
        """
        # Do not allow to change directory if there is at least one modified shot
        if len(shotlist) == 0:
            self.combobox_episode.setEnabled(True)
            self.combobox_part.setEnabled(True)
        else:
            self.combobox_episode.setEnabled(False)
            self.combobox_part.setEnabled(False)

        self.list_shots.blockSignals(True)
        for row_no in range(self.list_shots.count()):
            w = self.list_shots.item(row_no)
            shot_no_str = w.text().replace('*', '')
            if int(shot_no_str) in shotlist:
                w.setText('*' + shot_no_str)
            else:
                w.setText(shot_no_str)
        self.list_shots.blockSignals(False)



    def event_filter_id_changed(self, index):
        log.info("changed filter_id")
        filters = self.filter_by()
        self.signal_filter_by_changed.emit(filters)



    def event_reset_filter_by_shot(self):
        """ Show all shots no.
        """
        log.info("reset shot selection")
        self.list_shots.blockSignals(True)
        self.list_shots.clearSelection()
        for i in range(self.list_shots.count()):
            item = self.list_shots.item(i)
            _font = item.font()
            _font.setBold(False)
            item.setFont(_font)
        self.list_shots.blockSignals(False)

        filters = self.filter_by()
        filters['todo'] = False
        print("\nevent_reset_filter_by_shot:")
        pprint(filters)
        print("\n")
        self.signal_filter_by_changed.emit(filters)


    def event_filter_by_shot_todo(self):
        """ List only the shots that have no defined curves
        """
        # Deselect all previously selected shots
        self.list_shots.blockSignals(True)
        self.list_shots.clearSelection()
        for i in range(self.list_shots.count()):
            item = self.list_shots.item(i)
            _font = item.font()
            _font.setBold(False)
            item.setFont(_font)
        self.list_shots.blockSignals(False)

        # Set filters and patch it
        filters = self.filter_by()
        filters['todo'] = True
        self.signal_filter_by_changed.emit(filters)


    def event_select_shot(self):
        log.info("select shot(s)")

        k_curves = self.widget_curves_browser.get_selected_curve_name()
        self.backup_curves(k_curves)

        for i in range(self.list_shots.count()):
            item = self.list_shots.item(i)
            _font = item.font()
            if item in self.list_shots.selectedItems():
                _font.setBold(True)
            else:
                _font.setBold(False)
            item.setFont(_font)

        filters = self.filter_by()
        self.signal_filter_by_changed.emit(filters)


    def event_reset_curves_to_initial(self):
        log.info("reload curves")
        k_curves = self.widget_curves_browser.get_selected_curve_name()
        self.widget_curves_browser.mark_curve_as_modified(False)

        self.signal_reset_curves.emit(k_curves)
        # self.pushButton_reset_to_initial_curves.setEnabled(False)
        # self.signal_reset_shot_curves.emit(self.list_images.currentItem().text())

    def event_reset_to_initial_curve(self):
        log.info("event_reset_to_initial_curve")
        self.pushButton_reset_to_initial_curves.setEnabled(False)
        self.signal_reset_shot_curves.emit(self.list_images.currentItem().text())
        # self.list_images.setFocus()

    def event_remove_shot_curve(self):
        # Select an empty curve
        self.widget_curves_browser.deselect_curve_name()
        self.select_curves('')


    def event_save_database(self):
        k_curves = self.widget_curves_browser.get_selected_curve_name()
        log.info("save database: %s" % (k_curves))
        self.widget_curves_browser.mark_curve_as_modified(is_modified=False)
        self.pushButton_reset_to_initial_curves.setEnabled(False)
        self.signal_save_database.emit({
            'k_curves': k_curves,
            'channels': self.widget_rgb_curves.widget_rgb_graph.get_curves_channels(),
            'image_name': self.list_images.currentItem().text()
        })


    def filter_by(self):
        ep_no_str = self.combobox_episode.currentText()
        if ep_no_str != '' and ep_no_str != ' ':
            ep_no_str = 'ep%02d' % (int(ep_no_str))
        filter_by_dict = {
            'k_ed': self.combobox_edition.currentText(),
            'k_ep': ep_no_str,
            'k_part': self.combobox_part.currentText(),
            'step': self.comboBox_step.currentText(),
            'filter_id': self.comboBox_filter_id.currentText(),
            'shots': list(),
            'todo': False
        }

        if filter_by_dict['filter_id'] != '':
            filter_by_dict['filter_id'] = int(filter_by_dict['filter_id'])

        for item in self.list_shots.selectedItems():
            filter_by_dict['shots'].append(int(item.text().replace('*', '')))

        return filter_by_dict




    def refresh_frame_properties(self, frame):
        shot_no_str = '' if frame is None else '%05d' % (frame['shot_no'])
        k_curves = '' if frame is None else frame['k_curves']

        # Refresh properties
        self.label_frame_no.setText('')
        self.label_shot_no.setText('')
        self.label_step.setText('')
        self.label_dimension.setText('')
        self.label_curve.setText('')
        self.label_filter_id.setText('')
        if frame is not None:
            # self.label_edition.setText("%s, %s, %s" % (
            #     frame['k_ed'],
            #     frame['k_ep'],
            #     frame['k_part']))
            self.label_frame_no.setText("frame no. %d" % (frame['no']))
            self.label_step.setText("%s" % (frame['step']))
            self.label_filter_id.setText("   %03d" % (frame['filter_id']))
            # self.label_dimension.setText("%dx%d" % (frame['dimensions']['w'], frame['dimensions']['h']))
            self.label_shot_no.setText("shot no. %d" % (frame['shot_no']))
            self.label_curve.setText(frame['k_curves_initial'])


        # Refresh the list of shots: select current shot
        for i in range(self.list_shots.count()):
            item = self.list_shots.item(i)
            _font = item.font()
            if item in self.list_shots.selectedItems():
                _font.setBold(True)
            else:
                _font.setBold(False)
            if shot_no_str != '' and shot_no_str == item.text():
                _font.setBold(True)
            item.setFont(_font)

        # Refresh the current curve name
        self.widget_curves_browser.set_current_curve_name(k_curves)
        # self.list_images.setFocus()






    ### Curves ###

    def select_curves(self, curve_name):
        image_name = self.list_images.currentItem().text()
        log.info("selected %s for image %s" % (curve_name, image_name))
        self.pushButton_reset_to_initial_curves.setEnabled(True)
        self.signal_set_shot_curves.emit({
            'k_curves': curve_name,
            'image_name': image_name
        })

    def backup_curves(self, k_curves):
        channels = self.widget_rgb_curves.widget_rgb_graph.get_curves_channels()
        if channels is not None and k_curves != '':
            self.signal_backup_curves.emit({
                'k_curves': k_curves,
                'channels': channels,
            })


    def event_curves_modified(self, modification):
        # log.info("action on curves: %s" % (modification))
        if modification not in ['loaded', 'reset_all']:
            self.widget_curves_browser.mark_curve_as_modified(is_modified=True)
            self.pushButton_reset_to_initial_curves.setEnabled(True)
            self.signal_mark_shot_as_modified.emit(self.list_images.currentItem().text())


    def event_save_curves_and_shot(self, curve_name=""):
        log.info("save curve %s for shot specified by image name" % (curve_name))
        # if curve_name != "":
        #     self.event_save_curves_as(curve_name)

        channels = self.widget_rgb_curves.widget_rgb_graph.get_curves_channels()
        # if curves is not None:
        self.signal_save_curves.emit({
            'k_curves': curve_name,
            'channels': channels,
            'image_name': self.list_images.currentItem().text()
        })



    def wheelEvent(self, event):
        # print(QApplication.focusObject())
        if QApplication.focusObject() is self.widget_curves_browser.list_curve_names:
            self.widget_curves_browser.wheelEvent(event)
        event.accept()
        return True


    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        # Filter press/release events
        if event.type() == QEvent.Wheel:
            if QApplication.focusObject() is self.list_images:
                if event.angleDelta().y() > 0:
                    self.select_previous_image()
                elif event.angleDelta().y() < 0:
                    self.select_next_image()
                event.accept()
                return True
        elif event.type() == QEvent.KeyPress:
            return self.ui.keyPressEvent(event)
        return super().eventFilter(watched, event)

    # def event(self, event: QEvent) -> bool:
    #     print("%s: widget_curves_editor::event: " % (__name__), event.type())
    #     # return self.list_images.eventFilter(object, event)
    #     return super().event(event)



    ### Other events ###


    # def eventFilter(self, object, event):
    #     if event.type() == QEvent.Wheel:
    #         # print(QApplication.focusObject())
    #         # if QApplication.focusObject() is self.widget_curves_browser.list_curve_names:
    #         #     print("Select following/previous curves")
    #         # else:

    #         # # log.info("%s:eventFilter: wheel event" % (__name__))
    #         # if event.angleDelta().y() > 0:
    #         #     # log.info("wheelEvent:Previous")
    #         #     self.select_previous_image()
    #         # else:
    #         #     # log.info("wheelEvent:Next")
    #         #     self.select_next_image()

    #         return self.ui.wheelEvent(event)

    #     # elif event.type() != QEvent.Timer:
    #     #     print("eventFilter", event.type())
    #     # return super(Widget_curves_editor, self).eventFilter(object, event)
    #     # pprint(object)
    #     return self.list_images.eventFilter(object, event)




    def mousePressEvent(self, event):
        self.previous_position = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.previous_position is not None:
            delta = QPoint(event.globalPos() - self.previous_position)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.previous_position = event.globalPos()



    def keyPressEvent(self, event):
        key = event.key()
        modifier = event.modifiers()

        if modifier & Qt.ControlModifier:
            if key == Qt.Key_S:
                log.info("save curve and database")
                self.event_save_database()
                event.accept()
            elif key == Qt.Key_Z:
                print(QApplication.focusObject())
                if QApplication.focusObject() is self.widget_curves_browser.list_curve_names:
                    log.info("reset curves to initial values")
                    # print("self.list_curve_names")
                    self.event_reset_curves_to_initial()
                else:
                    log.info("reset shot to saved curves")
                    self.event_reset_to_initial_curve()
                event.accept()
                return

        elif key == Qt.Key_Up:
            log.info("Previous")
            self.select_previous_image()

        elif key == Qt.Key_Down:
            log.info("Next")
            self.select_next_image()

        else:
            accepted = self.widget_rgb_curves.keyPressEvent(event)
            if not accepted:
                super(Widget_curves_editor, self).keyPressEvent(event)


