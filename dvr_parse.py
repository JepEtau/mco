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
    start_frame: int
    end_frame: int
    frame_count: int = 0

    def __post_init__(self):
        self.frame_count = self.end_frame - self.start_frame + 1


class DVRItem:
    def __init__(
        self,
        timeline_item: Any,
        timeline: Any,
        project: Any
        # timeline_index: int,
    ):
        super().__init__()
        self._timeline_item = timeline_item
        self._timeline = timeline
        self._project = project
        # self._timeline_index = timeline_index

        self.name: str = timeline_item.GetName()
        self.start_frame: int = timeline_item.GetStart()
        self.end_frame: int = timeline_item.GetEnd()
        self.frame_count: int = timeline_item.GetDuration()
        self.media_clip: DVRMediaPoolCip = None

        media_pool_item = None
        try:
            media_pool_item = timeline_item.GetMediaPoolItem()
        except:
            warn(f"Failed to get MediaPoolItem for item `{self.name}`")

        if media_pool_item is not None:
            # pprint(media_pool_item.GetClipProperty())
            self.media_clip: DVRMediaPoolCip = DVRMediaPoolCip(
                name=media_pool_item.GetName(),
                media_id=media_pool_item.GetMediaId(),
                filepath=media_pool_item.GetClipProperty('File Path'),
                filename=media_pool_item.GetClipProperty('Filename'),
                start_frame=timeline_item.GetSourceStartFrame(),
                end_frame=timeline_item.GetSourceEndFrame(),
                # metadata=get_metadata_dictionary(media_pool_item),
            )
        self.media_pool_item = media_pool_item


    def __str__(self):
        item_str: str = f"""{self.__class__.__name__}(
            name={self.name},
            start_frame={self.start_frame},
            end_frame={self.end_frame},
            frame_count={self.end_frame},
            media_clip={self.media_clip},\n)
        """
        return item_str.replace ("            ", "  ")


    # Function to reapply stabilization without changing the settings
    def stabilize(self):
        # First, clear any current selection
        print(lightcyan(f"stabilize: {self.name}"))
        # print(self._timeline.SetCurrentTimecode(self.media_clip.start_frame+1))
        # Get the current stabilization settings
        # fusion_comp = self._item.GetFusionCompByIndex(1)
        # clip_item = selected_items[list(selected_items.keys())[0]]
        # clip_properties = self.media_pool_item.GetProperty()
        print("inspector")
        inspector_properties = self._timeline_item.GetProperty("Inspector")
        pprint(inspector_properties)

        print("GetFusionCompCount")
        print(self._timeline_item.GetFusionCompCount())
        print("GetProperty")
        pprint(self._timeline_item.GetProperty())

        # result = self._timeline_item.Stabilize()
        # print(result)



        # stabilization = self._item.GetStabilization()

        # # Store the current settings to reapply later
        # mode = stabilization.GetMode()
        # zoom = stabilization.GetZoom()
        # cropping_ratio = stabilization.GetCroppingRatio()
        # smoothness = stabilization.GetSmoothing()

        # print(f"clip: {self.name}")
        # print(f"  mode: {mode}")
        # print(f"  zoom: {zoom}")
        # print(f"  cropping ratio: {cropping_ratio}")
        # print(f"  smoothness: {smoothness}")

        # # Clear the current stabilization settings
        # stabilization.Clear()
        # print(f"Cleared stabilization for {clip.GetName()}")

        # # Reapply the original stabilization settings
        # stabilization.SetMode(current_mode)
        # stabilization.SetZoom(current_zoom)
        # stabilization.SetCroppingRatio(current_cropping_ratio)
        # stabilization.SetSmoothing(current_smoothness)

        # Apply the stabilization again (force the reapplication)
        # clip.Stabilize()
        print()

    @property
    def dvr_timeline_item(self):
        return self._timeline_item



class DVRTimeline:
    def __init__(self, timeline, project):
        self._timeline = timeline
        self._project = project

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
            items.append(
                DVRItem(
                    item,
                    timeline=self._timeline,
                    project=self._project
                )
            )
        return items

    def audio_track_count(self) -> int:
        return self._track_count(type='audio')

    def audio_track_name(self, index: int = 1) -> str:
        return self._track_name(type='audio', index=index)

    def audio_track_items(self, index: int = 1) -> list[Any]:
        raise NotImplementedError("To be reworked to work like video items")
        return self._timeline.GetItemListInTrack("audio", index)

    def set_as_current(self):
        self._project.SetCurrentTimeline(self._timeline)

    def set_current_timecode(self, timecode: int) -> None:
        self.set_as_current()
        self._timeline.SetCurrentTimecode(timecode)


    def get_start_timecode(self) -> str:
        self.set_as_current()
        return self._timeline.GetStartTimecode()


    def get_current_item(self) -> DVRItem:
        current_item = self._timeline.GetCurrentVideoItem()
        current_item_start = current_item.GetStart()
        current_item_end = current_item.GetEnd()
        for item in self.video_track_items():
            if (
                item.start_frame == current_item_start
                and item.end_frame == current_item_end
            ):
                return item
        raise ValueError(red("item not found"))



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
        return DVRTimeline(
            self.project.GetTimelineByIndex(index),
            self.project
        )

    def framerate(self) -> float:
        return self.project.GetSetting("timelineFrameRate")

    def resolution(self) -> tuple[int, int]:
        return (
            self.project.GetSetting("timelineResolutionWidth"),
            self.project.GetSetting("timelineResolutionHeight")
        )

    def set_current_timeline(self, index: int = 1):
        timeline = self.project.GetTimelineByIndex(index)
        self.project.SetCurrentTimeline(timeline)



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


    def select_page(self, name: Literal["cut", "edit", "deliver"]) -> None:
        self._resolve.OpenPage(name)



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
    # Open database/project
    print(lightcyan(f"DaVinci Resolve version:"), dvr.version())
    dvr.set_current_database(name=db_name)
    print(lightcyan(f"Database:"), dvr.current_database_name())
    project = dvr.load_project(project_name)
    print(lightcyan(f"Project loaded:"), project.name())

    timeline: DVRTimeline = project.timeline_by_index()
    print(lightcyan(f"Timeline:"), timeline.name())
    timeline.set_as_current()

    track_items = timeline.video_track_items()
    print(lightcyan(f"Input media clips:"))



    dvr.select_page(name="edit")
    # for item in track_items[14:16]:
    # item = track_items[14]
    # # print(item)
    # print(item)
    # item.stabilize()
    print(timeline.get_start_timecode())
    print(timeline.set_current_timecode("01:02:24:00"))
    item: DVRItem = timeline.get_current_item()

    dvr_item = item.dvr_timeline_item
    inspector_properties = dvr_item.GetProperty("Inspector")
    pprint(inspector_properties)

    print("GetFusionCompCount")
    print(dvr_item.GetFusionCompCount())
    print("GetProperty")
    pprint(dvr_item.GetProperty())

    pprint(item.media_clip.filepath)



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
