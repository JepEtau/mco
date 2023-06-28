import collections
import configparser
from copy import deepcopy
import os
import gc
from pathlib import Path, PosixPath
import cv2
import numpy as np
import os.path
from PySide6.QtCore import (
    QObject,
    Signal,
)
from functools import partial
from datetime import datetime
from pprint import pprint

from curve import Curve


class Hist(QObject):
    signal_ready_to_play = Signal(dict)
    signal_reload_frame = Signal()
    signal_is_modified = Signal(dict)
    signal_cache_is_ready = Signal()
    signal_histogram_modified = Signal(dict)
    signal_refresh_image = Signal()
    signal_close = Signal()
    signal_image_refreshed = Signal(cv2.Mat)
    signal_histogram_refreshed = Signal(dict)
    signal_stitching_curves_selected = Signal(dict)

    def __init__(self):
        super(Hist, self).__init__()

        self.view = None

        self.ref_image = None
        self.image = None
        self.current_channel = 'r'
        self.rgb_lut = None


        self.db_hist_curves_initial = dict()
        self.db_hist_curves = parse_stitching_curves_database()


        self.k_curves = 's000'
        self.current_curves = self.get_stitching_curves(self.k_curves)
        pprint(self.current_curves)

    def set_view(self, view):
        self.view = view

        self.view.signal_urls_dropped[dict].connect(self.event_urls_dropped)

        self.view.signal_curves_modified[dict].connect(self.event_stitching_curves_modified)
        self.view.signal_channel_selected[str].connect(self.event_channel_selected)
        # self.view.widget_stitching_curves.signal_save_curves_as[dict].connect(self.event_save_stitching_curves_as)
        # self.view.widget_stitching_curves.signal_discard.connect(self.event_discard_stitching_curves_modifications)

        # self.view.widget_stitching_curves.signal_remove_selection.connect(self.event_remove_stitching_curves_selection)
        # self.view.widget_stitching_curves.signal_selection_changed[str].connect(self.event_stitching_curves_selected)
        # self.view.widget_stitching_curves.signal_reset_selection.connect(self.event_reset_stitching_curves_selection)
        # self.view.widget_stitching_curves.signal_save_selection.connect(partial(self.event_save_modifications, 'stitching_curves'))


        # self.view.signal_preview_options_changed[dict].connect(self.event_preview_options_changed)

        # Force refresh of previe options
        # self.view.event_preview_options_changed()



    def event_urls_dropped(self, dropped_urls:dict):
        print(f"event_urls_dropped")
        pprint(dropped_urls)
        filepaths = dropped_urls['filepaths']
        self.load_images(filepaths)



    def load_images(self, filepaths:list):
        pprint(filepaths)
        image_list = list()
        for filepath in filepaths:
            try:
                image = self.load_image(filepath)
            except:
                continue
            image_list.append(image)

        self.ref_image = image_list[0]['img']
        self.image = image_list[1]['img']

        # Generate the image
        image, histogram = self.generate_image()
        self.signal_image_refreshed.emit(image)
        self.signal_histogram_refreshed.emit(histogram)
        self.signal_stitching_curves_selected.emit(self.current_curves)


    def load_image(self, filepath:str) -> dict:
        if filepath is None or filepath == '':
            return None
        try:
            img = cv2.imread(filepath)
        except:
            return None

        height, width, channel_count = img.shape
        filepath = os.path.abspath(filepath)
        modification_time = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime("%Y-%m-%d %H:%M:%S")
        # assume uint##
        bpp = int(str(img.dtype)[4:]) * channel_count
        image_dict = {
            'properties': {
                'filepath': filepath,
                'folder': os.path.dirname(filepath),
                'filesize': os.path.getsize(filepath),
                'filename': os.path.basename(filepath),
                'width': width,
                'height': height,
                'bpp': bpp,
                'channel_count': channel_count
            },
            'img': img,
        }
        return image_dict


    def event_channel_selected(self, channel:str):
        self.current_channel = channel
        # Generate the image
        image, histogram = self.generate_image()
        self.signal_image_refreshed.emit(image)
        self.signal_histogram_refreshed.emit(histogram)


    def event_stitching_curves_modified(self, curves:dict):
        print("hist: event_stitching_curves_modified")
        self.k_curves = curves['k_curves']
        if self.k_curves != '':
            self.db_hist_curves[self.k_curves] = deepcopy(curves)

        # Generate the image
        image, histogram = self.generate_image()
        self.signal_image_refreshed.emit(image)
        self.signal_histogram_refreshed.emit(histogram)


    def generate_image(self):
        current_channel = self.current_channel
        try:
            lut = self.db_hist_curves[self.k_curves]['lut']
        except:
            lut = self.db_hist_curves_initial[self.k_curves]['lut']

        # Apply RGB curves modifications to get a similar histogram between bgd and fgd
        if lut is not None:
            b, g, r = cv2.split(self.image)

            shape = r.shape
            r = lut['r'][r.flatten()].reshape(shape).astype(np.uint8)

            shape = g.shape
            g = lut['g'][g.flatten()].reshape(shape).astype(np.uint8)

            shape = b.shape
            b = lut['b'][b.flatten()].reshape(shape).astype(np.uint8)

            modified_img = cv2.merge((b, g, r))
        else:
            modified_img = self.image


        # Calculate histogram for the current channel only (optimization)
        histogram = None
        do_calculate_histograms = True
        if do_calculate_histograms:
            if current_channel == 'r':
                hist_target = cv2.calcHist([self.ref_image], [2], None, [256], ranges=[0, 256])
                hist_modified = cv2.calcHist([modified_img], [2], None, [256], ranges=[0, 256])
            elif current_channel == 'g':
                hist_target = cv2.calcHist([self.ref_image], [1], None, [256], ranges=[0, 256])
                hist_modified = cv2.calcHist([modified_img], [1], None, [256], ranges=[0, 256])
            elif current_channel == 'b':
                hist_target = cv2.calcHist([self.ref_image], [0], None, [256], ranges=[0, 256])
                hist_modified = cv2.calcHist([modified_img], [0], None, [256], ranges=[0, 256])

            if current_channel is not None:
                histogram = {
                    current_channel: {
                        'target': hist_target,
                        'modified': hist_modified,
                    }
                }

        ref_h, ref_w, c = self.ref_image.shape
        h, w, _ = modified_img.shape

        inter = 40

        image_height = max(ref_h, h)
        image_width = ref_w + inter + w

        image = np.zeros([image_height, image_width, c], dtype=np.uint8)

        image[0:ref_h,0:ref_w,] = self.ref_image
        image[0:h,ref_w + inter: ref_w + inter + w,] = modified_img

        cv2.imwrite("test.png", image)
        return (image, histogram)













    STITCHING_CURVES_DEFAULT = {
        'k_curves': '',
        'points': dict(),
        'lut': None,
    }


    def get_stitching_curves(self, k_curves):
        if k_curves is not None:
            # Return a dict of k_curves and (Curve, lut) for each channel
            if (k_curves not in self.db_hist_curves_initial.keys()
                and k_curves not in self.db_hist_curves.keys()):
                print("get_stitching_curves: [%s] is not in modified/initial db" % (k_curves))
                return self.STITCHING_CURVES_DEFAULT

            if k_curves in self.db_hist_curves.keys():
                print("get_stitching_curves: %s: modified" % (k_curves))
                curves = self.db_hist_curves[k_curves]

            elif k_curves in self.db_hist_curves_initial.keys():
                print("get_stitching_curves: %s: initial" % (k_curves))
                curves = self.db_hist_curves_initial[k_curves]
        else:
            return self.STITCHING_CURVES_DEFAULT

        if curves['lut'] is None:
            # Calculate lut from channels
            curves['lut'] = dict()
            for k_c in ['r', 'g', 'b']:
                curve = Curve()
                curve.remove_all_points()
                for p in curves['points'][k_c]:
                    curve.add_point(p[0], p[1])
                curves['lut'][k_c] = calculate_hist_lut(curve=curve)
        return curves













def calculate_hist_lut(curve:Curve):
    depth = 256.0
    lut_tmp = curve.calculate(sample_count=256, depth=depth, verbose=False)
    lut_tmp = (lut_tmp - depth/2) / 10
    tmp = np.arange(start=0, stop=256, step=1, dtype=np.float32)
    tmp32 = np.add(tmp, lut_tmp)

    return np.clip(tmp32, 0, 255).astype(np.uint8)




STITCHING_CURVES_DEFAULT = {
    'k_curves': '',
    'points': dict(),
    'lut': None,
}

def parse_stitching_curves_database(db=None, k_ep:str=''):

    # Open configuration file
    # filepath = os.path.join(db['common']['directories']['curves'], "stitching", "%s_stitching_curves.ini" % (k_ep))
    filepath = "hist_curve.ini"
    if filepath.startswith("~/"):
        filepath = os.path.join(PosixPath(Path.home()), filepath[2:])
    if not os.path.exists(filepath):
        print("warning: %s:parse_stitching_curves: %s, %s is missing" % (__name__, k_ep, filepath))
        return

    # Initialize local database
    db_hist_curves = dict()

    # Parse the file
    config = configparser.ConfigParser()
    config.read(filepath)
    for k_curves in config.sections():
        db_hist_curves[k_curves] = deepcopy(STITCHING_CURVES_DEFAULT)
        db_hist_curves[k_curves]['k_curves'] = k_curves
        for k_channel in ['r', 'g', 'b']:
            points_str = config.get(k_curves, k_channel).replace(' ', '').strip()
            db_hist_curves[k_curves]['points'][k_channel] = list()
            for point_str in points_str.split(','):
                xy = np.fromstring(point_str, dtype=np.float32, count=2, sep=':')
                db_hist_curves[k_curves]['points'][k_channel].append([xy[0], xy[1]])

        # print("curve name: %s" % (k_curves))
        # for c in ['r', 'g', 'b']:
        #     print("\t%s" % (c))
        #     points = db_hist_curves[k_curves]['points'][c]
        #     for p in points:
        #         print("\t ", p)

    return db_hist_curves



def write_stitching_curves_to_database(db, k_ep:str, curves:dict):
    # Open configuration file
    filepath = os.path.join(db['common']['directories']['curves'], "stitching", "%s_stitching_curves.ini" % (k_ep))
    if filepath.startswith("~/"):
        filepath = os.path.join(PosixPath(Path.home()), filepath[2:])

    if os.path.exists(filepath):
        config_stitching_curves_db = configparser.ConfigParser(dict_type=collections.OrderedDict)
        config_stitching_curves_db.read(filepath)
    else:
        config_stitching_curves_db = configparser.ConfigParser({}, collections.OrderedDict)

    k_curves = curves['k_curves']

    # Update the config file
    k_section = k_curves

    # Create a section if it does not exist
    if not config_stitching_curves_db.has_section(k_section):
        config_stitching_curves_db[k_section] = dict()

    # Modify/Add the points to this section
    for c in ['r', 'g', 'b']:
        for c in ['r', 'g', 'b']:
            points = curves['points'][c]
            matrix_str = ""
            for p_xy in points:
                matrix_str += "%s:%s, " % (
                    np.format_float_positional(p_xy.x()),
                    np.format_float_positional(p_xy.y()))
            config_stitching_curves_db.set(k_curves, c, matrix_str[:-2])

    # Sort the section
    config_stitching_curves_db[k_section] = collections.OrderedDict(sorted(config_stitching_curves_db[k_section].items(), key=lambda x: x[0]))

    # Write to the database
    with open(filepath, 'w') as config_file:
        config_stitching_curves_db.write(config_file)

    return True
