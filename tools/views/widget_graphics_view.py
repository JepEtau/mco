# -*- coding: utf-8 -*-
import sys
sys.path.append('scripts')

import numpy as np
import cv2
from pprint import pprint
from logger import log
from utils.pretty_print import *
from operator import itemgetter

from PySide6.QtCore import (
    QPoint,
    QSize,
    Qt,
    Signal,
    QEvent,
    QObject,
    QRectF,
    QPointF,
    QRect,
    QLine,
)
from PySide6.QtGui import (
    QColor,
    QImage,
    QPen,
    QBrush,
    QPixmap,
    QPainter,
    QKeyEvent,
    QPaintEvent,
    QWheelEvent,
    QColor,
)
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QGraphicsScene,
    QGraphicsEllipseItem,
    QGraphicsPolygonItem,
    QGraphicsView,
    QGraphicsPixmapItem,
    QGraphicsItem,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QFrame,
    QStyle,
)


from views.window_common import (
    Window_common,
    PAINTER_MARGIN_LEFT,
    PAINTER_MARGIN_TOP,
)
from filters.python_geometry import IMG_BORDER_HIGH_RES
from filters.utils import (
    FINAL_FRAME_HEIGHT,
    FINAL_FRAME_WIDTH,
    get_dimensions_from_crop_values,
)

COLOR_PART_CROP_RECT = QColor(30, 230, 30)
COLOR_CROP_RECT = QColor(230, 30, 30)
COLOR_FINAL_RECT = QColor(0, 255, 0)
COLOR_DISPLAY_RECT = QColor(255, 255, 255)
# PEN_CROP_SIZE must be equal to 1 or 2
PEN_CROP_SIZE = 1

class QPolygonCustom(QGraphicsPolygonItem):
    def paint(self, painter, option, widget):
        option.state &= ~ QStyle.StateFlag.State_Selected
        super(QPolygonCustom, self).paint(painter, option, widget)



class Widget_graphics_view(QGraphicsView):
    signal_regions_modified = Signal(list)

    def __init__(self, parent, ui, controller):
        super().__init__(parent)

        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.Shape.Panel)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self.setFrameStyle(0)

        self.__scene = QGraphicsScene(self)
        self.setScene(self.__scene)

        # self.__scene.setSceneRect(0,0,1920,1080)

        # self._pixmap_item = QGraphicsPixmapItem()
        # self.__scene.addItem(self._pixmap_item)

        self.__is_drawing_polygon = True
        self.__current_polygon = None  # the selected polygon
        self.new_polygon_points = []  # points that are stored when recording
        self.__current_polygon_points = list()
        self.__control_points = list()
        self.__selected_control_point = None

        # Rect, guidelines
        self.__lines = {
            'crop_rect': None,
            'final_rect': None,
            'final_rect2': None,
            'width_rect': None,
            'split': None,
            'stab_vline': None,
            'stab_hline': None,
        }

        # Debug
        # self.new_polygon_points.append(QPointF(50,50))
        # self.new_polygon_points.append(QPointF(50,389))
        # self.new_polygon_points.append(QPointF(400,400))
        # self.new_polygon_points.append(QPointF(400,123))
        # self.draw_polygon()

        self.control_key_pressed = False

        self.image = None
        self.is_repainting = False
        self.__parent = ui

        self._pixmap_item = QGraphicsPixmapItem()
        # self._pixmap_item.setPos(PAINTER_MARGIN_LEFT, PAINTER_MARGIN_TOP)
        self.__scene.addItem(self._pixmap_item)

        # self.setBackgroundBrush(QBrush(QColor("grey")))
        # self.__scene.setBackgroundBrush(QBrush(QColor("blue")))

        self.__is_editing_tracker = False
        # No time to develop, f**k OOP:
        self.__controller = controller
        self.__tracker = None
        self.__is_modifying = False
        self.poly_points = list()
        self.__is_drawing_polygon = False

        self.installEventFilter(self)


    def show_image(self, image):
        self.image = image
        self.draw_image()


    def repaint_frame(self):
        self.draw_image()


    def refresh_preview_options(self, options):
        if options['stabilize']['show_tracker'] and not self.__is_editing_tracker:
            self.__is_editing_tracker = True
            self.draw_tracker_regions()

        self.__is_editing_tracker = options['stabilize']['show_tracker']

        if not self.__is_editing_tracker:
            self.erase_tracker_regions()


    def event_segment_selected(self, segment):
        verbose = False

        if verbose:
            log.info("segment has been select, store segment tracking regions")
            print_purple(f"graphics_view: event_segment_selected")
            # pprint(segment)
        self.erase_tracker_regions()
        try:
            self.__tracker = segment['tracker']
        except:
            self.__tracker = None
        self.draw_tracker_regions()


    def draw_tracker_regions(self):
        if self.__tracker is None:
            self.erase_tracker_regions()
            return

        if self.__tracker['enable'] and self.__is_editing_tracker:
            self.repaint_frame()

            for region in self.__tracker['regions']:
                for point in region:
                    self.new_polygon_points.append(QPointF(point[0], point[1]))
                self.draw_polygon()

    def is_modifying_tracking_regions(self) -> bool:
        return self.__is_editing_tracker


    def draw_image(self):
        # print("viewport geometry:", self.viewport().geometry())
        # print("sceneRect geometry:", self.sceneRect())
        self.setSceneRect(0,0,self.viewport().geometry().width(), self.viewport().geometry().height())

        verbose = False
        # pprint(self.__scene.items())
        # print(self.__scene.sceneRect())

        if self.image is None:
            if verbose:
                print_orange("no image loaded")
            log.info("no image loaded")
            return

        img = self.image['cache']
        if img is None:
            if verbose:
                print_orange("no image cached")
            return
        if self.image['cache_initial'] is None:
            return

        if self.is_repainting:
            print_red("error: self.is_repainting is True!!")
            log.error("error: self.is_repainting is True!!")
            return
        self.is_repainting = True


        initial_img_height, initial_img_width, c = self.image['cache_initial'].shape
        img_height, img_width, c = img.shape
        try:
            q_image = QImage(img.data, img_width, img_height, img_width * 3, QImage.Format_BGR888)
        except:
            print_red("paintEvent: cannot convert img to qImage")
            return

        preview = self.image['preview_options']

        # delta_y = self.__parent.display_position_y
        delta_y = 0

        preview = self.image['preview_options']
        # print_lightgreen("paintEvent: preview")
        # pprint(preview)
        initial_img_height, initial_img_width, c = self.image['cache_initial'].shape
        # print("paintEvent: initial image = %dx%d" % (initial_img_height, initial_img_width))
        img_height, img_width, c = img.shape
        try:
            q_image = QImage(img.data, img_width, img_height, img_width * 3, QImage.Format_BGR888)
        except:
            print_red("paintEvent: cannot convert img to qImage")
            return

        # Shot geometry
        geometry = self.image['geometry']
        shot_geometry = geometry['shot']
        if shot_geometry is None and 'default' in geometry.keys():
            shot_geometry = geometry['default']


        # self.image['origin'] = [PAINTER_MARGIN_LEFT, PAINTER_MARGIN_TOP - delta_y]
        # print_lightgreen(f"paintEvent: begin, delta: {delta_y}")
        # print(shot_geometry)
        for k in self.__lines.keys():
            try:
                if self.__lines[k] is not None:
                    self.__scene.removeItem(self.__lines[k])
                self.__lines[k] = None
            except: pass

        if preview['geometry']['final_preview']:
            if verbose:
                print_purple("draw_image: display final_preview")
            self._pixmap_item.setPixmap(QPixmap.fromImage(q_image))
            self._pixmap_item.setPos(0, 0)

        else:
            preview_shot_geometry = preview['geometry']['shot']

            if preview_shot_geometry['crop_edition'] and not preview_shot_geometry['crop_preview']:
                # Add a red rectangle to the image

                if preview_shot_geometry['resize_preview']:
                    # Resize the image (i.e. draw rect on the resized image)
                    if verbose:
                        print_purple("draw_image: draw rect on the resized image")
                    x0 = 0
                    y0 = 0 - delta_y

                    # Patch the crop value if displaying deshaked shot
                    # crop = shot_geometry['crop']
                    # if not preview['geometry']['add_borders']:
                    #     crop = list(map(lambda x: x + IMG_BORDER_HIGH_RES, shot_geometry['crop']))

                    # # Image is resized, add the recalculated crop
                    # crop_top, crop_bottom, crop_left, crop_right, cropped_width, cropped_height = get_dimensions_from_crop_values(
                    #     width=initial_img_width, height=initial_img_height, crop=crop)
                    # w_tmp = int((cropped_width * FINAL_FRAME_HEIGHT) / float(cropped_height))
                    # pprint(self.image['geometry_values'])
                    crop_left = self.image['geometry_values']['crop'][2]
                    crop_top = self.image['geometry_values']['crop'][0]
                    cropped_height = self.image['geometry_values']['initial']['h'] - (self.image['geometry_values']['crop'][0] + self.image['geometry_values']['crop'][1])

                    w_tmp = self.image['geometry_values']['resize']['w']
                    pad_left = int(((FINAL_FRAME_WIDTH - w_tmp) / 2))

                    ratio = np.float32(cropped_height) / FINAL_FRAME_HEIGHT
                    crop_left = int(crop_left / ratio)
                    crop_top = int(crop_top / ratio)

                    # print("\t-> w=%d, c_w=%d, w_tmp=%d, pad: %d" % (w, c_w, w_tmp, pad_left))
                    # print("\t-> crop_left=%d, crop_top=%d" % (c_l, crop_top))

                    self.image['origin'] = [x0 + pad_left - crop_left, y0 - crop_top]

                    self._pixmap_item.setPixmap(QPixmap.fromImage(q_image))
                    self._pixmap_item.setPos(pad_left - crop_left, 0 - crop_top)


                    # Add the cropped resized rect
                    pen = QPen(COLOR_CROP_RECT)
                    pen.setWidth(PEN_CROP_SIZE)
                    pen.setStyle(Qt.SolidLine)
                    self.__lines['crop_rect'] = self.__scene.addRect(QRect(
                        pad_left - 1,
                        - delta_y - 1,
                        w_tmp + 1,
                        FINAL_FRAME_HEIGHT + 1), pen=pen)

                    # Add the final 1080p rect
                    pen = QPen(COLOR_DISPLAY_RECT)
                    pen.setWidth(PEN_CROP_SIZE)
                    pen.setStyle(Qt.SolidLine)
                    self.__lines['final_rect'] = self.__scene.addRect(QRect(
                        - 1,
                        - delta_y - 1,
                        FINAL_FRAME_WIDTH + 1,
                        FINAL_FRAME_HEIGHT + 1), pen=pen)

                else:
                    if verbose:
                        print_purple("draw_image: draw rect crop on the original image")
                    # Original
                    x0 = 0
                    y0 = - delta_y
                    crop = shot_geometry['crop']
                    if not preview['geometry']['add_borders']:
                        crop = list(map(lambda x: x + IMG_BORDER_HIGH_RES, shot_geometry['crop']))

                    self._pixmap_item.setPixmap(QPixmap.fromImage(q_image))
                    self._pixmap_item.setPos(0, 0)

                    # painter.drawImage(QPoint(x0, y0), q_image)

                    # Add a red rect for the crop
                    crop_top, crop_bottom, crop_left, crop_right, cropped_width, cropped_height = get_dimensions_from_crop_values(
                        width=initial_img_width, height=initial_img_height, crop=crop)

                    # print(f"({crop_left}, {crop_top}) -> ({cropped_width},{cropped_height})")
                    pen = QPen(COLOR_CROP_RECT)
                    pen.setWidth(PEN_CROP_SIZE)
                    pen.setStyle(Qt.SolidLine)

                    # https://doc.qt.io/qt-6/qrect.html, PEN_CROP_SIZE = 1
                    # print("\timg: %dx%d" % (img.data.shape[1], img.data.shape[0]))
                    # print("\trect: (%d;%d) w=%d, h=%d" % (c_l - 1, c_t - delta_y - 1, c_w + 1, c_h + 1))
                    self.__lines['crop_rect'] = self.__scene.addRect(QRect(
                        crop_left - 1,
                        crop_top - delta_y - 1,
                        cropped_width + 1,
                        cropped_height + 1), pen=pen)


            elif preview_shot_geometry['crop_preview']:
                # Image is cropped

                if preview_shot_geometry['resize_preview']:
                    # Image is also resized
                    if verbose:
                        print_purple("draw_image: resized cropped image")

                    # if not preview['geometry']['add_borders']:
                    #     crop_top, crop_bottom, crop_left, crop_right, cropped_width, cropped_height = get_dimensions_from_crop_values(
                    #         width=initial_img_width, height=initial_img_height, crop=shot_geometry['crop'])

                    # w_tmp = int((cropped_width * FINAL_FRAME_HEIGHT) / float(cropped_height))
                    # pad_left = int(((FINAL_FRAME_WIDTH - img_width) / 2) + 0.5)
                    pad_left = self.image['geometry_values']['pad']['left']
                    if self.image['geometry_values']['pad_error'] is not None:
                        pad_left += self.image['geometry_values']['pad_error'][2]

                    self.image['origin'] = [
                        pad_left,
                        - delta_y]
                    self._pixmap_item.setPixmap(QPixmap.fromImage(q_image))
                    self._pixmap_item.setPos(pad_left, - delta_y)

                    # Add the final 1080p rect
                    pen = QPen(COLOR_DISPLAY_RECT)
                    pen.setWidth(PEN_CROP_SIZE)
                    pen.setStyle(Qt.SolidLine)
                    self.__lines['crop_rect'] = self.__scene.addRect(QRect(
                        - 1,
                        - delta_y - 1,
                        FINAL_FRAME_WIDTH + 1,
                        FINAL_FRAME_HEIGHT + 1), pen=pen)

                else:
                    if verbose:
                        print_purple("draw_image: cropped image on the original image")
                    # print("paintEvent: draw cropped image on the original image")
                    # Crop and no rect
                    crop = shot_geometry['crop']
                    if not preview['geometry']['add_borders']:
                        crop = list(map(lambda x: x + IMG_BORDER_HIGH_RES, shot_geometry['crop']))
                    crop_top, crop_bottom, crop_left, crop_right, cropped_width, cropped_height = get_dimensions_from_crop_values(
                        width=initial_img_width, height=initial_img_height, crop=crop)

                    self._pixmap_item.setPixmap(QPixmap.fromImage(q_image))
                    self._pixmap_item.setPos(crop_left, crop_top)


            else:
                # original
                if verbose:
                    print_purple("draw_image: original image")

                if preview['geometry']['add_borders']:
                    # painter.drawImage(
                    #     QPoint(PAINTER_MARGIN_LEFT+IMG_BORDER_HIGH_RES, PAINTER_MARGIN_TOP+IMG_BORDER_HIGH_RES - delta_y),
                    #     q_image.scaled(q_image.width()*2, q_image.height()*2, aspectMode=Qt.KeepAspectRatio))
                    self._pixmap_item.setPixmap(QPixmap.fromImage(
                        q_image.scaled(q_image.width()*2, q_image.height()*2, aspectMode=Qt.KeepAspectRatio)))
                    self._pixmap_item.setPos(IMG_BORDER_HIGH_RES, IMG_BORDER_HIGH_RES)
                else:
                    self._pixmap_item.setPixmap(QPixmap.fromImage(q_image))
                    self._pixmap_item.setPos(0, 0)
                    # painter.drawImage(
                    #     QPoint(PAINTER_MARGIN_LEFT, PAINTER_MARGIN_TOP - delta_y), q_image)

            if (preview['geometry']['target']['width_edition']
                and preview_shot_geometry['crop_edition']
                and preview_shot_geometry['resize_preview']):

                # Add the target rect
                pad_left = ((FINAL_FRAME_WIDTH - geometry['target']['w']) / 2) + 0.5
                pen = QPen(COLOR_PART_CROP_RECT)
                pen.setWidth(PEN_CROP_SIZE)
                pen.setStyle(Qt.SolidLine)
                self.__lines['width_rect'] = self.__scene.addRect(QRect(
                    pad_left - 1,
                    - delta_y - 1,
                    geometry['target']['w'] + 1,
                    FINAL_FRAME_HEIGHT + 1), pen=pen)

                # Add the final 1080p rect
                pen = QPen(COLOR_DISPLAY_RECT)
                pen.setWidth(PEN_CROP_SIZE)
                pen.setStyle(Qt.SolidLine)
                self.__lines['final_rect2'] = self.__scene.addRect(QRect(
                    - 1,
                    - delta_y - 1,
                    FINAL_FRAME_WIDTH + 1,
                    FINAL_FRAME_HEIGHT + 1), pen=pen)


        if preview['curves']['split']:
            try: crop_top = 0 if preview_shot_geometry['resize_preview'] else (-1*crop_top)
            except:  crop_top = 0
            pen = QPen(QColor(255,255,255))
            pen.setStyle(Qt.DashLine)
            self.__lines['split'] = self.__scene.addLine(QLine(
                preview['curves']['split_x'], - crop_top,
                preview['curves']['split_x'], - crop_top + max(img_height, FINAL_FRAME_HEIGHT)),
                pen=pen)

            # painter.setPen(pen)
            # painter.drawLine(
            #     preview['curves']['split_x'] + PAINTER_MARGIN_LEFT, PAINTER_MARGIN_TOP - crop_top,
            #     preview['curves']['split_x'] + PAINTER_MARGIN_LEFT, PAINTER_MARGIN_TOP - crop_top + max(img_height, FINAL_FRAME_HEIGHT))

        guidelines = self.__parent.widget_stabilize.guidelines
        if guidelines.is_enabled():
            x, y = guidelines.coordinates()
            # print_lightcyan(f"(x, y) = ({x}, {y})")
            # print_lightgrey(f"img_height: {img_height}, FINAL_FRAME_HEIGHT={FINAL_FRAME_HEIGHT}")

            pen = QPen(QColor(240, 240, 240))
            pen.setStyle(Qt.SolidLine)
            self.__lines['stab_hline'] = self.__scene.addLine(QLine(
                x, 10,
                x, 10 + max(img_height, FINAL_FRAME_HEIGHT + IMG_BORDER_HIGH_RES)),
                pen)
            self.__lines['stab_vline'] = self.__scene.addLine(QLine(
                10, y,
                10 + max(img_width, FINAL_FRAME_WIDTH + IMG_BORDER_HIGH_RES), y),
                pen)

        self.is_repainting = False


    def event_region_modified(self):
        log.info("region modified")
        print_lightcyan("region modified")
        regions = list()
        for item in self.__scene.items():
            if type(item) == QPolygonCustom:
                points = list([item.mapToScene(x) for x in item.polygon()])
                regions.append(list([[int(point.x()), int(point.y())] for point in points]))
        pprint(regions)
        self.signal_regions_modified.emit(regions)


    def erase_tracker_regions(self):
        # print(f"erase_tracker_region")
        self.remove_control_points()
        for item in self.__scene.items():
            if type(item) == QPolygonCustom:
                self.__scene.removeItem(item)


    def record(self):
        print("record")
        self.__is_drawing_polygon = True


    def remove_selected_item(self):
        if self.__selected_control_point is not None:
            print(f"delete corner: {self.__current_polygon.polygon().count()}")
            if self.__current_polygon.polygon().count() > 3:
                print("delete corner")
                index = self.__selected_control_point[1]
                self.remove_control_points()
                polygon = self.__current_polygon.polygon()
                polygon.remove(index)
                self.__current_polygon.setPolygon(polygon)
                self.show_control_points()

                self.event_region_modified()
                self.__is_modifying = False

        elif self.__current_polygon is not None:
            print("delete selected polygon")
            # polygon_points = [self.__current_polygon.mapToScene(x) for x in self.__current_polygon.polygon()]
            # for point in polygon_points:
            #     self.__scene.removeItem(point).
            self.remove_control_points()
            self.__current_polygon_points.clear()
            self.__scene.removeItem(self.__current_polygon)
            self.__current_polygon = None

            self.event_region_modified()
            self.__is_modifying = False


    def remove_control_points(self):
        """ removes the control points (i,e the ellipse)"""
        # print("remove_control_points")
        for ellipse, _ in self.__control_points:
            self.__scene.removeItem(ellipse)
        self.__control_points.clear()
        self.__selected_control_point = None


    def show_control_points(self):
        # save polygon points
        self.__current_polygon_points = [self.__current_polygon.mapToScene(x) for x in self.__current_polygon.polygon()]

        self.__control_points.clear()
        for index, point in enumerate(self.__current_polygon_points):
            x, y = point.x(), point.y()
            ellipse = self.__scene.addEllipse(QRectF(x - 4, y - 4, 7, 7),
                                                pen=QPen(QColor("red")))
                # brush=QBrush(QColor("red")))
            ellipse.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
            self.__control_points.append((ellipse, index))
        self.__selected_control_point = None


    def mousePressEvent(self, event):
        if not self.__is_editing_tracker:
            return self.__parent.mousePressEvent(event)

        super(Widget_graphics_view, self).mousePressEvent(event)
        cursor_position = self.mapToScene(event.position().toPoint())

        if (event.button() == Qt.MouseButton.LeftButton
            and self.control_key_pressed
            and not self.__is_drawing_polygon):
            print("add a new point at position:" , cursor_position)
            if self.__current_polygon is not None:
                x, y = cursor_position.x(), cursor_position.y()
                # ellipse = self.__scene.addEllipse(QRectF(x - 3, y - 3, 5, 5),
                #     brush=QBrush(QColor("yellow")))
                self.remove_control_points()

                # print(self.__current_polygon)
                points_list = self.__current_polygon.polygon().toVector()
                distances = list()
                for i, p in zip(range(len(points_list)), points_list):
                    diff = p - cursor_position
                    distance = diff.x()**2 + diff.y()**2
                    distances.append([distance, i])
                distances = sorted(distances, key=itemgetter(0))
                pprint(distances)

                points = [self.__current_polygon.mapToScene(x) for x in self.__current_polygon.polygon()]
                if ((distances[0][1] == 0 and distances[1][1] == len(points) - 1)
                    or (distances[0][1] == len(points) - 1 and distances[1][1] == 0)):
                    points.append(cursor_position)
                else:
                    index = max(distances[0][1], distances[1][1])
                    points.insert(index, cursor_position)
                self.__current_polygon.setPolygon(points)
                self.show_control_points()
                # self.control_key_pressed = False
                # self.event_region_modified()
                self.__is_modifying = True

        if self.__is_drawing_polygon:
            print_lightcyan(f"drawing polygon")
            self.__selected_control_point = None
            if event.button() == Qt.MouseButton.RightButton:
                self.draw_polygon()
            elif event.button() == Qt.MouseButton.LeftButton:
                print("recording point")
                self.new_polygon_points.append(cursor_position)
            return

        if event.button() == Qt.MouseButton.RightButton:
            self.__selected_control_point = None
            return

        # self.__scene.mousePressEvent(event)
        super(Widget_graphics_view, self).mousePressEvent(event)

        if self.__selected_control_point is not None:
            self.__selected_control_point[0].setBrush(QBrush(Qt.BrushStyle.NoBrush))

        # Check if a point is selecteds
        for point in self.__control_points:
            if point[0].contains(cursor_position):
                self.__selected_control_point = point
                self.__selected_control_point[0].setBrush(QBrush(QColor("red")))
                return

        # Check if a polygon is selected
        self.remove_control_points()
        if self.__scene.selectedItems():
            self.__current_polygon = self.__scene.selectedItems()[0]
            print(f"items selected:", self.__current_polygon)
            self.show_control_points()
        else:
            # elsewhere
            self.__current_polygon = None



    def mouseMoveEvent(self, event) -> None:
        if not self.__is_editing_tracker:
            return self.__parent.mouseMoveEvent(event)

        super(Widget_graphics_view, self).mouseMoveEvent(event)
        cursor_position = self.mapToScene(event.position().toPoint())
        if cursor_position.x() < 0:
            cursor_position.setX(0)
        if cursor_position.y() < 0:
            cursor_position.setY(0)
        if cursor_position.x() > self.size().width():
            cursor_position.setX(self.size().width())
        if cursor_position.y() > self.size().height():
            cursor_position.setY(self.size().height())
        # print("move:", cursor_position)

        if self.__selected_control_point:
            self.__current_polygon_points[self.__selected_control_point[1]] = QPointF(cursor_position)
            self.__current_polygon.setPolygon(self.__current_polygon_points)
            self.__is_modifying = True


    def mouseReleaseEvent(self, event) -> None:
        if not self.__is_editing_tracker:
            return self.__parent.mouseMoveEvent(event)
        super(Widget_graphics_view, self).mouseReleaseEvent(event)

        if self.__is_modifying:
            self.event_region_modified()
            self.__is_modifying = False


    def draw_polygon(self):  # adds the polygon to the scene
        # print("draw polygon")
        self.__is_drawing_polygon = False

        if len(self.new_polygon_points) > 2:
            polygon = QPolygonCustom(self.new_polygon_points)
            polygon.setPen(QPen(Qt.red, 1, Qt.SolidLine))
            polygon.setFlags(QGraphicsItem.ItemIsSelectable)
            self.__scene.addItem(polygon)
            self.__current_polygon = polygon

        self.new_polygon_points = []



    def event_key_pressed(self, event:QKeyEvent) -> bool:
        key = event.key()
        modifiers = event.modifiers()
        print_green(f"widget_geometry: event_key_pressed: {key}")

        if not self.__is_editing_tracker:
            return False

        print("key_pressed")
        key = event.key()
        if key in [Qt.Key.Key_Enter, Qt.Key.Key_Return]:
            self.draw_polygon()
            self.event_region_modified()
            self.__is_modifying = False
            return True

        elif key == Qt.Key.Key_T:
            print("create a new polygon")
            self.record()
            return True

        elif key == Qt.Key.Key_Delete:
            print("remove a selected polygon/corner")
            self.remove_selected_item()
            return True

        if key == Qt.Key.Key_Control:
            self.control_key_pressed = True
            return True
        else:
            self.control_key_pressed = False

        return False


    def event_key_released(self, event:QKeyEvent) -> bool:
        key = event.key()
        modifiers = event.modifiers()
        if not self.__is_editing_tracker:
            return self.__parent.keyReleaseEvent(event)

        print("released")
        self.control_key_pressed = False



    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        verbose = False
        if event.type() == QEvent.Type.KeyPress:
            if verbose:
                print_lightcyan(f"eventFilter: widget_{self.objectName()}: keypress {event.key()}")
            if self.event_key_pressed(event):
                if verbose:
                    print(f"\taccepted")
                event.accept()
                return True
            else:
                print(f"\tsend to parent")
                return self.__parent.event_key_pressed(event)


        elif event.type() == QEvent.Type.KeyRelease:
            if verbose:
                print_lightcyan(f"eventFilter: widget_{self.objectName()}: keyrelease {event.key()}")
            if self.event_key_released(event):
                if verbose:
                    print(f"\taccepted")
                event.accept()
                return True
            else:
                if verbose:
                    print(f"\tsend to parent")
                return self.__parent.event_key_released(event)


        return super().eventFilter(watched, event)