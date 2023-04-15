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
    QCheckBox,
    QListWidgetItem,
    QSpacerItem,
    QWidget,
    QSizeGrip,
    QSizePolicy,
    QListView,
)

from utils.common import K_GENERIQUES, K_PARTS, K_ALL_PARTS

from common.stylesheet import set_stylesheet, set_widget_stylesheet
from viewer.ui.widget_browser_ui import Ui_widget_browser


class Widget_browser(QWidget, Ui_widget_browser):
    signal_action = Signal(str)
    signal_directory_changed = Signal(dict)
    signal_filter_by_changed = Signal(dict)
    signal_select_image = Signal(str)
    signal_close = Signal()

    def __init__(self, ui, controller):
        super(Widget_browser, self).__init__()
        self.controller = controller
        self.ui = ui

        # Set and patch ui
        self.setupUi(self)
        self.setAutoFillBackground(True)

        # self.sizegrip = QSizeGrip(self)
        # self.sizegrip.resize(16,16)
        # self.verticalLayout.addWidget(self.sizegrip, alignment=Qt.AlignBottom | Qt.AlignRight)

        self.setWindowFlags(Qt.Tool)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setWindowModality(Qt.NonModal)

        # self.display_frame_properties(None)

        self.list_images.setMinimumHeight(600)
        self.list_images.setAutoScroll(True)

        # Variables
        self.episodes_and_parts = dict()
        self.isAltModifierPressed = False
        self.previous_position = None

        # Filter by (visible/hidden)
        self.checkbox_editions = list()

        step_labels = self.model.get_step_labels()
        self.checkbox_steps = list()
        for s in step_labels:
            self.checkbox_steps.append([s, QCheckBox(s)])
            w = self.checkbox_steps[-1][1]
            self.layout_steps.addWidget(w)
            set_widget_stylesheet(w)
            self.checkbox_steps[-1][1].stateChanged['int'].connect(self.event_step_changed)

        self.checkbox_filter_ids = list()


        # Events for widgets that are always visible
        self.pushButton_minimize.clicked.connect(self.event_minimize)
        self.pushButton_exit.clicked.connect(self.event_exit)

        self.combobox_episode.currentIndexChanged['int'].connect(self.event_episode_changed)
        self.combobox_part.currentIndexChanged['int'].connect(self.event_part_changed)
        self.checkBox_editions_all_none.stateChanged['int'].connect(self.event_edition_all_none_changed)
        self.checkBox_steps_all_none.stateChanged['int'].connect(self.event_step_all_none_changed)
        self.checkBox_filter_ids_all_none.stateChanged['int'].connect(self.event_filter_id_all_none_changed)

        self.list_images.itemSelectionChanged.connect(self.event_select_image)

        self.checkBox_fit_image_to_window.stateChanged['int'].connect(self.event_fit_image_to_window_changed)


        # Connect signals
        self.model.signal_refresh_browser[dict].connect(self.event_refresh)
        self.model.signal_refresh_framelist[list].connect(self.refresh_image_list)

        self.installEventFilter(self)
        self.list_images.installEventFilter(self)
        self.list_images.verticalScrollBar().installEventFilter(self)

        # Set style
        set_stylesheet(self)
        self.adjustSize()



    def get_preferences(self):
        k_ep = ''
        if (self.combobox_episode.currentText() != ' '
        and self.combobox_episode.currentText() != ''):
            k_ep = int(self.combobox_episode.currentText())
        preferences = {
            'browser': {
                'geometry': self.geometry().getRect(),
                'episode': k_ep,
                'part': self.combobox_part.currentText(),
                'fit_image_to_window': self.checkBox_fit_image_to_window.isChecked(),
            },
            'hide': {
                'editions': list(),
                'steps': list(),
                'filter_ids': list(),
            }
        }

        for c_str, c in self.checkbox_editions:
            if not c.isChecked():
                preferences['hide']['editions'].append(c_str)
        for c_str, c in self.checkbox_steps:
            if not c.isChecked():
                preferences['hide']['steps'].append(c_str)
        for c_str, c in self.checkbox_filter_ids:
            if not c.isChecked():
                preferences['hide']['filter_ids'].append(c_str)

        return preferences



    def set_initial_options(self, preferences:dict):
        log.info("set_initial_options")
        s = preferences['browser']
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
        self.combobox_part.setCurrentText(s['k_part'])
        if s['k_part'] in K_ALL_PARTS:
            index = self.combobox_part.findText(s['k_part'])
            self.combobox_part.setCurrentIndex(index)
        self.combobox_part.blockSignals(False)

        # Fit image to window
        self.checkBox_fit_image_to_window.setChecked(s['fit_image_to_window'])

        # Filter by...
        hide_dict = preferences['hide']

        # Editions
        # Delete all, each checkbox will be added after loading the folder
        for w in self.widget_editions.findChildren(QCheckBox):
            w.deleteLater()

        # Steps
        self.checkBox_steps_all_none.blockSignals(True)
        if len(hide_dict['steps']) == len(self.checkbox_steps):
            self.checkBox_steps_all_none.setChecked(True)
        elif len(hide_dict['steps']) == 0:
            self.checkBox_steps_all_none.setChecked(False)
        else:
            self.checkBox_steps_all_none.setCheckState(Qt.PartiallyChecked)

        for c_str, c in self.checkbox_steps:
            c.blockSignals(True)
            if c_str in hide_dict['steps']:
                c.setChecked(False)
            else:
                c.setChecked(True)
            c.blockSignals(False)
        self.checkBox_steps_all_none.blockSignals(False)

        # Filters id
        for w in self.scrollArea_filter_ids.findChildren(QCheckBox):
            w.deleteLater()

        self.checkBox_filter_ids_all_none.blockSignals(True)
        self.checkBox_filter_ids_all_none.setChecked(True)
        self.checkBox_filter_ids_all_none.blockSignals(False)

        # self.list_images.adjustSize()
        self.setMaximumSize(QSize(400, 100))
        self.adjustSize()

        # Geometry
        self.move(s['geometry'][0], s['geometry'][1])



    def refresh_browsing_folder(self, episodes_and_parts:dict):
        log.info("refresh combobox_episode")
        self.episodes_and_parts = episodes_and_parts



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

        if len(self.episodes_and_parts.keys()) > 0:
            if selected_ep_str == ' ' or selected_ep_str == '':
                for k_p in K_GENERIQUES:
                    if k_p in self.episodes_and_parts[' ']:
                        self.combobox_part.addItem(k_p)
            elif selected_ep_str != '':
                k_ep = 'ep%02d' % (int(selected_ep_str))
                for k_p in K_PARTS:
                    if k_p in self.episodes_and_parts[k_ep]:
                        self.combobox_part.addItem(k_p)

        # Restore the previous part if exists
        i = self.combobox_part.findText(saved_part)
        if i != -1:
            self.combobox_part.setCurrentIndex(i)

        if self.combobox_part.count() > 0:
            self.combobox_part.setEnabled(True)
        else:
            self.combobox_part.setEnabled(False)
        self.combobox_part.blockSignals(False)



    def event_refresh(self, values:dict):
        log.info("directory has been parsed, refresh browser")
        # print("%s:event_refresh:" % (__name__))
        # pprint(values)

        # Episode
        k_ep = values['k_ep']
        ep_no_str = str(int(k_ep[2:])) if (k_ep != '' and  k_ep != ' ') else ''
        if self.combobox_episode.currentText() != ep_no_str:
            i = self.combobox_episode.findText(ep_no_str)
            if i != -1:
                self.combobox_episode.blockSignals(True)
                self.combobox_episode.setCurrentIndex(i)
                self.combobox_episode.blockSignals(False)

        # Part
        if self.combobox_part.currentText() != values['k_part']:
            i = self.combobox_part.findText(values['k_part'])
            if i != -1:
                self.combobox_part.blockSignals(True)
                self.combobox_part.setCurrentIndex(i)
                self.combobox_part.blockSignals(False)

        # Editions
        #   block widget signals and disconnect them
        self.checkBox_editions_all_none.blockSignals(True)
        self.checkBox_editions_all_none.setChecked(False)
        for c_str, c in self.checkbox_editions:
            # Disconnect all signals
            c.blockSignals(True)
            try:
                c.stateChanged.disconnect()
            except:
                pass
        #   delete wigets and associated list
        for w in self.widget_editions.findChildren(QCheckBox):
            w.deleteLater()
        self.checkbox_editions.clear()
        #   set all/none widget
        if len(values['editions']) == len(values['hide']['editions']):
            self.checkBox_editions_all_none.setChecked(False)
        elif len(values['editions']) == 0 or len(values['hide']['editions']) == 0:
            self.checkBox_editions_all_none.setChecked(True)
        else:
            self.checkBox_editions_all_none.setCheckState(Qt.PartiallyChecked)
        #   append checkbox widgets
        for e in values['editions']:
            self.checkbox_editions.append([e, QCheckBox(e)])
            w = self.checkbox_editions[-1][1]
            self.layout_editions.addWidget(w)
            set_widget_stylesheet(w)
            w.stateChanged['int'].connect(self.event_edition_changed)
        #   select/unselect checkbox and enable signals
        for c_str, c in self.checkbox_editions:
            c.blockSignals(True)
            if c_str in values['hide']['editions']:
                c.setChecked(False)
            else:
                c.setChecked(True)
            c.blockSignals(False)
        self.checkBox_editions_all_none.blockSignals(False)


        # Steps
        #   block widget signals
        self.checkBox_steps_all_none.blockSignals(True)
        self.checkBox_steps_all_none.setChecked(False)
        #   set all/none widget
        if len(values['hide']['steps']) == len(self.checkbox_steps):
            self.checkBox_steps_all_none.setChecked(False)
        elif len(values['hide']['steps']) == 0 or len(self.checkbox_steps) == 0:
            self.checkBox_steps_all_none.setChecked(True)
        else:
            self.checkBox_steps_all_none.setCheckState(Qt.PartiallyChecked)
        #   select/unselect checkbox and enable signals
        for c_str, c in self.checkbox_steps:
            c.blockSignals(True)
            if c_str in values['hide']['steps']:
                c.setChecked(False)
            else:
                c.setChecked(True)
            c.blockSignals(False)
        self.checkBox_steps_all_none.blockSignals(False)


        # Filter ids
        #   block widget signals and disconnect them
        self.checkBox_filter_ids_all_none.blockSignals(True)
        self.checkBox_filter_ids_all_none.setChecked(False)
        for c_str, c in self.checkbox_filter_ids:
            c.blockSignals(True)
            try:
                c.stateChanged.disconnect()
            except:
                pass
        #   delete wigets and associated list
        for w in self.widget_filter_ids.findChildren(QCheckBox):
            w.deleteLater()
        for w in self.widget_filter_ids.findChildren(QSpacerItem):
            w.deleteLater()
        self.checkbox_filter_ids.clear()


        if False:
            # When changing directory, enable all filter ids
            self.checkBox_filter_ids_all_none.setChecked(True)
        else:
            #   set all/none widget
            if len(values['filter_ids']) == len(values['hide']['filter_ids']):
                self.checkBox_filter_ids_all_none.setCheckState(Qt.Checked)
            elif len(values['filter_ids']) == 0 or len(values['hide']['filter_ids']) == 0:
                self.checkBox_filter_ids_all_none.setCheckState(Qt.Unchecked)
            else:
                self.checkBox_filter_ids_all_none.setCheckState(Qt.PartiallyChecked)

        #   append checkbox widgets
        for i in values['filter_ids']:
            self.checkbox_filter_ids.append([i, QCheckBox("%03d" % (i), self.widget_filter_ids)])
            w = self.checkbox_filter_ids[-1][1]
            self.layout_filtersNo.addWidget(w)
            set_widget_stylesheet(w)
            w.stateChanged['int'].connect(self.event_filter_id_changed)
        #   select/unselect checkbox and enable signals

        if 'reload' in values.keys() and values['reload']:
            for c_str, c in self.checkbox_filter_ids:
                c.blockSignals(True)
                if c_str in values['hide']['filter_ids']:
                    c.setChecked(False)
                else:
                    c.setChecked(True)
                c.blockSignals(False)
        else:
            for c_str, c in self.checkbox_filter_ids:
                c.blockSignals(True)
                # When changing directory, enable all filter ids
                c.setChecked(True)
                c.blockSignals(False)

        self.checkBox_filter_ids_all_none.blockSignals(False)

        self.widget_filter_ids.setContentsMargins(12, 0, -1, 0)
        self.widget_filter_ids.update()

        filters = self.filter_by()
        self.signal_filter_by_changed.emit(filters)



    def event_reload(self, index=-1):
        log.info("event_reload")
        self.refresh_combobox_part(index)

        # Generate a signal to inform that the following shall be updated:
        #   - editions
        #   - filter ids
        #   - list of frames
        k_ep = ''
        if (self.combobox_episode.currentText() != ' '
            and self.combobox_episode.currentText() != ''):
            k_ep = 'ep%02d' % (int(self.combobox_episode.currentText()))

        values = {
            'k_ep': k_ep,
            'k_part': self.combobox_part.currentText(),
            'hide': self.filter_by(),
            'reload': True
        }

        self.signal_directory_changed.emit(values)
        return True



    def event_episode_changed(self, index=-1):
        log.info("select ep: %s, part: %s" % (self.combobox_episode.currentText(), self.combobox_part.currentText()))
        self.refresh_combobox_part(index)

        # Generate a signal to inform that the following shall be updated:
        #   - editions
        #   - filter ids
        #   - list of frames
        k_ep = ''
        if (self.combobox_episode.currentText() != ' '
            and self.combobox_episode.currentText() != ''):
            k_ep = 'ep%02d' % (int(self.combobox_episode.currentText()))

        values = {
            'k_ep': k_ep,
            'k_part': self.combobox_part.currentText(),
        }

        self.signal_directory_changed.emit(values)
        return True




    def event_part_changed(self, index):
        log.info("select ep: %s, part: %s" % (self.combobox_episode.currentText(), self.combobox_part.currentText()))

        k_ep = ''
        current_episode = self.combobox_episode.currentText()
        if current_episode != ' ' and current_episode != '':
            k_ep = 'ep%02d' % (int(current_episode))

        values = {
            'k_ep': k_ep,
            'k_part': self.combobox_part.currentText(),
        }

        self.signal_directory_changed.emit(values)
        return True



    def event_edition_changed(self, state):
        log.info("changed filter_by, single edition")
        filters = self.filter_by()

        self.checkBox_editions_all_none.blockSignals(True)
        if len(filters['editions']) == 0:
            self.checkBox_editions_all_none.setCheckState(Qt.Checked)
        elif len(filters['editions']) == len(self.checkbox_editions):
            self.checkBox_editions_all_none.setCheckState(Qt.Unchecked)
        else:
            self.checkBox_editions_all_none.setCheckState(Qt.PartiallyChecked)
        self.checkBox_editions_all_none.blockSignals(False)

        self.signal_filter_by_changed.emit(filters)


    def event_edition_all_none_changed(self, state):
        self.checkBox_editions_all_none.blockSignals(True)
        new_state = self.checkBox_editions_all_none.checkState()

        if (new_state == Qt.PartiallyChecked
        or new_state == Qt.Checked):
            self.checkBox_editions_all_none.setCheckState(Qt.Checked)
            for c_str, c in self.checkbox_editions:
                c.blockSignals(True)
                c.setChecked(True)
                c.blockSignals(False)

        if new_state == Qt.Unchecked:
            for c_str, c in self.checkbox_editions:
                c.blockSignals(True)
                c.setChecked(False)
                c.blockSignals(False)

        self.checkBox_editions_all_none.blockSignals(False)

        filters = self.filter_by()
        self.signal_filter_by_changed.emit(filters)



    def event_step_changed(self, state):
        log.info("changed filter_by, single step")
        filters = self.filter_by()

        self.checkBox_steps_all_none.blockSignals(True)
        if len(filters['steps']) == 0:
            self.checkBox_steps_all_none.setCheckState(Qt.Checked)
        elif len(filters['steps']) == len(self.checkbox_steps):
            self.checkBox_steps_all_none.setCheckState(Qt.Unchecked)
        else:
            self.checkBox_steps_all_none.setCheckState(Qt.PartiallyChecked)
        self.checkBox_steps_all_none.blockSignals(False)

        self.signal_filter_by_changed.emit(filters)



    def event_step_all_none_changed(self, state):
        self.checkBox_steps_all_none.blockSignals(True)
        new_state = self.checkBox_steps_all_none.checkState()

        if (new_state == Qt.PartiallyChecked
        or new_state == Qt.Checked):
            self.checkBox_steps_all_none.setCheckState(Qt.Checked)
            for c_str, c in self.checkbox_steps:
                c.blockSignals(True)
                c.setChecked(True)
                c.blockSignals(False)

        if new_state == Qt.Unchecked:
            for c_str, c in self.checkbox_steps:
                c.blockSignals(True)
                c.setChecked(False)
                c.blockSignals(False)

        self.checkBox_steps_all_none.blockSignals(False)

        filters = self.filter_by()
        self.signal_filter_by_changed.emit(filters)



    def event_filter_id_changed(self, index):
        log.info("changed filter_by, single filter_id")
        filters = self.filter_by()

        self.checkBox_filter_ids_all_none.blockSignals(True)
        if len(filters['filter_ids']) == 0:
            self.checkBox_filter_ids_all_none.setCheckState(Qt.Checked)
        elif len(filters['filter_ids']) == len(self.checkbox_filter_ids):
            self.checkBox_filter_ids_all_none.setCheckState(Qt.Unchecked)
        else:
            self.checkBox_filter_ids_all_none.setCheckState(Qt.PartiallyChecked)
        self.checkBox_filter_ids_all_none.blockSignals(False)

        self.signal_filter_by_changed.emit(filters)



    def event_filter_id_all_none_changed(self, state):
        self.checkBox_filter_ids_all_none.blockSignals(True)
        new_state = self.checkBox_filter_ids_all_none.checkState()

        if (new_state == Qt.PartiallyChecked
        or new_state == Qt.Checked):
            self.checkBox_filter_ids_all_none.setCheckState(Qt.Checked)
            for w in self.widget_filter_ids.findChildren(QCheckBox):
                w.blockSignals(True)
                w.setChecked(True)
                w.blockSignals(False)

        if new_state == Qt.Unchecked:
            for w in self.widget_filter_ids.findChildren(QCheckBox):
                w.blockSignals(True)
                w.setChecked(False)
                w.blockSignals(False)

        self.checkBox_filter_ids_all_none.blockSignals(False)

        filters = self.filter_by()
        self.signal_filter_by_changed.emit(filters)



    def filter_by(self):
        filter_by_dict = {
            'editions': list(),
            'steps': list(),
            'filter_ids': list()
        }

        for c_str, c in self.checkbox_editions:
            if not c.isChecked():
                filter_by_dict['editions'].append(c_str)

        for c_str, c in self.checkbox_steps:
            if not c.isChecked():
                filter_by_dict['steps'].append(c_str)

        for c_str, c in self.checkbox_filter_ids:
            if not c.isChecked():
                filter_by_dict['filter_ids'].append(c_str)

        return filter_by_dict



    def refresh_image_list(self, imagelist):
        # Save current selected image
        if self.list_images.count() > 0 and len(imagelist) > 0:
            saved_image_name = self.list_images.currentItem().text()
            log.info("current frame: %s" % (saved_image_name))
        else:
            log.info("no frames")
            saved_image_name = ""

        self.list_images.blockSignals(True)

        # Remove all names
        self.list_images.clear()

        # Update list of images
        no = -1
        for name, i in zip(imagelist, range(len(imagelist))):
            self.list_images.addItem(QListWidgetItem(name))
            if name == saved_image_name:
                no = i

        # Select previous image
        image_name = ''
        if self.list_images.count() > 0:
            if no == -1:
                no = 0
            log.info("set current frame, no=%d, nb of frames=%d" % (no, self.list_images.count()))
            self.list_images.setCurrentRow(no)
            self.list_images.item(no).setSelected(True)
            image_name = self.list_images.currentItem().text()

        self.list_images.blockSignals(False)
        self.signal_select_image.emit(image_name)


    def display_frame_properties(self, frame):
        self.label_edition.setText('')
        self.label_frame_no.setText('')
        self.label_shot.setText('')
        self.label_step.setText('')
        self.label_dimension.setText('')
        if frame is not None:
            self.label_edition.setText("%s, %s, %s" % (
                frame['k_ed'],
                frame['k_ep'],
                frame['k_part']))
            self.label_frame_no.setText("\tframe no. %d" % (frame['no']))
            self.label_shot.setText("\tshot no. %d (start: %06d)" % (frame['shot_no'], frame['start']))
            self.label_step.setText("\t%s (%03d)" % (frame['step'], frame['filter_id']))
            self.label_dimension.setText("\t%dx%d" % (frame['dimensions']['w'], frame['dimensions']['h']))


    def is_fit_to_image_enabled(self):
        return self.checkBox_fit_image_to_window.isChecked()

    def switch_fit_image_state(self):
        log.info("click on fit image button")
        self.checkBox_fit_image_to_window.click()

    def event_fit_image_to_window_changed(self):
        log.info("fit image changed")
        self.signal_action.emit('repaint')


    def event_minimize(self):
        log.info("minimize button clicked")
        self.signal_action.emit('minimize')


    def event_exit(self):
        log.info("exit button clicked")
        self.signal_action.emit('exit')


    def closeEvent(self, event):
        self.signal_action.emit('exit')


    def event_select_image(self):
        image_name = self.list_images.currentItem().text()
        current_item = self.list_images.currentItem()
        # print("event_select_image: is selected?", current_item.isSelected())
        # log.info("select [%s]" % (image_name))
        self.signal_select_image.emit(image_name)
        return True



    def select_next_image(self):
        if self.list_images.count() == 0:
            return True
        self.list_images.item(self.list_images.currentRow()).setSelected(False)
        no = self.list_images.currentRow() + 1
        if no >= self.list_images.count():
            no = 0
        # log.info("select row no. %d" % (no))
        self.list_images.setCurrentRow(no)
        self.list_images.item(no).setSelected(True)


    def select_previous_image(self):
        if self.list_images.count() == 0:
            return True
        self.list_images.item(self.list_images.currentRow()).setSelected(False)
        no = self.list_images.currentRow()
        if no == 0:
            no = self.list_images.count() - 1
        else:
            no = no - 1
        # log.info("select row no. %d" % (no))
        self.list_images.setCurrentRow(no)
        self.list_images.item(no).setSelected(True)



    def select_first_image(self):
        if self.list_images.count() > 0:
            self.list_images.setCurrentRow(0)
            self.list_images.item(0).setSelected(True)
        return True


    def select_last_image(self):
        if self.list_images.count() > 0:
            row_no = self.list_images.count() - 1
            self.list_images.setCurrentRow(row_no)
            self.list_images.item(row_no).setSelected(True)
        return True

    def event_page_up(self, event):
        return self.list_images.keyPressEvent(event)

    def event_page_down(self, event):
        return self.list_images.keyPressEvent(event)

    def mousePressEvent(self, event):
        self.previous_position = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.previous_position is not None:
            delta = QPoint(event.globalPos() - self.previous_position)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.previous_position = event.globalPos()



    def keyPressEvent(self, event):
        if self.event_key_pressed(event):
            event.accept()
            return True
        return self.ui.keyPressEvent(event)


    def event_key_pressed(self, event):
        key = event.key()
        if key == Qt.Key_F:
            self.switch_fit_image_state()
            return True

        # elif key == Qt.Key_F5:
        #     log.info("reload")
        #     self.event_episode_changed()
        #     return True
        return False

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        # Filter press/release events
        if QApplication.focusObject() is self.list_images:
            if event.type() == QEvent.KeyPress:
                if event.key() == Qt.Key_F:
                    self.ui.setFocus()
                    self.ui.keyPressEvent(event)
                    return True

                self.list_images.keyPressEvent(event)

        if event.type() == QEvent.Wheel:
            # log.info("%s:eventFilter: wheel event" % (__name__))
            if event.angleDelta().y() > 0:
                # log.info("wheelEvent:Previous")
                self.select_previous_image()
            else:
                # log.info("wheelEvent:Next")
                self.select_next_image()
            event.accept()
            return True

        return self.ui.eventFilter(watched, event)
