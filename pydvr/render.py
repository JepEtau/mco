
from typing import Any, Literal
from .render_settings import RenderSettings



class Render(RenderSettings):
    def __init__(self, dvr_project: Any):
        super().__init__(dvr_project=dvr_project)
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



