
import os


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
