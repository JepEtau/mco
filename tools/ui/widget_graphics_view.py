from __future__ import annotations
from copy import copy
from dataclasses import dataclass
from pprint import pprint
import time
from typing import TYPE_CHECKING
from PySide6.QtCore import (
    Qt,
    Signal,
    Slot,
    QPoint,
    QPointF,
    QSize,
    QRect,
    QRectF,
    QEvent,
    QObject,
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
    QBrush,
    QCursor,
    QTransform,
)
from PySide6.QtWidgets import (
    QTableWidgetItem,
    QWidget,
    QCheckBox,
    QHBoxLayout,
    QVBoxLayout,
    QSpacerItem,
    QSizePolicy,
    QGraphicsView,
    QFrame,
    QGraphicsScene,
    QGraphicsPixmapItem,
    QGraphicsItem,
    QApplication,
    QGraphicsEllipseItem,
    QGraphicsPathItem,
)

import cv2
import numpy as np
from backend.frame_cache import Frame
from backend._types import (
    GeometryPreviewOptions,
    TargetSceneGeometry,
    AppType,
)
from parsers import (
    SceneGeometry,
    MaskShape,
)
from utils.p_print import lightcyan, lightgreen, red, yellow
if TYPE_CHECKING:
    from backend.replace_controller import ReplaceController
    from .window_replace import ReplaceWindow

COLOR_PART_CROP_RECT = QColor(30, 230, 30)
COLOR_CROP_RECT = QColor(230, 30, 30)
COLOR_FINAL_RECT = QColor(0, 255, 0)
COLOR_DISPLAY_RECT = QColor(255, 255, 255)
PAD = 24
PEN_WIDTH: int = 1
FINAL_HEIGHT: int = 1080




# class GraphicsScene(QGraphicsScene):
#     def __init__(self, parent=None):
#         super().__init__(parent)

#     def mouseMoveEvent(self, event):
#         self.posX = event.scenePos().x()
#         self.parent().parent().setPosition(event.scenePos().x())


@dataclass(slots=True)
class DsrShape:
    shape: MaskShape
    center: list[float | int, float | int]
    axes: list[float | int, float | int]
    angle: float
    item: QGraphicsEllipseItem


class GraphicsViewWidget(QGraphicsView):
    signal_wheel_event = Signal(QWheelEvent)

    def __init__(
        self,
        parent: QWidget | None,
        main_window: ReplaceWindow,
        controller,
        app_type: AppType,
    ) -> None:
        super().__init__(parent)

        self.app_type: AppType = app_type
        self._parent = parent
        self.main_window = main_window

        # self.controller: ReplaceController = controller
        # self.ui = ui
        self.setObjectName('preview')


        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.Shape.Panel)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self.setFrameStyle(0)

        self.setMouseTracking(True)

        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)


        self.control_key_pressed = False
        self.image = None
        self.is_repainting = False


        self._pixmap_item = QGraphicsPixmapItem()
        self._scene.addItem(self._pixmap_item)
        self.current_position: QPointF = None
        self.is_alt_key_pressed: bool = False


        self.modif_keys: dict[str, bool] = {
            'radius': False,
            'width': False,
            'height': False,
            'angle': False,
        }
        self.radius: int = 10
        self.width: int = 30
        self.height: int = 10
        self.angle: float = 45
        # sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # sizePolicy.setHorizontalStretch(0)
        # sizePolicy.setVerticalStretch(0)
        # sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())

        # self.setSizePolicy(sizePolicy)
        # self.setMinimumSize(QSize(300, 300))
        # self.setStyleSheet(u"background-color: rgb(0, 0, 0);")
        # self.scene_geometry: TargetSceneGeometry | None = None
        # self.preview_options: GeometryPreviewOptions | None = None

        self.shapes: list[DsrShape] = []
        self.shape: DsrShape | None = None
        self.modifying_index: int = -1

        self.modified: bool = False

        self.installEventFilter(self)


    @staticmethod
    def _scale(pixmap: QPixmap, factor):
        return pixmap.scaled(factor * pixmap.width(), factor * pixmap.height())


    def update_geometry(self, scene_geometry: TargetSceneGeometry):
        # print(lightcyan("update preview geometry"))
        self.scene_geometry = scene_geometry


    def set_preview_options(self, options: GeometryPreviewOptions) -> None:
        self.preview_options: GeometryPreviewOptions = options
        # self.repaint()


    def display_frame(self, frame: Frame) -> None:
        # if frame.qimage is None:
            # h, w, c = frame.img.shape
            # frame.qimage = QImage(
            #     frame.img, w, h, w * c, QImage.Format.Format_BGR888
            # )
            # frame.img = None
        self.frame = frame
        self.draw_image()


    def repaint_frame(self):
        self.draw_image()


    def draw_widget_guides(self, painter: QPainter) -> None:
        return
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
            # print(lightcyan("use autocrop"))
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


    def draw_shape(self):
        if self.current_position is None:
            return

        if self.shape is None:
            cursor_position = self.mapToScene(self.current_position.toPoint())
            x, y = cursor_position.x(), cursor_position.y()
            # print(f"(x, y): ({x}, {y})")

            shape_name: MaskShape = self.main_window.get_current_shape()
            axes: tuple[float, float] = (
                (self.radius, self.radius)
                if shape_name == 'circle'
                else (self.width, self.height)
            )
            center = [x + axes[0], y + axes[1]]

            item: QGraphicsEllipseItem = QGraphicsEllipseItem(
                QRectF(x - axes[0], y - axes[1], 2*axes[0]+1, 2*axes[1]+1)
            )
            # item.setRotation(self.angle)
            item.setOpacity(0.5)
            item.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
            item.setBrush(QBrush(QColor("red")))
            item.setPen(QPen(QColor("red")))
            item.setTransformOriginPoint(x, y)
            item.setRotation(self.angle)

            self.shape = DsrShape(
                shape=shape_name,
                center=center,
                axes=axes,
                item=item,
                angle=self.angle,
            )
            self._scene.addItem(self.shape.item)

            self.modified = True

    def mouseMoveEvent(self, event):
        # print(event.position())
        self.current_position = event.position()

        # TODO: limit to image size
        cursor_position = self.mapToScene(event.position().toPoint())
        h, w = self.frame.img.shape[:2]
        outside: bool = False
        if cursor_position.x() > min(self.size().width(), w):
            cursor_position.setX(min(self.size().width(), w))
            outside = True
        if cursor_position.y() > min(self.size().height(), h):
            cursor_position.setY(min(self.size().height(), h))
            outside = True

        if self.shape is not None:
            self._scene.removeItem(self.shape.item)
            self.shape = None

        if not outside:
            self.draw_shape()

        super().mouseMoveEvent(event)


    def mousePressEvent(self, event):
        # Append the shape to the list of patches
        # if self.control_key_pressed:
        if self.shape is not None:
            if self.modifying_index != -1:
                del self.shapes[self.modifying_index]
            self.shapes.append(self.shape)
            self.shape = None
            self.modifying_index = -1
            self.setCursor(Qt.CursorShape.ArrowCursor)
        return super().mousePressEvent(event)


    def draw_image(self):
        print("viewport geometry:", self.viewport().geometry())
        print("sceneRect geometry:", self.sceneRect())
        self.setSceneRect(0, 0, self.viewport().geometry().width(), self.viewport().geometry().height())

        verbose = True
        # pprint(self.__scene.items())
        # print(self.__scene.sceneRect())

        # if self.image is None:
        #     print("no image loaded")
        #     return

        # img = self.image['cache']
        # if img is None:
        #     return
        # if self.image['cache_initial'] is None:
        #     return

        if self.is_repainting:
            print(red("error: self.is_repainting is True!!"))
            return
        self.is_repainting = True


        # Use
        # if self.app_type == 'replace':
        #     qimage = QImage(self.frame.img, iw, ih, iw * c, QImage.Format.Format_BGR888)
        #     scaled: QPixmap = QPixmap().fromImage(qimage).scaled(
        #         int(container_w),
        #         int(container_h),
        #         aspectMode=Qt.AspectRatioMode.KeepAspectRatio,
        #         mode=Qt.TransformationMode.FastTransformation
        #     )
        #     iw, ih = scaled.size().toTuple()
        #     ix0: int = (container_w - iw) // 2
        #     iy0: int = (container_h - ih) // 2
        #     painter.drawPixmap(QPoint(ix0, iy0), scaled)
        #     self.draw_widget_guides(painter)
        #     painter.end()
        #     return
        img = self.frame.img


        initial_img_height, initial_img_width, c = img.shape
        img_height, img_width, c = img.shape
        try:
            q_image = QImage(img.data, img_width, img_height, img_width * 3, QImage.Format_BGR888)
        except:
            print(red("paintEvent: cannot convert img to qImage"))
            return

        # preview = self.image['preview_options']

        # # delta_y = self.__parent.display_position_y
        # delta_y = 0

        # preview = self.image['preview_options']
        # # print_lightgreen("paintEvent: preview")
        # # pprint(preview)
        # initial_img_height, initial_img_width, c = img.shape
        # # print("paintEvent: initial image = %dx%d" % (initial_img_height, initial_img_width))
        # img_height, img_width, c = img.shape
        # try:
        #     q_image = QImage(img.data, img_width, img_height, img_width * 3, QImage.Format_BGR888)
        # except:
        #     print(red("paintEvent: cannot convert img to qImage"))
        #     return


        self._pixmap_item.setPixmap(QPixmap.fromImage(q_image))
        self._pixmap_item.setPos(0, 0)


        # if preview['curves']['split']:
        #     try: crop_top = 0 if preview_shot_geometry['resize_preview'] else (-1*crop_top)
        #     except:  crop_top = 0
        #     pen = QPen(QColor(255,255,255))
        #     pen.setStyle(Qt.DashLine)
        #     self.__lines['split'] = self.__scene.addLine(QLine(
        #         preview['curves']['split_x'], - crop_top,
        #         preview['curves']['split_x'], - crop_top + max(img_height, FINAL_FRAME_HEIGHT)),
        #         pen=pen)

        # guidelines = self.__parent.widget_stabilize.guidelines
        # if guidelines.is_enabled():
        #     x, y = guidelines.coordinates()
        #     # print_lightcyan(f"(x, y) = ({x}, {y})")
        #     # print_lightgrey(f"img_height: {img_height}, FINAL_FRAME_HEIGHT={FINAL_FRAME_HEIGHT}")

        #     pen = QPen(QColor(240, 240, 240))
        #     pen.setStyle(Qt.SolidLine)
        #     self.__lines['stab_hline'] = self.__scene.addLine(QLine(
        #         x, 10,
        #         x, 10 + max(img_height, FINAL_FRAME_HEIGHT + IMG_BORDER_HIGH_RES)),
        #         pen)
        #     self.__lines['stab_vline'] = self.__scene.addLine(QLine(
        #         10, y,
        #         10 + max(img_width, FINAL_FRAME_WIDTH + IMG_BORDER_HIGH_RES), y),
        #         pen)

        self.is_repainting = False


    # def paintEvent(self, event: QPaintEvent):
    #     if self.frame is None:
    #         return

    #     pen_width = PEN_WIDTH

    #     painter = QPainter()
    #     if not painter.begin(self):
    #         return

    #     # qimage: QPixmap = self.frame.qimage
    #     ih, iw, c = self.frame.img.shape
    #     container_w, container_h = self.size().toTuple()
    #     ix0: int = (container_w - iw) // 2
    #     iy0: int = (container_h - ih) // 2

    #     if self.app_type == 'replace':
    #         qimage = QImage(self.frame.img, iw, ih, iw * c, QImage.Format.Format_BGR888)
    #         scaled: QPixmap = QPixmap().fromImage(qimage).scaled(
    #             int(container_w),
    #             int(container_h),
    #             aspectMode=Qt.AspectRatioMode.KeepAspectRatio,
    #             mode=Qt.TransformationMode.FastTransformation
    #         )
    #         iw, ih = scaled.size().toTuple()
    #         ix0: int = (container_w - iw) // 2
    #         iy0: int = (container_h - ih) // 2
    #         painter.drawPixmap(QPoint(ix0, iy0), scaled)
    #         self.draw_widget_guides(painter)
    #         painter.end()
    #         return


    #     preview: GeometryPreviewOptions = self.preview_options
    #     if preview is None:
    #         self.draw_widget_guides(painter)
    #         painter.end()
    #         return

    #     # Select crop values
    #     crop_values = self.get_crop_values(self.scene_geometry.scene)
    #     t, b, l, r = crop_values
    #     cw, ch = iw - (l + r), ih - (t + b)
    #     if (
    #         (preview.crop_edition or preview.crop_preview)
    #         and not preview.resize_preview
    #         and not preview.width_edition
    #         and not preview.final_preview
    #     ):

    #         # Crop rect
    #         if preview.crop_preview:
    #             cropped_img: np.ndarray = np.ascontiguousarray(self.frame.img[t:ih-b,l:iw-r,:])
    #             pixmap: QPixmap = QPixmap().fromImage(
    #                 QImage(cropped_img, cw, ch, cw * c, QImage.Format.Format_BGR888)
    #             )
    #             _cw, _ch = pixmap.size().toTuple()
    #             if  _cw != cw or _ch != ch:
    #                 print(red(f"Error: cropped {_cw}x{_ch} != {cw}x{ch}"))
    #             painter.drawPixmap(
    #                 QPoint(ix0 + l, iy0 + t),
    #                 pixmap
    #             )

    #         elif preview.crop_edition:
    #             qimage = QImage(self.frame.img, iw, ih, iw * c, QImage.Format.Format_BGR888)
    #             pixmap: QPixmap = QPixmap().fromImage(qimage)
    #             painter.drawPixmap(QPoint(ix0, iy0), pixmap)

    #             painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
    #             pen = QPen(COLOR_CROP_RECT)
    #             pen.setWidth(pen_width)
    #             pen.setStyle(Qt.PenStyle.SolidLine)
    #             painter.setPen(pen)
    #             painter.drawRect(
    #                 ix0 + l - PEN_WIDTH, iy0 + t - PEN_WIDTH,
    #                 cw + 2*PEN_WIDTH, ch + 2*PEN_WIDTH
    #             )
    #         self.draw_widget_guides(painter)
    #         painter.end()
    #         return


    #     if (
    #         preview.resize_preview
    #         and not preview.width_edition
    #         and not preview.final_preview
    #     ):
    #         resize_img = self.crop_and_resize(self.frame.img, crop_values, self.scene_geometry)
    #         r_h, r_w = resize_img.shape[:2]
    #         pixmap: QPixmap = QPixmap().fromImage(
    #             QImage(resize_img, r_w, r_h, r_w * c, QImage.Format.Format_BGR888)
    #         )
    #         painter.drawPixmap(
    #             QPoint(
    #                 (container_w - r_w) // 2,
    #                 (container_h - r_h) // 2
    #             ),
    #             pixmap
    #         )
    #         self.draw_widget_guides(painter)
    #         painter.end()
    #         return


    #     if (
    #         preview.width_edition
    #         and not preview.final_preview
    #     ):
    #         # Chapter width
    #         resize_img = self.crop_and_resize(self.frame.img, crop_values, self.scene_geometry)
    #         r_h, r_w = resize_img.shape[:2]
    #         pixmap: QPixmap = QPixmap().fromImage(
    #             QImage(resize_img, r_w, r_h, r_w * c, QImage.Format.Format_BGR888)
    #         )
    #         print(lightcyan(f"resized: {r_w}x{r_h}"))
    #         painter.drawPixmap(
    #             QPoint(
    #                 (container_w - r_w) // 2,
    #                 (container_h - r_h) // 2
    #             ),
    #             pixmap
    #         )

    #         ch_w, ch_h = self.scene_geometry.chapter.width, 1080
    #         ch_x0 = (container_w - ch_w) // 2
    #         ch_x1 = (container_w - ch_w) // 2 + ch_w

    #         painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
    #         pen = QPen(COLOR_PART_CROP_RECT)
    #         pen.setWidth(PEN_WIDTH)
    #         pen.setStyle(Qt.PenStyle.SolidLine)
    #         painter.setPen(pen)
    #         painter.drawLine(
    #             QPoint(ch_x0 - PEN_WIDTH, iy0), QPoint(ch_x0 - PEN_WIDTH, iy0 + ch_h - 1 + 2*PAD)
    #         )
    #         painter.drawLine(
    #             QPoint(ch_x1 - PEN_WIDTH, iy0), QPoint(ch_x1 - PEN_WIDTH, iy0 + ch_h - 1 + 2*PAD)
    #         )

    #         self.draw_widget_guides(painter)
    #         painter.end()
    #         return


    #     if preview.final_preview:
    #         ch_w: int = self.scene_geometry.chapter.width

    #         painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
    #         cx1, cy1 = self.geometry().size().toTuple()
    #         x0 = (cx1 - ch_w) // 2
    #         y0 = (cy1 - FINAL_HEIGHT) // 2
    #         x1 = x0 + ch_w - PEN_WIDTH
    #         y1 = y0 + FINAL_HEIGHT - PEN_WIDTH
    #         painter.fillRect(QRect(QPoint(x0, y0), QPoint(x1, y1)), QColor(0,255,0))
    #         print(f"({x0}, {y0}) -> ({x1}, {y1})")

    #         resize_img = self.crop_and_resize(self.frame.img, crop_values, self.scene_geometry)
    #         r_h, r_w = resize_img.shape[:2]
    #         print(lightgreen(f"resized to: {resize_img.shape}"))
    #         l: int = (r_w - ch_w) // 2
    #         if l < 0:
    #             print(red(f"Error: {r_w} < {ch_w}"))
    #             f_w, f_h = r_w, r_h
    #             pixmap: QPixmap = QPixmap().fromImage(
    #                 QImage(resize_img, r_w, r_h, r_w * c, QImage.Format.Format_BGR888)
    #             )
    #             painter.drawPixmap(
    #                 QPoint(
    #                     (container_w - f_w) // 2,
    #                     (container_h - f_h) // 2
    #                 ),
    #                 pixmap
    #             )

    #         else:
    #             final_img: np.ndarray = np.ascontiguousarray(
    #                 resize_img[:, l : l + ch_w, :]
    #             )
    #             f_h, f_w = final_img.shape[:2]
    #             print(lightgreen(f"final: {final_img.shape} w={ch_w}, l={l}"))
    #             pixmap: QPixmap = QPixmap().fromImage(
    #                 QImage(final_img, ch_w, r_h, ch_w * c, QImage.Format.Format_BGR888)
    #             )
    #             painter.drawPixmap(
    #                 QPoint(
    #                     (container_w - f_w) // 2,
    #                     (container_h - f_h) // 2
    #                 ),
    #                 pixmap
    #             )
    #         self.draw_widget_guides(painter)
    #         painter.end()
    #         return


    #     # else...
    #     pixmap: QPixmap = QPixmap().fromImage(
    #         QImage(self.frame.img, iw, ih, iw * c, QImage.Format.Format_BGR888)
    #     )
    #     ix0: int = (container_w - iw) // 2
    #     iy0: int = (container_h - ih) // 2
    #     painter.drawPixmap(QPoint(ix0, iy0), pixmap)

    #     self.draw_widget_guides(painter)
    #     painter.end()


    def event_key_released(self, event: QKeyEvent) -> bool:
        if event is None:
            return

        for k in self.modif_keys.keys():
            self.modif_keys[k] = False

        self.control_key_pressed = False

        if event.modifiers() & Qt.KeyboardModifier.AltModifier:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.is_alt_key_pressed = False

        return False


    def event_key_pressed(self, event: QKeyEvent) -> bool:
        key, modifiers = event.key(), event.modifiers()
        # print(f"{time.time()} {__name__}.event_key_pressed: {key}, modifiers={modifiers}")

        self.is_alt_key_pressed = modifiers & Qt.KeyboardModifier.AltModifier

        if modifiers & Qt.KeyboardModifier.ControlModifier:
            self.control_key_pressed = True
        else:
            if key == Qt.Key.Key_Z:
                self.event_key_released(None)
                self.modif_keys['radius'] = True
                self.modif_keys['height'] = True
                return True

            elif key == Qt.Key.Key_D:
                self.event_key_released(None)
                self.modif_keys['radius'] = True
                self.modif_keys['width'] = True
                return True

            elif key == Qt.Key.Key_Q:
                self.event_key_released(None)
                self.modif_keys['angle'] = True
                return True

            elif key == Qt.Key.Key_S:
                print("select")
                is_mouse_over_shape: bool = False
                print(f" nb of shapes: {len(self.shapes)}")
                for i, s in enumerate(self.shapes):
                    if s.item.isUnderMouse():
                        print("under mouse")
                        is_mouse_over_shape = True
                        self.modifying_index = i
                        self.modifying_shape = s.item.rect()
                        self._scene.removeItem(s.item)
                        break

                if is_mouse_over_shape:
                    self.setCursor(Qt.CursorShape.OpenHandCursor)
                    return True

            elif key in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
                for i, s in enumerate(self.shapes):
                    if s.item.isUnderMouse():
                        print("delete under mouse")
                        self.modifying_index = -1
                        self._scene.removeItem(s.item)
                        del self.shapes[i]
                        self.setCursor(Qt.CursorShape.ArrowCursor)
                        return True

            elif key == Qt.Key.Key_Escape:
                if self.modifying_index != -1:
                    ellipse = self._scene.addEllipse(
                        self.modifying_shape,
                        pen=QPen(QColor("red")),
                        brush=QBrush(QColor("red"))
                    )
                    ellipse.setOpacity(0.5)
                    ellipse.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
                    self.shapes[self.modifying_index] = ellipse
                    self.modifying_index = -1
                    self.setCursor(Qt.CursorShape.ArrowCursor)
                    return True

        return False



    def event_wheel(self, event: QWheelEvent) -> bool:
        if not any(self.modif_keys.values()):
            if self.shapes and self.modified:
                # do not allow changing frame if modification is on going
                return True

            if self.modifying_index == -1:
                print("not for this")
                return False

        # print(event.angleDelta().y())
        diff: int = 0
        if event.angleDelta().y() > 0:
            diff = 1
        elif event.angleDelta().y() < 0:
            diff = -1

        shape_name: MaskShape = self.main_window.get_current_shape()
        if shape_name == 'circle' and self.modif_keys['radius']:
            self.radius = min(max(self.radius + diff, 0), 20)

        elif shape_name != 'circle':
            if self.modif_keys['width']:
                self.width = min(max(self.width + diff, -90), 90)

            elif self.modif_keys['height']:
                self.height = min(max(self.height + diff, -90), 90)

            elif self.modif_keys['angle']:
                self.angle = min(max(self.angle + 5 * diff, -90), 90)

        self._scene.removeItem(self.shape.item)
        self.shape = None
        self.draw_shape()

        return True


    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Wheel:
            # print_lightcyan(f"eventFilter: widget_controls: wheel")
            if self.event_wheel(event):
                # print(f"\twheel: accepted")
                event.accept()
                return True
            # else:
            #     if self._parent.event_wheel(event):
            #         event.accept()
            #         return

        return super().eventFilter(watched, event)
