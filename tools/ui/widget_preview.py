from pprint import pprint
from PySide6.QtCore import (
    Qt,
    Signal,
    Slot,
    QPoint,
    QSize,
    QRect,
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

import cv2
import numpy as np
from backend.frame_cache import Frame
from backend._types import (
    GeometryPreviewOptions,
    TargetSceneGeometry,
    AppType,
)
from utils.mco_types import SceneGeometry
from utils.p_print import lightcyan, lightgreen, red, yellow


COLOR_PART_CROP_RECT = QColor(30, 230, 30)
COLOR_CROP_RECT = QColor(230, 30, 30)
COLOR_FINAL_RECT = QColor(0, 255, 0)
COLOR_DISPLAY_RECT = QColor(255, 255, 255)
PAD = 24
PEN_WIDTH: int = 1
FINAL_HEIGHT: int = 1080

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
        print(lightcyan("set_geometry"))
        self.scene_geometry = scene_geometry


    def set_preview_options(self, options: GeometryPreviewOptions) -> None:
        self.preview_options: GeometryPreviewOptions = options
        self.repaint()


    def display_frame(self, frame: Frame) -> None:
        # if frame.qimage is None:
            # h, w, c = frame.img.shape
            # frame.qimage = QImage(
            #     frame.img, w, h, w * c, QImage.Format.Format_BGR888
            # )
            # frame.img = None
        self.frame = frame
        self.repaint()


    def draw_widget_guides(self, painter: QPainter) -> None:
        cx1, cy1 = self.geometry().size().toTuple()
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

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        pen = QPen(QColor(255,255,250))
        pen.setWidth(1)
        pen.setStyle(Qt.PenStyle.SolidLine)
        painter.setPen(pen)

        width = 1440
        x0 = (cx1 - width) // 2
        x1 = x0 + width
        y = cy1 // 2
        painter.drawLine(x0, y, x1, y)



    def get_crop_values(self, scene_geometry: SceneGeometry) -> tuple[int, int, int, int]:
        # Select crop values
        if (
            all(v != 0 for v in scene_geometry.autocrop)
            and scene_geometry.use_autocrop
        ):
            print(lightcyan("use autocrop"))
            return scene_geometry.autocrop
        else:
            return scene_geometry.crop


    def crop_and_resize(
        self,
        img: np.ndarray,
        crop_values: tuple[int, int, int, int],
        scene_geometry: TargetSceneGeometry,
    ) -> np.ndarray:
        ih, iw = img.shape[:2]
        t, b, l, r = crop_values
        cw, ch = iw - (l + r), ih - (t + b)
        cropped_img: np.ndarray = np.ascontiguousarray(
            self.frame.img[t : ih-b, l : iw-r, :]
        )
        r_h: int = FINAL_HEIGHT
        # change this if not ratio or keep_width
        if scene_geometry.scene.keep_ratio and scene_geometry.scene.fit_to_width:
            print(yellow("keep_ratio and fit to width"))
            r_w = scene_geometry.chapter.width
            r_h = int(ch * r_w / cw)
        elif scene_geometry.scene.keep_ratio:
            print(yellow("keep_ratio"))
            r_w = int(cw * r_h / ch)
        elif scene_geometry.scene.fit_to_width:
            print(yellow("fit to width"))
            r_w = scene_geometry.chapter.width
        else:
            print(red("WHAT?"))
        resized_img: np.ndarray = cv2.resize(
            cropped_img,
            (r_w, r_h),
            interpolation=cv2.INTER_AREA
        )
        _r_h, _r_w = resized_img.shape[:2]
        if _r_h > FINAL_HEIGHT:
            y0: int = (_r_h - FINAL_HEIGHT) // 2
            print(red(f"higher, from {y0} to {y0 + FINAL_HEIGHT}"))
            resized_img = np.ascontiguousarray(
                resized_img[y0 : y0 + FINAL_HEIGHT, :, : ]
            )
        elif _r_h < FINAL_HEIGHT:
            print(red("too small"))
            y0: int = (FINAL_HEIGHT - _r_h) // 2
            resized_img = cv2.copyMakeBorder(
                resized_img,
                y0, FINAL_HEIGHT - _r_h - y0,
                0, 0,
                borderType=cv2.BORDER_CONSTANT,
                value=[255, 0, 0]
            )

        if  _r_w != r_w or _r_h != r_h:
            print(red(f"Error: resized {_r_w}x{_r_h} != {r_w}x{r_h}"))
        return resized_img


    def paintEvent(self, event: QPaintEvent):
        if self.frame is None:
            return

        pen_width = PEN_WIDTH

        painter = QPainter()
        if not painter.begin(self):
            return

        # qimage: QPixmap = self.frame.qimage
        ih, iw, c = self.frame.img.shape
        container_w, container_h = self.size().toTuple()
        ix0: int = (container_w - iw) // 2
        iy0: int = (container_h - ih) // 2

        if self.app_type == 'replace':
            qimage = QImage(self.frame.img, iw, ih, iw * c, QImage.Format.Format_BGR888)
            scaled: QPixmap = QPixmap().fromImage(qimage).scaled(
                int(container_w),
                int(container_h),
                aspectMode=Qt.AspectRatioMode.KeepAspectRatio,
                mode=Qt.TransformationMode.FastTransformation
            )
            iw, ih = scaled.size().toTuple()
            ix0: int = (container_w - iw) // 2
            iy0: int = (container_h - ih) // 2
            painter.drawPixmap(QPoint(ix0, iy0), scaled)
            self.draw_widget_guides(painter)
            painter.end()
            return


        preview: GeometryPreviewOptions = self.preview_options
        if preview is None:
            self.draw_widget_guides(painter)
            painter.end()
            return

        # Select crop values
        crop_values = self.get_crop_values(self.scene_geometry.scene)
        t, b, l, r = crop_values
        cw, ch = iw - (l + r), ih - (t + b)
        if (
            (preview.crop_edition or preview.crop_preview)
            and not preview.resize_preview
            and not preview.width_edition
            and not preview.final_preview
        ):

            # Crop rect
            if preview.crop_preview:
                cropped_img: np.ndarray = np.ascontiguousarray(self.frame.img[t:ih-b,l:iw-r,:])
                pixmap: QPixmap = QPixmap().fromImage(
                    QImage(cropped_img, cw, ch, cw * c, QImage.Format.Format_BGR888)
                )
                _cw, _ch = pixmap.size().toTuple()
                if  _cw != cw or _ch != ch:
                    print(red(f"Error: cropped {_cw}x{_ch} != {cw}x{ch}"))
                painter.drawPixmap(
                    QPoint(ix0 + l, iy0 + t),
                    pixmap
                )

            elif preview.crop_edition:
                qimage = QImage(self.frame.img, iw, ih, iw * c, QImage.Format.Format_BGR888)
                pixmap: QPixmap = QPixmap().fromImage(qimage)
                painter.drawPixmap(QPoint(ix0, iy0), pixmap)

                painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
                pen = QPen(COLOR_CROP_RECT)
                pen.setWidth(pen_width)
                pen.setStyle(Qt.PenStyle.SolidLine)
                painter.setPen(pen)
                painter.drawRect(
                    ix0 + l - PEN_WIDTH, iy0 + t - PEN_WIDTH,
                    cw + 2*PEN_WIDTH, ch + 2*PEN_WIDTH
                )
            self.draw_widget_guides(painter)
            painter.end()
            return


        if (
            not preview.crop_edition
            and preview.resize_preview
            and not preview.width_edition
            and not preview.final_preview
        ):
            resize_img = self.crop_and_resize(self.frame.img, crop_values, self.scene_geometry)
            r_h, r_w = resize_img.shape[:2]
            pixmap: QPixmap = QPixmap().fromImage(
                QImage(resize_img, r_w, r_h, r_w * c, QImage.Format.Format_BGR888)
            )
            painter.drawPixmap(
                QPoint(
                    (container_w - r_w) // 2,
                    (container_h - r_h) // 2
                ),
                pixmap
            )
            self.draw_widget_guides(painter)
            painter.end()
            return


        if (
            preview.width_edition
            and not preview.final_preview
        ):
            # Chapter width
            resize_img = self.crop_and_resize(self.frame.img, crop_values, self.scene_geometry)
            r_h, r_w = resize_img.shape[:2]
            pixmap: QPixmap = QPixmap().fromImage(
                QImage(resize_img, r_w, r_h, r_w * c, QImage.Format.Format_BGR888)
            )
            print(lightcyan(f"resized: {r_w}x{r_h}"))
            painter.drawPixmap(
                QPoint(
                    (container_w - r_w) // 2,
                    (container_h - r_h) // 2
                ),
                pixmap
            )

            ch_w, ch_h = self.scene_geometry.chapter.width, 1080
            ch_x0 = (container_w - ch_w) // 2
            ch_x1 = (container_w - ch_w) // 2 + ch_w

            painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
            pen = QPen(COLOR_PART_CROP_RECT)
            pen.setWidth(PEN_WIDTH)
            pen.setStyle(Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawLine(
                QPoint(ch_x0 - PEN_WIDTH, iy0), QPoint(ch_x0 - PEN_WIDTH, iy0 + ch_h - 1 + 2*PAD)
            )
            painter.drawLine(
                QPoint(ch_x1 - PEN_WIDTH, iy0), QPoint(ch_x1 - PEN_WIDTH, iy0 + ch_h - 1 + 2*PAD)
            )

            self.draw_widget_guides(painter)
            painter.end()
            return


        if preview.final_preview:
            ch_w: int = self.scene_geometry.chapter.width

            painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
            cx1, cy1 = self.geometry().size().toTuple()
            x0 = (cx1 - ch_w) // 2
            y0 = (cy1 - FINAL_HEIGHT) // 2
            x1 = x0 + ch_w - PEN_WIDTH
            y1 = y0 + FINAL_HEIGHT - PEN_WIDTH
            painter.fillRect(QRect(QPoint(x0, y0), QPoint(x1, y1)), QColor(0,255,0))
            print(f"({x0}, {y0}) -> ({x1}, {y1})")

            resize_img = self.crop_and_resize(self.frame.img, crop_values, self.scene_geometry)
            r_h, r_w = resize_img.shape[:2]
            print(lightgreen(f"resized to: {resize_img.shape}"))
            l: int = (r_w - ch_w) // 2
            if l < 0:
                print(red(f"Error: {r_w} < {ch_w}"))
                f_w, f_h = r_w, r_h
                pixmap: QPixmap = QPixmap().fromImage(
                    QImage(resize_img, r_w, r_h, r_w * c, QImage.Format.Format_BGR888)
                )
                painter.drawPixmap(
                    QPoint(
                        (container_w - f_w) // 2,
                        (container_h - f_h) // 2
                    ),
                    pixmap
                )

            else:
                final_img: np.ndarray = np.ascontiguousarray(
                    resize_img[:, l : l + ch_w, :]
                )
                f_h, f_w = final_img.shape[:2]
                print(lightgreen(f"final: {final_img.shape} w={ch_w}, l={l}"))
                pixmap: QPixmap = QPixmap().fromImage(
                    QImage(final_img, ch_w, r_h, ch_w * c, QImage.Format.Format_BGR888)
                )
                painter.drawPixmap(
                    QPoint(
                        (container_w - f_w) // 2,
                        (container_h - f_h) // 2
                    ),
                    pixmap
                )
            self.draw_widget_guides(painter)
            painter.end()
            return


        # else...
        pixmap: QPixmap = QPixmap().fromImage(
            QImage(self.frame.img, iw, ih, iw * c, QImage.Format.Format_BGR888)
        )
        ix0: int = (container_w - iw) // 2
        iy0: int = (container_h - ih) // 2
        painter.drawPixmap(QPoint(ix0, iy0), pixmap)

        self.draw_widget_guides(painter)
        painter.end()
