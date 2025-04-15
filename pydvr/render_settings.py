
import os
from typing import Any, Literal


SettingKey = Literal[
    "SelectAllFrames",
    "MarkIn",
    "MarkOut",
    "TargetDir",
    "CustomName",
    "UniqueFilenameStyle",
    "ExportVideo",
    "ExportAudio",
    "FormatWidth",
    "FormatHeight",
    "FrameRate",
    "PixelAspectRatio",
    "VideoQuality",
    "AudioCodec",
    "AudioBitDepth",
    "AudioSampleRate",
    "ColorSpaceTag",
    "GammaTag",
    "ExportAlpha",
    "EncodingProfile",
    "MultiPassEncode",
    "AlphaMode",
    "NetworkOptimization",
    "ClipStartFrame",
    "TimelineStartTimecode",
    "ReplaceExistingFilesInPlace",
]


PixelRatio = Literal[
    "16_9",
    "4_3",
    "square",
    "cinemascope",
]


class RenderSettings:
    def __init__(self, dvr_project: Any):
        self._render_settings: dict[SettingKey, float | int | str] = {}
        self._dvr_project = dvr_project
        self.new_settings()


    def new_settings(self) -> None:
        self._render_settings = {
            "ExportVideo": True,
            "ExportAudio": True,
            "ReplaceExistingFilesInPlace": False,
        }


    def set_setting(self, name: SettingKey, value: int | float | str) -> None:
        self._render_settings[name] = value


    def apply_settings(self) -> bool:
        return self._dvr_project.SetRenderSettings(self._render_settings)


    def set_settings(self, settings: SettingKey) -> bool:
        return self._dvr_project.SetRenderSettings(settings)


    def select_all_frames(self, select: bool) -> bool:
        """Select all frames: when set True, the settings MarkIn and MarkOut are ignored
        """
        self._render_settings["SelectAllFrames"] = select


    @property
    def mark_in(self) -> int:
        return self._render_settings.get("MarkIn", 0)

    @mark_in.setter
    def mark_in(self, value) -> None:
        self._render_settings["MarkIn"] = value

    def set_mark_in(self, mark: int) -> None:
        self.mark_in = mark


    @property
    def mark_out(self) -> int:
        return self._render_settings.get("MarkOut", 0)

    @mark_out.setter
    def mark_out(self, value) -> None:
        self._render_settings["MarkOut"] = value

    def set_mark_out(self, mark: int) -> None:
        self.mark_out = mark


    @property
    def mark_range(self) -> tuple[int, int]:
        return (
            self._render_settings.get("MarkIn", 0),
            self._render_settings.get("MarkOut", 0)
        )

    @mark_range.setter
    def mark_range(self, marks: tuple[int, int]) -> None:
        self._render_settings["MarkIn"] = marks[0]
        self._render_settings["MarkOut"] = marks[1]

    def set_mark_range(self, mark_in: int, mark_out: int) -> None:
        self.mark_range = (mark_in, mark_out)


    @property
    def export_video(self) -> bool:
        return self._render_settings["ExportVideo"]

    @export_video.setter
    def export_video(self, enable: bool) -> None:
        self._render_settings["ExportVideo"] = enable


    @property
    def export_audio(self) -> bool:
        return self._render_settings["ExportAudio"]

    @export_audio.setter
    def export_audio(self, enable: bool) -> None:
        self._render_settings["ExportAudio"] = enable


    @property
    def overwrite_output_file(self) -> bool:
        return self._render_settings["ReplaceExistingFilesInPlace"]

    @overwrite_output_file.setter
    def overwrite_output_file(self, enable: bool) -> None:
        self._render_settings["ReplaceExistingFilesInPlace"] = enable


    @property
    def output_size(self) -> tuple[int, int]:
        return (
            self._render_settings.get("FormatWidth", -1),
            self._render_settings.get("FormatHeight", -1),
        )

    @output_size.setter
    def output_size(self, size: tuple[int, int]) -> None:
        self._render_settings["FormatWidth"] = size[0]
        self._render_settings["FormatHeight"] = size[1]

    def set_output_size(self, size: tuple[int, int]) -> None:
        self.output_size = size


    @property
    def framerate(self) -> float | int:
        return self._render_settings["FrameRate"]

    @framerate.setter
    def framerate(self, framerate: float | int) -> None:
        self._render_settings["FrameRate"] = framerate

    def set_framerate(self, framerate: float | int) -> None:
        self.framerate = framerate


    @property
    def pixel_ratio(self) -> PixelRatio:
        return self._render_settings["PixelAspectRatio"]

    @pixel_ratio.setter
    def pixel_ratio(self, ratio: PixelRatio) -> None:
        # for SD resolution: "16_9" or "4_3"
        # other: "square" or "cinemascope"
        # TODO: check if allowed depending on resolution
        self._render_settings["PixelAspectRatio"] = ratio

    def set_pixel_ratio(self, ratio: PixelRatio) -> None:
        self.pixel_ratio = ratio


    @property
    def output_dir(self) -> str:
        return self._render_settings.get("TargetDir", "")

    @output_dir.setter
    def output_dir(self, directory: str) -> None:
        self._render_settings["TargetDir"] = (
            os.path.abspath(os.path.expanduser(directory))
        )

    def set_output_dir(self, directory: str) -> None:
        self.output_dir = directory


    @property
    def custom_name(self) -> str:
        return self._render_settings.get("CustomName", "")

    @custom_name.setter
    def custom_name(self, name: str) -> None:
        self._render_settings["CustomName"] = name

    def set_custom_name(self, name: str) -> None:
        self.custom_name = name


    @property
    def video_quality(self) -> int | str:
        """
            "VideoQuality" possible values for current codec (if applicable):
            - 0 (int) - will set quality to automatic
            - [1 -> MAX] (int) - will set input bit rate
            - ["Least", "Low", "Medium", "High", "Best"] (String)
        """
        quality = self._render_settings.get("VideoQuality", "auto")
        return quality.lower() if isinstance(quality, str) else quality


    @video_quality.setter
    def video_quality(self, quality: int | str) -> None:
        if "auto" in quality:
            quality = 0
        elif isinstance(quality, str):
            quality = quality.capitalize()
        self._render_settings["VideoQuality"] = quality


    def set_video_quality(self, quality: int | str) -> None:
        self.video_quality = quality

    # Not implemented:
    #   UniqueFilenameStyle
    #   AudioCodec
    #   AudioBitDepth
    #   AudioSampleRate
    #   ColorSpaceTag
    #   GammaTag
    #   ExportAlpha
    #   EncodingProfile
    #   MultiPassEncode
    #   AlphaMode
    #   NetworkOptimization
    #   ClipStartFrame
    #   TimelineStartTimecode



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


