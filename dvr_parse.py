from dataclasses import dataclass
from pprint import pprint
import random
import signal
import sys
from argparse import ArgumentParser
import logging
from pprint import pprint
import signal
import sys
import time
from dvr.dvr import DVR, app_already_started, Pages
from dvr.timeline import DVRTimeline
from dvr.timeline_item import DVRItem
from parsers import (
    parse_database,
)
from utils.arg_parser import common_argument_parser
from utils.logger import main_logger
from utils.p_print import *


dvr = None

def main():
    # Arguments
    parser: ArgumentParser = common_argument_parser(
        description="Generate episode (final)",
        add_language=True,
    )

    parser.add_argument(
        "--project",
        "-p",
        type=str,
        default="ep01_python",
        required=False,
        help="project name"
    )

    arguments = parser.parse_args()

    if arguments.debug:
        main_logger.addHandler(logging.StreamHandler(sys.stdout))
        main_logger.setLevel("DEBUG")

    episode: int = arguments.episode
    project_name = arguments.project
    db_name = "mco"

    global dvr
    dvr = DVR()
    # Open database/project
    print(lightcyan(f"DaVinci Resolve version:"), dvr.version())
    dvr.set_current_database(name=db_name)
    print(lightcyan(f"Database:"), dvr.current_database_name())
    project = dvr.load_project(project_name)
    print(lightcyan(f"Project loaded:"), project.name)

    pprint(project.get_settings())

    timeline: DVRTimeline = project.get_timeline()
    print(lightcyan(f"Timeline:"), timeline.name)
    timeline.set_as_current()
    pprint(timeline.get_settings())

    dvr.select_page(name="edit")
    if False:
        print(lightcyan(f"Input media clips:"))
        item: DVRItem
        count = timeline.video_item_count()
        random.seed(time.time())
        for no in range(1, 5):
            dvr_index = random.randint(1, count)
            item: DVRItem = timeline.select_item(dvr_index)
            pprint(item.get_properties())
            item.cropping.crop = (0, 0, 0, 0)
            print(f"item no. {dvr_index}:\n  {item.media_clip.filename}, start frame {item.start_frame}\n")

    dvr.select_page("deliver")
    print(project.get_render_mode())


    print("done")
    if not app_already_started():
        print(yellow("TODO: close it"))
        dvr.quit()




def signal_handler(signum, frame):
    # Close if it has been started from this script
    if not app_already_started():
        print(yellow("TODO: close it"))
        dvr.quit()


if __name__ == "__main__":
    # signal.signal(signal.SIGINT, signal.SIG_DFL)
    signal.signal(signal.SIGINT, signal_handler)
    main()
