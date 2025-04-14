from typing import Any

from .render import (
    Render,
)
from .timeline import DVRTimeline


class DVRProject:
    def __init__(self, project: Any):
        self._dvr_project = project
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
#   GetPresetList()                                 --> [presets...]       # Returns a list of presets and their information.
#   SetPreset(presetName)                           --> Bool               # Sets preset by given presetName (string) into project.
#   AddRenderJob()                                  --> string             # Adds a render job based on current render settings to the render queue. Returns a unique job id (string) for the new render job.
#   DeleteRenderJob(jobId)                          --> Bool               # Deletes render job for input job id (string).
#   DeleteAllRenderJobs()                           --> Bool               # Deletes all render jobs in the queue.
#   GetRenderJobList()                              --> [render jobs...]   # Returns a list of render jobs and their information.
#   GetRenderPresetList()                           --> [presets...]       # Returns a list of render presets and their information.
#   StartRendering(jobId1, jobId2, ...)             --> Bool               # Starts rendering jobs indicated by the input job ids.
#   StartRendering([jobIds...], isInteractiveMode=False)    --> Bool       # Starts rendering jobs indicated by the input job ids.
#                                                                          # The optional "isInteractiveMode", when set, enables error feedback in the UI during rendering.
#   StartRendering(isInteractiveMode=False)                 --> Bool       # Starts rendering all queued render jobs.
#                                                                          # The optional "isInteractiveMode", when set, enables error feedback in the UI during rendering.
#   StopRendering()                                 --> None               # Stops any current render processes.
#   IsRenderingInProgress()                         --> Bool               # Returns True if rendering is in progress.
#   LoadRenderPreset(presetName)                    --> Bool               # Sets a preset as current preset for rendering if presetName (string) exists.
#   SaveAsNewRenderPreset(presetName)               --> Bool               # Creates new render preset by given name if presetName(string) is unique.
#   DeleteRenderPreset(presetName)                  --> Bool               # Delete render preset by provided name.
#   SetRenderSettings({settings})                   --> Bool               # Sets given settings for rendering. Settings is a dict, with support for the keys:
#                                                                          # Refer to "Looking up render settings" section for information for supported settings
#   GetRenderJobStatus(jobId)                       --> {status info}      # Returns a dict with job status and completion percentage of the job by given jobId (string).
#   GetQuickExportRenderPresets()                   --> [preset_name..]    # Returns a list of Quick Export render presets by name
#   RenderWithQuickExport(preset_name, {param_dict})--> {status info}      # Starts a quick export render for the current active timeline. preset_name from GetQuickExportRenderPresets list. param_dict supports render settings keys "TargetDir", "CustomName", "VideoQuality", and "EnableUpload".
#                                                                          # "EnableUpload" key enables direct upload for supported web presets.
#                                                                          # Returns a dict with job status and time taken to render, or an error string if render has failed or not attempted
#                                                                          # Refer to "Looking up Render Settings" section for information on the above supported settings
#   GetSetting(settingName)                         --> string             # Returns value of project setting (indicated by settingName, string). Check the section below for more information.
#   SetSetting(settingName, settingValue)           --> Bool               # Sets the project setting (indicated by settingName, string) to the value (settingValue, string). Check the section below for more information.
#   GetRenderFormats()                              --> {render formats..} # Returns a dict (format -> file extension) of available render formats.
#   GetRenderCodecs(renderFormat)                   --> {render codecs...} # Returns a dict (codec description -> codec name) of available codecs for given render format (string).
#   GetCurrentRenderFormatAndCodec()                --> {format, codec}    # Returns a dict with currently selected format 'format' and render codec 'codec'.
#   SetCurrentRenderFormatAndCodec(format, codec)   --> Bool               # Sets given render format (string) and render codec (string) as options for rendering.
#   GetCurrentRenderMode()                          --> int                # Returns the render mode: 0 - Individual clips, 1 - Single clip.
#   SetCurrentRenderMode(renderMode)                --> Bool               # Sets the render mode. Specify renderMode = 0 for Individual clips, 1 for Single clip.
#   GetRenderResolutions(format, codec)             --> [{Resolution}]     # Returns list of resolutions applicable for the given render format (string) and render codec (string). Returns full list of resolutions if no argument is provided. Each element in the list is a dictionary with 2 keys "Width" and "Height".
#   RefreshLUTList()                                --> Bool               # Refreshes LUT List
#   GetUniqueId()                                   --> string             # Returns a unique ID for the project item
#   InsertAudioToCurrentTrackAtPlayhead(mediaPath,  --> Bool               # Inserts the media specified by mediaPath (string) with startOffsetInSamples (int) and durationInSamples (int) at the playhead on a selected track on the Fairlight page. Returns True if successful, otherwise False.
#           startOffsetInSamples, durationInSamples)
#   LoadBurnInPreset(presetName)                    --> Bool               # Loads user defined data burn in preset for project when supplied presetName (string). Returns true if successful.
#   ExportCurrentFrameAsStill(filePath)             --> Bool               # Exports current frame as still to supplied filePath. filePath must end in valid export file format. Returns True if successful, False otherwise.
#   GetColorGroupsList()                            --> [ColorGroups...]   # Returns a list of all group objects in the timeline.
#   AddColorGroup(groupName)                        --> ColorGroup         # Creates a new ColorGroup. groupName must be a unique string.
#   DeleteColorGroup(colorGroup)                    --> Bool               # Deletes the given color group and sets clips to ungrouped.
