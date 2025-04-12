from dataclasses import dataclass
import os
from pprint import pprint
import signal
import subprocess
import sys
from argparse import ArgumentParser
import logging
from pprint import pprint
import signal
import sys
import time
from typing import Any, Literal
from warnings import warn
from parsers import (
    parse_database,
)
from utils.arg_parser import common_argument_parser
from utils.logger import main_logger
from utils.p_print import *

# RESOLVE_SCRIPT_API = os.path.join(
#     os.environ["PROGRAMDATA"],
#     "Blackmagic Design", "DaVinci Resolve", "Support", "Developer", "Scripting"
# )
# RESOLVE_SCRIPT_LIB="C:\\Program Files\\Blackmagic Design\\DaVinci Resolve\\fusionscript.dll"
# # RESOLVE_PYTHON_PATH = os.path.join(RESOLVE_SCRIPT_API, "Modules")
# # # PYTHONPATH="%PYTHONPATH%;%RESOLVE_SCRIPT_API%\Modules\"


# os.environ["RESOLVE_SCRIPT_API"] = RESOLVE_SCRIPT_API
# os.environ["RESOLVE_SCRIPT_LIB"] = RESOLVE_SCRIPT_LIB
# if "PYTHONPATH" in os.environ:
#     os.environ["PYTHONPATH"] = ";".join((os.environ["PYTHONPATH"], RESOLVE_PYTHON_PATH))
# else:
#     os.environ["PYTHONPATH"] = RESOLVE_PYTHON_PATH

# print(os.environ["RESOLVE_SCRIPT_API"])
# print(os.environ["RESOLVE_SCRIPT_LIB"])
# print(os.environ["PYTHONPATH"])

# print(os.environ.keys())
# for k in os.environ:
#     print(f"{k}: {os.environ[k]}")
# RESOLVE_SCRIPT_API="%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting"
# RESOLVE_SCRIPT_LIB="C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll"
# PYTHONPATH="%PYTHONPATH%;%RESOLVE_SCRIPT_API%\Modules\"
dvr_python = "C:\\ProgramData\\Blackmagic Design\\DaVinci Resolve\\Support\\Developer\\Scripting\\Modules"
RESOLVE_EXE_PATH = r"C:\Program Files\Blackmagic Design\DaVinci Resolve\Resolve.exe"
sys.path.append(dvr_python)

import DaVinciResolveScript as dvr


DbType = Literal['Disk', 'PostgreSQL']
TrackType = Literal['video', 'audio', 'subtitle']

ClipProperty = Literal[
    "File Path",
    "Resolution",
    "Frame Rate",
    "Codec",
    "Bit Depth",
    "Clip Name",
    "Duration",
    "Media Type",
    "Start TC",
    "End TC",
    "Reel",
    "Scene",
    "Shot",
    "Take",
    "Camera Type",
    "Audio Channels",
    "Sample Rate",
]

already_started: bool = True


@dataclass
class DVRMediaPoolCip:
    name: str
    media_id: str
    filepath: str
    filename: str



class DVRItem:
    def __init__(self, item: Any):
        super().__init__()
        self.name: str = item.GetName()
        self.start_frame: int = item.GetStart()
        self.end_frame: int = item.GetEnd()
        self.frame_count: int = item.GetDuration()
        self.media_clip: DVRMediaPoolCip = None

        media_pool_item = None
        try:
            media_pool_item = item.GetMediaPoolItem()
        except:
            warn(f"Failed to get MediaPoolItem for item `{self.name}`")

        if media_pool_item is not None:
            # pprint(media_pool_item.GetClipProperty())
            self.media_clip: DVRMediaPoolCip = DVRMediaPoolCip(
                name=media_pool_item.GetName(),
                media_id=media_pool_item.GetMediaId(),
                filepath=media_pool_item.GetClipProperty('File Path'),
                filename=media_pool_item.GetClipProperty('Filename'),
                # metadata=get_metadata_dictionary(media_pool_item),
            )

    def __str__(self):
        item_str: str = f"""{self.__class__.__name__}(
            name={self.name},
            start_frame={self.start_frame},
            end_frame={self.end_frame},
            frame_count={self.end_frame},
            media_clip={self.media_clip},\n)
        """
        return item_str.replace ("            ", "  ")


class DVRTimeline:
    def __init__(self, timeline):
        self._timeline = timeline

    def name(self) -> str:
        return self._timeline.GetName()

    def set_name(self, name: str) -> str:
        self._timeline.SetName(name)

    def _track_count(self, type: TrackType = 'video') -> int:
        return self._timeline.GetTrackCount(type)

    def _track_name(self, type: TrackType = 'video', index: int = 1) -> str:
        try:
            return self._timeline.GetTrackName(type, index)
        except:
            raise ValueError(f"Failed getting track name for index={index}")

    def video_track_count(self) -> int:
        return self._track_count(type='video')

    def video_track_name(self, index: int = 1) -> str:
        return self._track_name(type='video', index=index)

    def video_track_items(self, index: int = 1) -> list[DVRItem]:
        items: list[DVRItem] = []
        for item in self._timeline.GetItemListInTrack("video", index):
            items.append(DVRItem(item))
        return items

    def audio_track_count(self) -> int:
        return self._track_count(type='audio')

    def audio_track_name(self, index: int = 1) -> str:
        return self._track_name(type='audio', index=index)

    def audio_track_items(self, index: int = 1) -> list[Any]:
        raise NotImplementedError("To be reworked to work like video items")
        return self._timeline.GetItemListInTrack("audio", index)



class DVRProject:
    def __init__(self, project: Any):
        self.project = project

    def name(self) -> str:
        try:
            return self.project.GetName()
        except Exception as e:
            raise ValueError(f"Erroneous project")

    def timeline_count(self) -> int:
        return self.project.GetTimelineCount()

    def timeline_by_index(self, index: int = 1) -> DVRTimeline:
        return DVRTimeline(self.project.GetTimelineByIndex(index))

    def framerate(self) -> float:
        return self.project.GetSetting("timelineFrameRate")

    def resolution(self) -> tuple[int, int]:
        return (
            self.project.GetSetting("timelineResolutionWidth"),
            self.project.GetSetting("timelineResolutionHeight")
        )



class DVR:
    def __init__(self):
        global already_started
        self._resolve = dvr.scriptapp("Resolve")
        if self._resolve is None:
            # raise SystemError(red("resolve is None"))
            subprocess.Popen(args=[f"\"{RESOLVE_EXE_PATH}\"", "-nogui"])
            time.sleep()
            self._resolve = dvr.scriptapp("Resolve")


        try:
            self._version = self._resolve.GetVersionString()
        except Exception as e:
            warn(yellow("DaVinci Resolve is not opened, try opening it"))
            already_started = False
            subprocess.Popen(args=[f"\"{RESOLVE_EXE_PATH}\"", "-nogui"])
            try:
                self._version = self._resolve.GetVersionString()
            except:
                raise SystemError(red("Failed to start DaVinci Resolve"))

        self.pm = self._resolve.GetProjectManager()
        self._project = None


    def quit(self):
        self._resolve.Quit()


    def version(self) -> str:
        return self._version


    def database_names(self) -> list[str]:
        database_list = self.pm.GetDatabaseList()
        return list([db['DbName'] for db in database_list])


    def current_database(self) -> dict[str, str]:
        return self.pm.GetCurrentDatabase()


    def current_database_name(self) -> str:
        return self.pm.GetCurrentDatabase()['DbName']


    def set_current_database(self, name: str, type: DbType = 'Disk', ip_address: str = "") -> None:
        current_db = {
            'DbType': type,
            'DbName': name,
        }
        if ip_address:
            current_db['IpAddress'] = ip_address
        try:
            self.pm.SetCurrentDatabase(current_db)
        except:
            raise ValueError(f"Failed to set current database to {name}")


    def load_project(self, name: str) -> DVRProject:
        try:
            self._project: DVRProject = DVRProject(self.pm.LoadProject(name))
        except Exception as e:
            raise ValueError(f"Failed to load project: {type(e)}")
        return self._project


    def project(self) -> DVRProject:
        if self._project is None:
            raise ValueError(f"No project loaded")
        return self._project







def get_metadata_dictionary(media_pool_item):
    """
    Try to get all available metadata from a media pool item.

    Args:
        media_pool_item: MediaPoolItem object

    Returns:
        dict: Dictionary of metadata key-value pairs
    """
    if not media_pool_item:
        return {}

    # Common metadata fields to try
    metadata_fields = [
        "File Path", "Resolution", "Frame Rate", "Codec", "Bit Depth",
        "Duration", "Media Type", "Start TC", "End TC", "Reel", "Scene",
        "Shot", "Take", "Camera Type", "Audio Channels", "Sample Rate"
    ]

    metadata = {}
    print(f"Trying to get metadata for: {media_pool_item.GetName()}")

    # Try each metadata field
    for field in metadata_fields:
        try:
            value = media_pool_item.GetMetadata(field)
            if value:
                metadata[field] = value
                print(f"  ✓ {field}: {value}")
            else:
                print(f"  ✗ {field}: No value")
        except Exception as e:
            print(f"  ! Error getting '{field}': {str(e)}")

    return metadata



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

    dvr = DVR()
    print(f"DaVinci Resolve version: {dvr.version()}")
    print(f"Available databases: {dvr.database_names()}")
    print(f"current database: {dvr.current_database_name()}")
    dvr.set_current_database(name=db_name)
    print(f"current database: {dvr.current_database_name()}")

    print(f"Try loading project: {project_name}")
    project = dvr.load_project(project_name)
    print(f"Project loaded: {project.name()}")
    # project = project_manager.GetCurrentProject()
    # # Get a list of all projects

    if False:
        # Get a simple list of media pool items and their metadata
        media_pool = project.GetMediaPool()
        root_folder = media_pool.GetRootFolder()
        clips = root_folder.GetClipList()

        print("Media Pool Items:")
        for clip in clips[:5]:  # Just test the first 5
            print(f"Clip: {clip.GetName()}")
            try:
                path = clip.GetMetadata("File Path")
                print(f"  File Path: {path}")
                print(f"  id: {clip.GetMediaId()}")

            except Exception as e:
                print(f"  Error: {e}")

    if True:
        # timeline = project.GetCurrentTimeline()
        timeline: DVRTimeline = project.timeline_by_index()
        # timeline.SetName("ep01_episode")
        print(f"got timeline: {timeline.name()}")
        # if not timeline.SetTrackName("video", 1, "episode"):
        #     print("failed naming track name")
        print(f"    video track count: {timeline.video_track_count()}")
        print(f"    video track name: {timeline.video_track_name()}")

        # media_pool = project.GetMediaPool()
        # root_folder = media_pool.GetRootFolder()
        # clip_list = root_folder.GetClipList()
        # first_clip_name = clip_list[0].GetName()
        # print(clip_list[0].GetMetadata("Codec"))
        track_items = timeline.video_track_items()
        for item in track_items[:5]:
            print(item)

    print("done")
    if not already_started:
        print(yellow("TODO: close it"))
        dvr.quit()




def signal_handler(signum, frame):
    # Close if it has been started from this script
    if not already_started:
        print(yellow("TODO: close it"))
        dvr.quit()


if __name__ == "__main__":
    # signal.signal(signal.SIGINT, signal.SIG_DFL)
    signal.signal(signal.SIGINT, signal_handler)
    main()
