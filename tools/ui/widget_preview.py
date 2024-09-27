from PySide6.QtCore import (
    Qt,
    Signal,
    Slot,
    QPoint,
    QSize,
)
from PySide6.QtGui import (
    QWheelEvent,
    QPixmap,
    QImage,
    QPaintEvent,
    QPainter,
    QPen,
    QColor,
    QKeyEvent,
)
from PySide6.QtWidgets import (
    QTableWidgetItem,
    QWidget,
    QCheckBox,
    QHBoxLayout,
    QVBoxLayout,
    QSpacerItem,
    QSizePolicy,
)

import numpy as np
from backend.frame_cache import Frame


class PreviewWidget(QWidget):
    signal_wheel_event = Signal(QWheelEvent)

    def __init__(
        self,
        parent: QWidget | None
    ) -> None:
        super().__init__(parent)

        self.frame: Frame = None

        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())

        self.setSizePolicy(sizePolicy)
        self.setMinimumSize(QSize(300, 300))
        self.setStyleSheet(u"background-color: rgb(0, 0, 0);")


    @staticmethod
    def _scale(pixmap: QPixmap, factor):
        return pixmap.scaled(factor * pixmap.width(), factor * pixmap.height())


    def display_frame(self, frame: Frame) -> None:
        if frame.pixmap is None:
            h, w, c = frame.img.shape
            frame.pixmap = QPixmap().fromImage(
                QImage(frame.img, w, h, w * c, QImage.Format.Format_BGR888)
            )
            frame.img = None
        self.frame = frame
        self.repaint()


    def paintEvent(self, event: QPaintEvent):
        if self.frame is None:
            return

        painter = QPainter()
        if not painter.begin(self):
            return

        cx1, cy1 = self.geometry().size().toTuple()

        pixmap: QPixmap = self.frame.pixmap

        container_w, container_h = self.size().toTuple()
        scaled: QPixmap = pixmap.scaled(
            int(container_w),
            int(container_h),
            aspectMode=Qt.AspectRatioMode.KeepAspectRatio,
            mode=Qt.TransformationMode.FastTransformation
        )
        w, h = scaled.size().toTuple()
        x0: int = (container_w - w) // 2
        y0: int = (container_h - h) // 2

        painter.drawPixmap(QPoint(x0, y0), scaled)

        if False:
            # For debug
            pen_width = 1
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
            pen = QPen(QColor(255,255,255))
            pen.setWidth(pen_width)
            pen.setStyle(Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawRect(0, 0, cx1 - pen_width, cy1 - pen_width)


            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            pen = QPen(QColor(0,255,0))
            pen.setWidth(pen_width)
            pen.setStyle(Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawLine(0, 0, cx1 - pen_width, cy1 - pen_width)
            painter.drawLine(0, cy1 - pen_width, cx1 - pen_width, 0)


            painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
            pen = QPen(QColor(255,255,250))
            pen.setWidth(1)
            pen.setStyle(Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawRect(self.rect().adjusted(0,0,-1,-1))

        painter.end()
