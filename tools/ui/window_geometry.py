from __future__ import annotations
from pprint import pprint
from typing import TYPE_CHECKING

from PySide6.QtCore import (
    Signal,
    Slot,
    QEvent,
    QObject,
    Slot,
)
from PySide6.QtGui import (
    QKeyEvent,
)
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QSpacerItem,
    QSizePolicy,
)

from backend._types import GeometryPreviewOptions
from utils.p_print import red
from logger import log
from .stylesheet import set_stylesheet
from .widget_geometry import GeometryWidget
from .window_common import CommonWindow

if TYPE_CHECKING:
    from backend.geometry_controller import GeometryController


class GeometryWindow(CommonWindow):
    signal_k_ep_p_refreshed = Signal(dict)
    signal_preview_modified = Signal(dict)

    def __init__(
        self,
        controller: GeometryController = None
    ):
        super().__init__(controller, 'geometry')
        self.controller: GeometryController = controller

        self.main_widget = QWidget(self)
        self.main_layout = QVBoxLayout(self.main_widget)
        self.horizontalLayout = QHBoxLayout()
        self.verticalLayout = QVBoxLayout()
        self.horizontalLayout.setSpacing(6)

        set_stylesheet(self)

        # Preview
        self.verticalLayout.addWidget(self.widget_preview)

        # Player control
        self.verticalLayout.addWidget(self.widget_player_ctrl)
        self.horizontalLayout.addLayout(self.verticalLayout)

        # Geometry
        self.widget_geometry: GeometryWidget = GeometryWidget(self, controller)
        self.widgets['geometry'] = self.widget_geometry

        self.verticalLayout_tool = QVBoxLayout()
        self.verticalLayout_tool.addItem(
            QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )
        self.verticalLayout_tool.addWidget(self.widget_geometry)
        self.horizontalLayout.addLayout(self.verticalLayout_tool)

        # Selection
        self.horizontalLayout.addWidget(self.widget_selection)

        self.main_layout.addLayout(self.horizontalLayout)
        self.setCentralWidget(self.main_widget)

        self.widget_geometry.signal_preview_toggled[bool].connect(
            self.preview_modified
        )
        self.widget_geometry.signal_preview_options_changed.connect(
            self.preview_options_changed
        )

        self.show()
        self.installEventFilter(self)


    def apply_user_preferences(self, user_preferences: dict):
        try:
            w: list[int] = user_preferences['window']
            self.setGeometry(*w['geometry'])
        except:
            self.setGeometry(50, 50 , 1920, 1080)
        # self.setGeometry(0, 0 , 1920, 1080)
        # self.move(QPoint(100,100))
        self.widget_selection.apply_user_preferences(user_preferences)
        self.widget_geometry.apply_user_preferences(user_preferences)
        self.preview_options_changed()


    def event_edition_started(self):
        log.info(f"Edition started")
        self.widget_selection.edition_started(True)


    @Slot(bool)
    def preview_modified(self, enabled: bool) -> None:
        log.info(f"widget preview changed to {enabled}")
        self.signal_preview_modified.emit({'enabled': enabled})
        self.preview_enabled = enabled
        self.widget_player_ctrl.set_preview_enabled(enabled)
        self.display_frame()


    @Slot(GeometryPreviewOptions)
    def preview_options_changed(self) -> None:
        self.widget_preview.set_preview_options(
            self.widget_geometry.get_preview_options()
        )

    # def get_preview_options(self):
    #     log.info("get preview options")
    #     preview_options = dict()
    #     for e, w in self.widgets.items():
    #         preview_options.update({e: w.get_preview_options()})
    #     return preview_options


    # def event_preview_options_consolidated(self, new_preview_settings):
    #     # log.info("preview options have been consolidated, refresh widgets")
    #     self.widget_geometry.refresh_preview_options(new_preview_settings)
    #     # self.widget_painter.refresh_preview_options(new_preview_settings)

    def display_frame(self):
        frame, original_frame = self.controller.get_frame_at_index(self.current_frame_index)
        self.widget_player_ctrl.refresh_values(frame, original_frame)

        self.widget_preview.update_geometry(self.controller.get_scene_geometry(frame))
        self.widget_preview.display_frame(frame)
        self.widget_geometry.refresh_values(frame)



    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        modifiers = event.modifiers()
        self.current_key_pressed = None
        # print(f"{__name__} received: {key}")

        for w in (
            self.widget_geometry,
            self.widget_player_ctrl,
            # self.widget_preview,
            self.widget_selection
        ):
            if w.event_key_pressed(event):
                # print(f"{__name__} {key} forwarded to {w.objectName()}")
                event.accept()
                return True
        return super().keyPressEvent(event)


    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        for w in (
            self.widget_player_ctrl,
            self.widget_geometry,
            # self.widget_preview,
            self.widget_selection
        ):
            try:
                # print(f"{__name__} forwarded to {w.objectName()}")
                w.event_key_released(event)
            except:
                pass
        event.accept()
        return super().keyReleaseEvent(event)



    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Wheel:
            for w in (
                self.widget_geometry,
                self.widget_player_ctrl,
                # self.widget_preview,
                # self.widget_selection
            ):
                if w.event_wheel(event):
                    return True

        return super().eventFilter(watched, event)
