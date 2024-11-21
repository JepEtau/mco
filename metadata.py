from argparse import ArgumentParser, Namespace
from concurrent.futures import ThreadPoolExecutor
import os
from pprint import pprint
import shutil
import signal
import sys
import time
import numpy as np
import cv2
from matplotlib import pyplot as plt
import multiprocessing as mp
from utils.images_io import write_image, load_image_fp32, img_info
from utils.media import extract_media_info_mco
from utils.path_utils import absolute_path
from processing.brightness_contrast import *


signal.signal(signal.SIGINT, signal.SIG_DFL)
in_media_path = "/home/adg/mco/cache/ep01/scenes_sim/ep01_episode_001__j_bcfb0b7_sim.mxf"
in_media_info = extract_media_info_mco(in_media_path)

pprint(in_media_info)


