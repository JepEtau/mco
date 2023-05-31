# -*- coding: utf-8 -*-
import sys
sys.path.append('scripts')

import numpy as np
import cv2
from pprint import pprint
from logger import log
from utils.pretty_print import *

from PySide6.QtCore import (
    QPoint,
    QSize,
    Qt,
    Signal,
    QEvent,
    QObject,
)
from PySide6.QtGui import (
    QColor,
    QImage,
    QPen,
    QPainter,
    QKeyEvent,
    QPaintEvent,
    QWheelEvent,
)
from PySide6.QtWidgets import (
    QWidget,
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


class Widget_painter(QWidget):

    def __init__(self, parent, ui):
        super(Widget_painter, self).__init__()
        self.setObjectName("widget_painter")

        # self.setMouseTracking(True)
        self.image = None
        self.is_repainting = False
        self.__parent = ui


    def show_image(self, image):
        self.image = image
        self.repaint()

    def repaint_frame(self):
        self.repaint()



    def paintEvent(self, event:QPaintEvent):
        if self.image is None:
            log.info("no image loaded")
            return

        img = self.image['cache']
        if img is None:
            return
        if self.image['cache_initial'] is None:
            return

        if self.is_repainting:
            log.error("error: self.is_repainting is True!!")
            return
        self.is_repainting = True
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



        self.image['origin'] = [PAINTER_MARGIN_LEFT, PAINTER_MARGIN_TOP - delta_y]
        # print_lightgreen(f"paintEvent: begin, delta: {delta_y}")
        # print(shot_geometry)
        painter = QPainter()
        if painter.begin(self):

            if preview['geometry']['final_preview']:
                # print("paintEvent: display final_preview")
                painter.drawImage(
                    QPoint(PAINTER_MARGIN_LEFT, PAINTER_MARGIN_TOP - delta_y), q_image)
            else:
                preview_shot_geometry = preview['geometry']['shot']

                if preview_shot_geometry['crop_edition'] and not preview_shot_geometry['crop_preview']:
                    # Add a red rectangle to the image

                    if preview_shot_geometry['resize_preview']:
                        # Resize the image (i.e. draw rect on the resized image)
                        x0 = PAINTER_MARGIN_LEFT
                        y0 = PAINTER_MARGIN_TOP - delta_y

                        # Patch the crop value if displaying deshaked shot
                        # crop = shot_geometry['crop']
                        # if not preview['geometry']['add_borders']:
                        #     crop = list(map(lambda x: x + IMG_BORDER_HIGH_RES, shot_geometry['crop']))

                        # # Image is resized, add the recalculated crop
                        # crop_top, crop_bottom, crop_left, crop_right, cropped_width, cropped_height = get_dimensions_from_crop_values(
                        #     width=initial_img_width, height=initial_img_height, crop=crop)
                        # w_tmp = int((cropped_width * FINAL_FRAME_HEIGHT) / float(cropped_height))
                        pprint(self.image['geometry_values'])
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

                        painter.drawImage(
                            QPoint(x0 + pad_left - crop_left, y0 - crop_top),
                            q_image)

                        # Add the cropped resized rect
                        pen = QPen(COLOR_CROP_RECT)
                        pen.setWidth(PEN_CROP_SIZE)
                        pen.setStyle(Qt.SolidLine)
                        painter.setPen(pen)
                        painter.drawRect(
                            PAINTER_MARGIN_LEFT + pad_left - 1,
                            PAINTER_MARGIN_LEFT - delta_y - 1,
                            w_tmp + 1,
                            FINAL_FRAME_HEIGHT + 1)

                        # Add the final 1080p rect
                        pen = QPen(COLOR_DISPLAY_RECT)
                        pen.setWidth(PEN_CROP_SIZE)
                        pen.setStyle(Qt.SolidLine)
                        painter.setPen(pen)
                        painter.drawRect(
                            PAINTER_MARGIN_LEFT - 1,
                            PAINTER_MARGIN_LEFT - delta_y - 1,
                            FINAL_FRAME_WIDTH + 1,
                            FINAL_FRAME_HEIGHT + 1)

                    else:
                    # print("paintEvent: draw rect crop on the original image")
                        # Original
                        x0 = PAINTER_MARGIN_LEFT
                        y0 = PAINTER_MARGIN_TOP - delta_y
                        crop = shot_geometry['crop']
                        if not preview['geometry']['add_borders']:
                            crop = list(map(lambda x: x + IMG_BORDER_HIGH_RES, shot_geometry['crop']))
                        painter.drawImage(QPoint(x0, y0), q_image)

                        # Add a red rect for the crop
                        crop_top, crop_bottom, crop_left, crop_right, cropped_width, cropped_height = get_dimensions_from_crop_values(
                            width=initial_img_width, height=initial_img_height, crop=crop)

                        # print(f"({crop_left}, {crop_top}) -> ({cropped_width},{cropped_height})")

                        pen = QPen(COLOR_CROP_RECT)
                        pen.setWidth(PEN_CROP_SIZE)
                        pen.setStyle(Qt.SolidLine)
                        painter.setPen(pen)
                        # https://doc.qt.io/qt-6/qrect.html, PEN_CROP_SIZE = 1
                        # print("\timg: %dx%d" % (img.data.shape[1], img.data.shape[0]))
                        # print("\trect: (%d;%d) w=%d, h=%d" % (c_l - 1, c_t - delta_y - 1, c_w + 1, c_h + 1))

                        painter.drawRect(
                            PAINTER_MARGIN_LEFT + crop_left - 1,
                            PAINTER_MARGIN_LEFT + crop_top - delta_y - 1,
                            cropped_width + 1,
                            cropped_height + 1)

                elif preview_shot_geometry['crop_preview']:
                    # Image is cropped

                    if preview_shot_geometry['resize_preview']:
                        # Image is also resized

                        # if not preview['geometry']['add_borders']:
                        #     crop_top, crop_bottom, crop_left, crop_right, cropped_width, cropped_height = get_dimensions_from_crop_values(
                        #         width=initial_img_width, height=initial_img_height, crop=shot_geometry['crop'])

                        # w_tmp = int((cropped_width * FINAL_FRAME_HEIGHT) / float(cropped_height))
                        # pad_left = int(((FINAL_FRAME_WIDTH - img_width) / 2) + 0.5)
                        pad_left = (self.image['geometry_values']['pad']['left']
                                    + self.image['geometry_values']['pad_error'][2])

                        self.image['origin'] = [
                            PAINTER_MARGIN_LEFT + pad_left,
                            PAINTER_MARGIN_TOP - delta_y]
                        painter.drawImage(
                            QPoint(
                                PAINTER_MARGIN_LEFT + pad_left,
                                PAINTER_MARGIN_TOP - delta_y),
                            q_image)

                        # Add the final 1080p rect
                        pen = QPen(COLOR_DISPLAY_RECT)
                        pen.setWidth(PEN_CROP_SIZE)
                        pen.setStyle(Qt.SolidLine)
                        painter.setPen(pen)
                        painter.drawRect(
                            PAINTER_MARGIN_LEFT - 1,
                            PAINTER_MARGIN_LEFT - delta_y - 1,
                            FINAL_FRAME_WIDTH + 1,
                            FINAL_FRAME_HEIGHT + 1)
                    else:
                        # print("paintEvent: draw cropped image on the original image")
                        # Crop and no rect
                        crop = shot_geometry['crop']
                        if not preview['geometry']['add_borders']:
                            crop = list(map(lambda x: x + IMG_BORDER_HIGH_RES, shot_geometry['crop']))
                        crop_top, crop_bottom, crop_left, crop_right, cropped_width, cropped_height = get_dimensions_from_crop_values(
                            width=initial_img_width, height=initial_img_height, crop=crop)

                        painter.drawImage(
                            QPoint(PAINTER_MARGIN_LEFT + crop_left,
                                PAINTER_MARGIN_TOP + crop_top - delta_y),
                            q_image)

                else:
                    # original
                    # print("paintEvent: draw original image")

                    if preview['geometry']['add_borders']:
                        painter.drawImage(
                            QPoint(PAINTER_MARGIN_LEFT+IMG_BORDER_HIGH_RES, PAINTER_MARGIN_TOP+IMG_BORDER_HIGH_RES - delta_y),
                            q_image.scaled(q_image.width()*2, q_image.height()*2, aspectMode=Qt.KeepAspectRatio))

                    else:
                        painter.drawImage(
                            QPoint(PAINTER_MARGIN_LEFT, PAINTER_MARGIN_TOP - delta_y), q_image)

                if (preview['geometry']['target']['width_edition']
                    and preview_shot_geometry['crop_edition']
                    and preview_shot_geometry['resize_preview']):

                    # Add the target rect
                    pad_left = ((FINAL_FRAME_WIDTH - geometry['target']['w']) / 2) + 0.5
                    pen = QPen(COLOR_PART_CROP_RECT)
                    pen.setWidth(PEN_CROP_SIZE)
                    pen.setStyle(Qt.SolidLine)
                    painter.setPen(pen)
                    painter.drawRect(
                        PAINTER_MARGIN_LEFT + pad_left - 1,
                        PAINTER_MARGIN_LEFT - delta_y - 1,
                        geometry['target']['w'] + 1,
                        FINAL_FRAME_HEIGHT + 1)

                    # Add the final 1080p rect
                    pen = QPen(COLOR_DISPLAY_RECT)
                    pen.setWidth(PEN_CROP_SIZE)
                    pen.setStyle(Qt.SolidLine)
                    painter.setPen(pen)
                    painter.drawRect(
                        PAINTER_MARGIN_LEFT - 1,
                        PAINTER_MARGIN_LEFT - delta_y - 1,
                        FINAL_FRAME_WIDTH + 1,
                        FINAL_FRAME_HEIGHT + 1)



            if preview['curves']['split']:
                try: crop_top = 0 if preview_shot_geometry['resize_preview'] else (-1*crop_top)
                except:  crop_top = 0
                pen = QPen(QColor(255,255,255))
                pen.setStyle(Qt.DashLine)
                painter.setPen(pen)
                painter.drawLine(
                    preview['curves']['split_x'] + PAINTER_MARGIN_LEFT, PAINTER_MARGIN_TOP - crop_top,
                    preview['curves']['split_x'] + PAINTER_MARGIN_LEFT, PAINTER_MARGIN_TOP - crop_top + max(img_height, FINAL_FRAME_HEIGHT))

            guidelines = self.__parent.widget_stabilize.guidelines
            if guidelines.is_enabled():
                x, y = guidelines.coordinates()

                pen = QPen(QColor(255,255,255))
                pen.setStyle(Qt.SolidLine)
                painter.setPen(pen)
                painter.drawLine(
                    x, 10,
                    x, 10 + max(img_height, FINAL_FRAME_HEIGHT + PAINTER_MARGIN_TOP + IMG_BORDER_HIGH_RES))

                painter.drawLine(
                    10, y,
                    10 + max(img_width, FINAL_FRAME_WIDTH + PAINTER_MARGIN_LEFT + IMG_BORDER_HIGH_RES), y)


            painter.end()
        self.is_repainting = False

