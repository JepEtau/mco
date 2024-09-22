from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QTableWidgetItem,
    QWidget,
    QCheckBox,
    QHBoxLayout,
)


class PreviewWidget(QWidget):

    def __init__(self, parent: QWidget | None) -> None:
        super().__init__(parent)
