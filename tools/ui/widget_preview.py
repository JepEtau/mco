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
from backend._types import (
    GeometryPreviewOptions,
    TargetSceneGeometry,
    AppType,
)


COLOR_PART_CROP_RECT = QColor(30, 230, 30)
COLOR_CROP_RECT = QColor(230, 30, 30)
COLOR_FINAL_RECT = QColor(0, 255, 0)
COLOR_DISPLAY_RECT = QColor(255, 255, 255)
PAD = 24

class PreviewWidget(QWidget):
    signal_wheel_event = Signal(QWheelEvent)

    def __init__(
        self,
        parent: QWidget | None,
        app_type: AppType,
    ) -> None:
        super().__init__(parent)

        self.frame: Frame = None
        self.app_type: AppType = app_type

        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())

        self.setSizePolicy(sizePolicy)
        self.setMinimumSize(QSize(300, 300))
        self.setStyleSheet(u"background-color: rgb(0, 0, 0);")
        self.scene_geometry: TargetSceneGeometry | None = None
        self.preview_options: GeometryPreviewOptions | None = None


    @staticmethod
    def _scale(pixmap: QPixmap, factor):
        return pixmap.scaled(factor * pixmap.width(), factor * pixmap.height())


    def set_geometry(self, scene_geometry: TargetSceneGeometry):
        self.scene_geometry = scene_geometry


    def set_preview_options(self, options: GeometryPreviewOptions) -> None:
        self.preview_options: GeometryPreviewOptions = options
        # Use the same geometry/frame
        self.repaint()


    def display_frame(self, frame: Frame) -> None:
        if frame.pixmap is None:
            h, w, c = frame.img.shape
            frame.pixmap = QPixmap().fromImage(
                QImage(frame.img, w, h, w * c, QImage.Format.Format_BGR888)
            )
            # frame.img = None
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
        iw, ih = pixmap.size().toTuple()

        container_w, container_h = self.size().toTuple()
        scaled: QPixmap
        if self.app_type == 'replace':
            scaled = pixmap.scaled(
                int(container_w),
                int(container_h),
                aspectMode=Qt.AspectRatioMode.KeepAspectRatio,
                mode=Qt.TransformationMode.FastTransformation
            )
        else:
            scaled = pixmap

        w, h = scaled.size().toTuple()
        ix0: int = (container_w - w) // 2
        iy0: int = (container_h - h) // 2
        painter.drawPixmap(QPoint(ix0, iy0), scaled)

        if True:
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

        # Coordinates of center
        xc0 = cx1 // 2
        yc0 = cy1 // 2

        if self.scene_geometry is not None:
            factor: float = h / ih


            # final 4:3 screen
            screen_w, screen_h = 1440, 1080
            x0: int = (container_w - screen_w) // 2
            y0: int = (container_h - screen_h) // 2
            pen_width = 1
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
            pen = QPen(COLOR_FINAL_RECT)
            pen.setWidth(pen_width)
            pen.setStyle(Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawRect(x0, y0, screen_w - 1, screen_h - 1)


            # Chapter width
            ch_w, ch_h = self.scene_geometry.chapter.width, 1080

            ch_x0: int = xc0 - ch_w // 2
            ch_x1: int = ch_x0 + ch_w

            # x0: int = (container_w - ch_w) // 2
            # y0: int = (container_h - screen_h) // 2
            ch_y0 = iy0 + PAD
            pen_width = 1
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
            pen = QPen(COLOR_PART_CROP_RECT)
            pen.setWidth(pen_width)
            pen.setStyle(Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawLine(
                QPoint(ch_x0, iy0), QPoint(ch_x0, iy0 + ch_h - 1 + 2*PAD)
            )
            painter.drawLine(
                QPoint(ch_x1, iy0), QPoint(ch_x1, iy0 + ch_h - 1 + 2*PAD)
            )
            # painter.drawRect(x0, y0, ch_w - 1, screen_h - 1)


            # Crop
            has_autocrop: bool = (
                len(self.scene_geometry.scene.autocrop) == 4
                and all(v != 0 for v in self.scene_geometry.scene.autocrop)
            )
            if has_autocrop:
                t, b, l, r = np.array(self.scene_geometry.scene.autocrop) * factor
            else:
                t, b, l, r = np.array(self.scene_geometry.scene.crop) * factor

            pen_width = 1
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
            pen = QPen(COLOR_CROP_RECT)
            pen.setWidth(pen_width)
            pen.setStyle(Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawRect(
                l + ix0, t + iy0,
                w - (l + r) - 1, h - (t + b) - 1
            )


        painter.end()
