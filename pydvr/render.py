
import os
from typing import Any, Literal



class RenderSettings:
    def __init__(self):
        self.select_all_frames: bool = True
        self.mark_in: int = -1
        self.mark_out: int = -1
        self.target_dir: str = None


    def set_target_dir(self, directory: str) -> None:
        self.target_dir = os.path.abspath(os.path.expanduser(directory))


    def as_dict(self):
        settings_dict = {
            "SelectAllFrames": self.select_all_frames,
            "MarkIn": self.mark_in if self.mark_in > 0 else None,
            "MarkOut": self.mark_out if self.mark_out > 0 else None,
            "TargetDir": self.target_dir if self.target_dir else None,
            # "CustomName": ,
            # "UniqueFilenameStyle": ,
            # "ExportVideo": ,
            # "ExportAudio": ,
            # "FormatWidth": ,
            # "FormatHeight": ,
            # "FrameRate": ,
            # "PixelAspectRatio": ,
            # "VideoQuality": ,
            # "AudioCodec": ,
            # "AudioBitDepth": ,
            # "AudioSampleRate": ,
            # "ColorSpaceTag": ,
            # "GammaTag": ,
            # "ExportAlpha": ,
            # "EncodingProfile": ,
            # "MultiPassEncode": ,
            # "AlphaMode": ,
            # "NetworkOptimization": ,
            # "ClipStartFrame": ,
            # "TimelineStartTimecode": ,
            # "ReplaceExistingFilesInPlace": ,
        }
        return dict([{k: v} for k, v in settings_dict.items if v is not None])



class Render:
    def __init__(self, dvr_project: Any):
        self._dvr_project = dvr_project


    def get_presets(self) -> list:
        return self._dvr_project.GetPresetList()


    def set_preset(self, name: str) -> bool:
        return self._dvr_project.SetPreset(name)


    def load_preset(self, name: str) -> bool:
        return self._dvr_project.LoadRenderPreset(name)


    def save_as_preset(self, name: str) -> bool:
        return self._dvr_project.SaveAsNewRenderPreset(name)


    def delete_preset(self, name: str) -> bool:
        return self._dvr_project.DeleteRenderPreset(name)


    def LoadBurnInPreset(self, name: str) -> bool:
        self._dvr_project.LoadBurnInPreset(name)


    def set_settings(self, settings: RenderSettings) -> bool:
        return self._dvr_project.SetRenderSettings(settings.as_dict())


    def set_mode(self, mode: Literal["single", "individual"]) -> bool:
        return self._dvr_project.SetCurrentRenderMode(
            1 if mode == "single" else 0
        )


    def get_render_mode(self) -> Literal["single", "individual"]:
        return (
            "single"
            if self._dvr_project.GetCurrentRenderMode() == 1
            else "individual"
        )


    def add_render_job(self) -> str:
        return self.AddRenderJob()


    def delete_render_job(self, job_id: str) -> bool:
        return self._dvr_project.DeleteRenderJob(job_id)


    def delete_all_render_jobs(self) -> bool:
        return self._dvr_project.DeleteAllRenderJobs()


    def get_render_jobs(self) -> list:
        return self._dvr_project.GetRenderJobList()


    def start_rendering(self, job_ids: list[str] = [], interactive: bool = False) -> bool:
        if job_ids:
            return self._dvr_project.StartRendering(job_ids, isInteractiveMode=interactive)

        return self._dvr_project.StartRendering(isInteractiveMode=interactive)


    def stop_rendering(self) -> bool:
        return self._dvr_project.StopRendering()


    def is_rendering(self) -> bool:
        return self._dvr_project.IsRenderingInProgress()


    def rendering_status(self, job_id: str) -> dict[str, str]:
        return self._dvr_project.GetRenderJobStatus(job_id)


    def get_video_formats(self) -> dict[str, str]:
        """Returns extension for each video format
            {
                'AVI': 'avi',
                'BRAW': 'braw',
                'Cineon': 'cin',
                'DCP': 'dcp',
                'DPX': 'dpx',
                'EXR': 'exr',
                'GIF': 'gif',
                'HLS': 'm3u8',
                'IMF': 'imf',
                'JPEG 2000': 'j2c',
                'MJ2': 'mj2',
                'MKV': 'mkv',
                'MP4': 'mp4',
                'MTS': 'mts',
                'MXF OP-Atom': 'mxf',
                'MXF OP1A': 'mxf_op1a',
                'Panasonic AVC': 'pavc',
                'QuickTime': 'mov',
                'TIFF': 'tif',
                'Wave': 'wav'
            }
        """
        return self._dvr_project.GetRenderFormats()


# Project
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
#   GetRenderFormats()                              --> {render formats..} # Returns a dict (format -> file extension) of available render formats.
#   GetRenderCodecs(renderFormat)                   --> {render codecs...} # Returns a dict (codec description -> codec name) of available codecs for given render format (string).
#   GetCurrentRenderFormatAndCodec()                --> {format, codec}    # Returns a dict with currently selected format 'format' and render codec 'codec'.
#   SetCurrentRenderFormatAndCodec(format, codec)   --> Bool               # Sets given render format (string) and render codec (string) as options for rendering.
#   GetCurrentRenderMode()                          --> int                # Returns the render mode: 0 - Individual clips, 1 - Single clip.
#   SetCurrentRenderMode(renderMode)                --> Bool               # Sets the render mode. Specify renderMode = 0 for Individual clips, 1 for Single clip.
#   GetRenderResolutions(format, codec)             --> [{Resolution}]     # Returns list of resolutions applicable for the given render format (string) and render codec (string). Returns full list of resolutions if no argument is provided. Each element in the list is a dictionary with 2 keys "Width" and "Height".
#   LoadBurnInPreset(presetName)                    --> Bool               # Loads user defined data burn in preset for project when supplied presetName (string). Returns true if successful.
#   ExportCurrentFrameAsStill(filePath)             --> Bool               # Exports current frame as still to supplied filePath. filePath must end in valid export file format. Returns True if successful, False otherwise.



# Looking up Render Settings
# --------------------------
# This section covers the supported settings for the method SetRenderSettings({settings})

# The parameter setting is a dictionary containing the following keys:
#     - "SelectAllFrames": Bool (when set True, the settings MarkIn and MarkOut are ignored)
#     - "MarkIn": int
#     - "MarkOut": int
#     - "TargetDir": string
#     - "CustomName": string
#     - "UniqueFilenameStyle": 0 - Prefix, 1 - Suffix.
#     - "ExportVideo": Bool
#     - "ExportAudio": Bool
#     - "FormatWidth": int
#     - "FormatHeight": int
#     - "FrameRate": float (examples: 23.976, 24)
#     - "PixelAspectRatio": string (for SD resolution: "16_9" or "4_3") (other resolutions: "square" or "cinemascope")
#     - "VideoQuality" possible values for current codec (if applicable):
#     -    0 (int) - will set quality to automatic
#     -    [1 -> MAX] (int) - will set input bit rate
#     -    ["Least", "Low", "Medium", "High", "Best"] (String) - will set input quality level
#     - "AudioCodec": string (example: "aac")
#     - "AudioBitDepth": int
#     - "AudioSampleRate": int
#     - "ColorSpaceTag" : string (example: "Same as Project", "AstroDesign")
#     - "GammaTag" : string (example: "Same as Project", "ACEScct")
#     - "ExportAlpha": Bool
#     - "EncodingProfile": string (example: "Main10"). Can only be set for H.264 and H.265.
#     - "MultiPassEncode": Bool. Can only be set for H.264.
#     - "AlphaMode": 0 - Premultiplied, 1 - Straight. Can only be set if "ExportAlpha" is true.
#     - "NetworkOptimization": Bool. Only supported by QuickTime and MP4 formats.
#     - "ClipStartFrame": int
#     - "TimelineStartTimecode": string (example: "01:00:00:00")
#     - "ReplaceExistingFilesInPlace": Bool


# Looking up timeline export properties
# -------------------------------------
# This section covers the parameters for the argument Export(fileName, exportType, exportSubtype).

# exportType can be one of the following constants:
#     - resolve.EXPORT_AAF
#     - resolve.EXPORT_DRT
#     - resolve.EXPORT_EDL
#     - resolve.EXPORT_FCP_7_XML
#     - resolve.EXPORT_FCPXML_1_8
#     - resolve.EXPORT_FCPXML_1_9
#     - resolve.EXPORT_FCPXML_1_10
#     - resolve.EXPORT_HDR_10_PROFILE_A
#     - resolve.EXPORT_HDR_10_PROFILE_B
#     - resolve.EXPORT_TEXT_CSV
#     - resolve.EXPORT_TEXT_TAB
#     - resolve.EXPORT_DOLBY_VISION_VER_2_9
#     - resolve.EXPORT_DOLBY_VISION_VER_4_0
#     - resolve.EXPORT_DOLBY_VISION_VER_5_1
#     - resolve.EXPORT_OTIO
#     - resolve.EXPORT_ALE
#     - resolve.EXPORT_ALE_CDL
# exportSubtype can be one of the following enums:
#     - resolve.EXPORT_NONE
#     - resolve.EXPORT_AAF_NEW
#     - resolve.EXPORT_AAF_EXISTING
#     - resolve.EXPORT_CDL
#     - resolve.EXPORT_SDL
#     - resolve.EXPORT_MISSING_CLIPS
# Please note that exportSubType is a required parameter for resolve.EXPORT_AAF and resolve.EXPORT_EDL. For rest of the exportType, exportSubtype is ignored.
# When exportType is resolve.EXPORT_AAF, valid exportSubtype values are resolve.EXPORT_AAF_NEW and resolve.EXPORT_AAF_EXISTING.
# When exportType is resolve.EXPORT_EDL, valid exportSubtype values are resolve.EXPORT_CDL, resolve.EXPORT_SDL, resolve.EXPORT_MISSING_CLIPS and resolve.EXPORT_NONE.
# Note: Replace 'resolve.' when using the constants above, if a different Resolve class instance name is used.
