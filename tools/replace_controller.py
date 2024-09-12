from __future__ import annotations
from PySide6.QtCore import (
    QObject,
    Signal,
    Qt,
    QPoint,
    QSize,
)

from .replace_window import ReplaceWindow


class ReplaceController(QObject):
    def __init__(self) -> None:
        super().__init__()
        self.view: ReplaceWindow = None

    def set_view(self, window: ReplaceWindow) -> None:
        self.view: ReplaceWindow = window
