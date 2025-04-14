from typing import Any
from .render import Render
from .timeline import DVRTimeline


class DVRProject:
    def __init__(self, dvr_project: Any):
        self._dvr_project = dvr_project
        self._render = Render(dvr_project=self._dvr_project)
        self._timelines: dict[str | int, DVRTimeline] = {}


    @property
    def name(self) -> str:
        try:
            return self._dvr_project.GetName()
        except Exception as e:
            raise ValueError(f"Erroneous project")


    @name.setter
    def name(self, name: str) -> None:
        self._dvr_project.SetName(name)


    @property
    def dvr_project(self) -> Any:
        """Return the DaVinciProject object
        """
        return self._dvr_project


    def get_settings(self) -> dict[str, float | int | str]:
        return self._dvr_project.GetSetting()


    def get_setting(self, name: str) -> Any | dict[str, Any]:
        if not name:
            raise ValueError(f"Not a valid setting name: {name}")
        return self._dvr_project.GetSetting(name)


    def set_setting(self, name: str, value: float | int | str) -> bool:
        if not name:
            raise ValueError(f"Not a valid property name: {name}")
        return self._dvr_project.SetSetting(name, value)


    def timeline_count(self) -> int:
        return self._dvr_project.GetTimelineCount()


    def get_timeline(self, index: int = 1) -> DVRTimeline:
        if index not in self._timelines:
            self._timelines[index] = DVRTimeline(
                dvr_project=self._dvr_project, timeline_index=index
            )
        return self._timelines[index]


    def framerate(self) -> float:
        return self._dvr_project.GetSetting("timelineFrameRate")


    def resolution(self) -> tuple[int, int]:
        return (
            self._dvr_project.GetSetting("timelineResolutionWidth"),
            self._dvr_project.GetSetting("timelineResolutionHeight")
        )


    def set_current_timeline(self, index: int = 1) -> bool:
        timeline = self._dvr_project.GetTimelineByIndex(index)
        return self._dvr_project.SetCurrentTimeline(timeline)


    @property
    def render(self) -> Render:
        return self._render


# Project
#   GetMediaPool()                                  --> MediaPool          # Returns the Media Pool object.
#   GetTimelineCount()                              --> int                # Returns the number of timelines currently present in the project.
#   GetTimelineByIndex(idx)                         --> Timeline           # Returns timeline at the given index, 1 <= idx <= project.GetTimelineCount()
#   GetCurrentTimeline()                            --> Timeline           # Returns the currently loaded timeline.
#   SetCurrentTimeline(timeline)                    --> Bool               # Sets given timeline as current timeline for the project. Returns True if successful.
#   GetGallery()                                    --> Gallery            # Returns the Gallery object.
#   GetName()                                       --> string             # Returns project name.
#   SetName(projectName)                            --> Bool               # Sets project name if given projectName (string) is unique.
#   GetSetting(settingName)                         --> string             # Returns value of project setting (indicated by settingName, string). Check the section below for more information.
#   SetSetting(settingName, settingValue)           --> Bool               # Sets the project setting (indicated by settingName, string) to the value (settingValue, string). Check the section below for more information.
#   RefreshLUTList()                                --> Bool               # Refreshes LUT List
#   GetUniqueId()                                   --> string             # Returns a unique ID for the project item
#   InsertAudioToCurrentTrackAtPlayhead(mediaPath,  --> Bool               # Inserts the media specified by mediaPath (string) with startOffsetInSamples (int) and durationInSamples (int) at the playhead on a selected track on the Fairlight page. Returns True if successful, otherwise False.
#           startOffsetInSamples, durationInSamples)
#   GetColorGroupsList()                            --> [ColorGroups...]   # Returns a list of all group objects in the timeline.
#   AddColorGroup(groupName)                        --> ColorGroup         # Creates a new ColorGroup. groupName must be a unique string.
#   DeleteColorGroup(colorGroup)                    --> Bool               # Deletes the given color group and sets clips to ungrouped.
