from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QTableWidgetItem,
    QWidget,
    QCheckBox,
    QHBoxLayout,
)
from .ui.ui_widget_player_ctrl import Ui_PlayerControlWidget

class PlayerCtrlWidget(QWidget, Ui_PlayerControlWidget):

    def __init__(self, parent: QWidget | None) -> None:
        super().__init__(parent)
        self.setupUi(self)
