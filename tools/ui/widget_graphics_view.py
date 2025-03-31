from __future__ import annotations
from copy import copy, deepcopy
from dataclasses import dataclass
from pprint import pprint
import time
from logger import log

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
    QMouseEvent,
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
    DsrRegion,
)
from .widget_dsr import DsrSceneRegion, dsr_mask_to_scene
from utils.p_print import *
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



class GraphicsViewWidget(QGraphicsView):
    signal_wheel_event = Signal(QWheelEvent)

    # DSR
    signal_dsr_updated_event = Signal(list)


    def __init__(
        self,
        parent: QWidget | ReplaceWindow,
        main_window: ReplaceWindow,
        controller,
        app_type: AppType,
    ) -> None:
        super().__init__(parent)

        self.app_type: AppType = app_type
        self._parent = parent
        self.main_window = main_window

        self.controller: ReplaceController = controller
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
        self.img_size: list[float, float] | tuple[float, float] = (0, 0)
        self.is_repainting = False


        self._pixmap_item = QGraphicsPixmapItem()
        self._scene.addItem(self._pixmap_item)
        self.current_position: QPointF = None
        self.cursor_offset = QPointF(0, 0)
        self.is_alt_key_pressed: bool = False


        self.modif_keys: dict[str, bool] = {
            'radius': False,
            'width': False,
            'height': False,
            'angle': False,
        }
        self.radius: int = 0.015
        self.width: int = 0.025
        self.height: int = 0.015
        self.angle: float = -45
        # sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # sizePolicy.setHorizontalStretch(0)
        # sizePolicy.setVerticalStretch(0)
        # sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())

        # self.setSizePolicy(sizePolicy)
        # self.setMinimumSize(QSize(300, 300))
        # self.setStyleSheet(u"background-color: rgb(0, 0, 0);")
        # self.scene_geometry: TargetSceneGeometry | None = None
        # self.preview_options: GeometryPreviewOptions | None = None

        self.regions: list[DsrSceneRegion] = []
        self.default_region: DsrSceneRegion = DsrSceneRegion(
            shape='circle',
            center=(0.5, 0.5),
            axes=(0.025, 0.015),
            angle=0,
            item=None
        )
        self.new_region: DsrSceneRegion = deepcopy(self.default_region)
        self.modifying_shape: bool = False
        self.previous_dsr_region = None

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
        self.frame: Frame = frame
        h, w = self.frame.img.shape[:2]
        self.img_size = (float(w), float(h))
        self.draw_image()


    def repaint_frame(self):
        self.draw_image()



    def add_region_to_scene(
        self,
        region: DsrRegion | DsrSceneRegion
    ) -> DsrSceneRegion:
        # Convert from Mask to SceneSHape
        if isinstance(region, DsrRegion):
            region: DsrSceneRegion = dsr_mask_to_scene(region)

        # Draw/Add item to scene
        s = region.map_to_scene(self.img_size)
        x, y = s.center
        axes = s.axes if s.shape != 'circle' else [s.axes[0], s.axes[0]]
        item: QGraphicsEllipseItem = QGraphicsEllipseItem(
            QRectF(x - axes[0], y - axes[1], 2 * axes[0]+1, 2 * axes[1]+1)
        )
        # item.setRotation(self.angle)
        item.setOpacity(0.5)
        item.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        item.setBrush(QBrush(QColor("red")))
        item.setPen(QPen(QColor("red")))
        item.setTransformOriginPoint(x, y)
        item.setRotation(s.angle)

        region.item = item
        self._scene.addItem(region.item)

        return region


    def set_patch_edition(self, enabled: bool):
        if not enabled:
            self._scene.removeItem(self.new_region.item)
            self.new_region = None

    def append_dsr_region(self, recall: bool = False) -> None:
        if recall and self.previous_dsr_region is not None:
            self._scene.removeItem(self.new_region.item)
            self.new_region = self.previous_dsr_region.copy()
            self._scene.addItem(self.new_region.item)
        else:
            self.previous_dsr_region = self.new_region.copy()
        self.regions.append(self.new_region.copy())
        self.cursor_offset = QPointF(0, 0)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.new_region.item = None
        self.modifying_shape = False
        self.signal_dsr_updated_event.emit(self.regions)


    def start_modifying_shape(self, selected: DsrSceneRegion) -> None:
        print(lightcyan("start moving shape"))
        # Remove from scene and list of shapes
        self._scene.removeItem(self.new_region.item)
        self._scene.removeItem(selected.item)

        # Save current shape to restore it if discarded
        selected.item = None
        self._saved_region = deepcopy(selected)

        # Use selected shape as a new shape
        self.new_region = selected.copy()
        self.axes = self.new_region.axes
        self.radius = self.new_region.axes[0]
        self.angle = self.new_region.angle
        self.main_window.set_current_dsr_shape(self.new_region.shape)

        # Get position and calculate offset from position to center of shape
        cursor_position: QPointF = self.mapToScene(self.current_position.toPoint())
        self.cursor_offset = QPointF(*self.new_region.center) - cursor_position
        w, h = self.img_size
        self.cursor_offset = QPointF(
            self.cursor_offset.x() / w,
            self.cursor_offset.y() / h
        )
        print(f"  shape center: {self.new_region.center}")
        print(f"  cursor_position: {cursor_position}")
        print(f"  cursor_offset: {self.cursor_offset}")

        # Modify center of the item
        # w, h = self.img_size
        # cursor_position = cursor_position + self.cursor_offset
        # x, y = (cursor_position / self.w ).toTuple()

        # self.new_region.center = (x, y)
        self.modifying_shape = True
        self.add_region_to_scene(self.new_region)


    def discard_modifying_shape(self, current_position: QPointF) -> None:
        if not self.modifying_shape:
            return

        self.regions.append(deepcopy(self._saved_region))
        print("Discard shape, restore shape:")
        pprint(self.regions[-1])
        self.add_region_to_scene(self.regions[-1])

        # Finally, new shape
        self.modifying_shape = False
        self.cursor_offset = QPointF(0, 0)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self._scene.removeItem(self.new_region.item)

        self.new_region: DsrSceneRegion = deepcopy(self.default_region)
        self.draw_new_region(current_position)

        self.signal_dsr_updated_event.emit(self.regions)


    def draw_new_region(self, cursor_position: QPointF) -> None:
        if self.current_position is None:
            return

        if self.new_region.item is None:
            cursor_position = cursor_position + self.cursor_offset
            # print(f"draw item at {cursor_position.toTuple()}, offset={self.cursor_offset.toTuple()}")
            x, y = cursor_position.toTuple()
            w, h = self.img_size

            shape_name: MaskShape = self.main_window.get_current_dsr_shape()
            axes: tuple[float, float] = (
                (self.radius, self.radius * w / h)
                if shape_name == 'circle'
                else (self.width, self.height)
            )

            x0, y0 = x - axes[0] * w, y - axes[1] * h
            item: QGraphicsEllipseItem = QGraphicsEllipseItem(
                x0, y0, 2 * axes[0] * w, 2 * axes[1] * h
            )
            item.setOpacity(0.5)
            item.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
            item.setBrush(QBrush(QColor("red")))
            item.setPen(QPen(QColor("red")))
            item.setTransformOriginPoint(x, y)
            item.setRotation(self.angle)

            self.new_region.item = item
            self.new_region.shape = shape_name
            self.new_region.center = (x/w, y/h)
            self.new_region.axes = axes
            self.new_region.angle = self.angle

            # print(f"  moving: {self.new_region.center}, {self.new_region.axes}")
            self._scene.addItem(self.new_region.item)

            # self.modified = True


    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() in (
            Qt.MouseButton.ForwardButton, Qt.MouseButton.BackButton
        ):
            return

        if self.new_region is not None:
            self.regions.append(self.new_region.copy())
            self.cursor_offset = QPointF(0, 0)
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.new_region.item = None
            self.signal_dsr_updated_event.emit(self.regions)
        else:
            raise ValueError("new_region is None")
        return super().mouseDoubleClickEvent(event)


    def mouseMoveEvent(self, event):
        # print(f"mouseMoveEvent: {event.position()}")
        self.current_position = self.mapToScene(event.position().toPoint())

        # TODO: limit to image size
        cursor_position = self.mapToScene(event.position().toPoint())
        w, h = self.img_size
        outside: bool = False
        if cursor_position.x() > min(self.size().width(), w):
            cursor_position.setX(min(self.size().width(), w))
            outside = True
        if cursor_position.y() > min(self.size().height(), h):
            cursor_position.setY(min(self.size().height(), h))
            outside = True

        if self.new_region.item is not None:
            self._scene.removeItem(self.new_region.item)
            self.new_region.item = None

        if not outside:
            self.draw_new_region(
                cursor_position=self.mapToScene(self.current_position.toPoint())
            )

        super().mouseMoveEvent(event)


    def mousePressEvent(self, event: QMouseEvent):
        print(f"widget graphics: pressEvent: {event.button()}")
        return self._parent.mousePressEvent(event=event)


    def mouse_press_event(self, event: QMouseEvent):
        # Append the shape to the list of patches

        if self.control_key_pressed:
            self.append_dsr_region()

        elif self.modifying_shape:
            print("Moved")
            self.modifying_shape = False
            # center: QPointF = event.position() + self.cursor_offset
            self.regions.append(self.new_region.copy())
            self.cursor_offset = QPointF(0, 0)
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.new_region.item = None
            self.signal_dsr_updated_event.emit(self.regions)

        elif not self.modifying_shape:
            # start moving shape
            is_mouse_over_shape: bool = False
            for i, s in enumerate(reversed(self.regions)):
                if s.item is None:
                    continue
                if s.item.isUnderMouse():
                    print("under mouse")
                    is_mouse_over_shape = True
                    self.start_modifying_shape(s)
                    del self.regions[len(self.regions) - i - 1]
                    self.signal_dsr_updated_event.emit(self.regions)
                    break

            if is_mouse_over_shape:
                print("selected a shape")


                self.setCursor(Qt.CursorShape.OpenHandCursor)

                return True

        return False


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
        print(f"{time.time()} {__name__}.event_key_pressed: 0x{key:3X}, modifiers={modifiers}")

        self.is_alt_key_pressed = modifiers & Qt.KeyboardModifier.AltModifier

        if modifiers & Qt.KeyboardModifier.ControlModifier:
            self.control_key_pressed = True
            return False

        if key == Qt.Key.Key_Asterisk:
            self.append_dsr_region(recall=True)
            return True

        if key == Qt.Key.Key_Plus:
            self.append_dsr_region()
            return True

        elif key in (Qt.Key.Key_S, Qt.Key.Key_Z, Qt.Key.Key_8):
            self.event_key_released(None)
            self.modif_keys['radius'] = True
            self.modif_keys['height'] = True
            return True

        elif key in (Qt.Key.Key_Q, Qt.Key.Key_6):
            self.event_key_released(None)
            self.modif_keys['radius'] = True
            self.modif_keys['width'] = True
            return True

        elif key in (Qt.Key.Key_D, Qt.Key.Key_5):
            self.event_key_released(None)
            self.modif_keys['angle'] = True
            return True

        elif key in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace, Qt.Key.Key_Minus):
            for i, s in enumerate(self.regions):
                if s.item.isUnderMouse():
                    print("delete under mouse")
                    self.modifying_index = -1
                    self._scene.removeItem(s.item)
                    del self.regions[i]
                    self.setCursor(Qt.CursorShape.ArrowCursor)
                    self.cursor_offset = QPoint(0, 0)
                    self.signal_dsr_updated_event.emit(self.regions)
                    return True

        elif key == Qt.Key.Key_Escape:
            self.discard_modifying_shape(self.current_position)
            return True

        return False


    def wheelEvent(self, event: QKeyEvent) -> bool:
        return self._parent.wheelEvent(event)


    def event_wheel(self, event: QWheelEvent) -> bool:
        print(f"graphics viewevent_wheel with {self.modif_keys}")
        is_editing: bool = any(self.modif_keys.values())

        if not is_editing:
            print(f"\tnot for self: editing{self._parent.is_editing_patches()}, any key: {any(self.modif_keys.values())}")
            return False

        # print(event.angleDelta().y())
        diff: int = 0
        if event.angleDelta().y() > 0:
            diff = 1
        elif event.angleDelta().y() < 0:
            diff = -1

        shape_name: MaskShape = self.main_window.get_current_dsr_shape()
        w, h = self.img_size
        if shape_name == 'circle' and self.modif_keys['radius']:
            diff /= w
            self.radius = min(max(self.radius + diff, 0), 0.25)

        elif shape_name != 'circle':
            if self.modif_keys['width']:
                diff /= w
                self.width = min(max(self.width + diff, 0), 0.25)

            elif self.modif_keys['height']:
                diff /= h
                self.height = min(max(self.height + diff, 0), 0.25)

            elif self.modif_keys['angle']:
                self.angle = min(max(self.angle - 5 * diff, -90), 90)

        self._scene.removeItem(self.new_region.item)
        self.new_region.item = None
        self.draw_new_region(
            cursor_position=self.mapToScene(self.current_position.toPoint())
        )

        return True


    # def eventFilter(self, watched: QObject, event: QEvent) -> bool:
    #     if event.type() == QEvent.Type.Wheel:
    #         print(lightcyan(time.time()), f"graphics view, eventFilter: wheel")
    #         if self.event_wheel(event):
    #             # print(f"\twheel: accepted")
    #             event.accept()
    #             return True
    #         # else:
    #         #     if self._parent.event_wheel(event):
    #         #         event.accept()
    #         #         return

    #     return super().eventFilter(watched, event)


    def event_shape_changed(self, shape_name: MaskShape) -> None:
        if self.new_region is not None:
            self._scene.removeItem(self.new_region.item)
            self.new_region.item = None
        self.draw_new_region(
            cursor_position=self.mapToScene(self.current_position.toPoint())
        )



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


    def draw_image(self):
        # print("viewport geometry:", self.viewport().geometry())
        # print("sceneRect geometry:", self.sceneRect())
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
        # print(red(f"draw image {self.frame.no}"))
        for shape in self.regions:
            self._scene.removeItem(shape.item)
        self.regions.clear()

        dsr_shapes = self.controller.playlist_dsr(frame_no=self.frame.no)
        for mask in dsr_shapes:
            self.regions.append(self.add_region_to_scene(mask))

        initial_img_height, initial_img_width, c = img.shape
        img_height, img_width, c = img.shape
        try:
            q_image = QImage(img.data, img_width, img_height, img_width * 3, QImage.Format_BGR888)
        except:
            print(red("paintEvent: cannot convert img to qImage"))
            return


        self._pixmap_item.setPixmap(QPixmap.fromImage(q_image))
        self._pixmap_item.setPos(0, 0)



        self.is_repainting = False


