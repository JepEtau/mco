from dataclasses import dataclass
from typing import Any
from warnings import warn
from .media_pool import DVRMediaPoolItem

from utils.p_print import lightcyan



@dataclass
class Transform:
    item: Any

    @property
    def zoom_x(self) -> float:
        return self.item.GetProperty("ZoomX")

    @zoom_x.setter
    def zoom_x(self, x: float) -> None:
        return self.item.SetProperty("ZoomX", x)

    @property
    def zoom_y(self) -> float:
        return self.item.GetProperty("ZoomY")

    @zoom_y.setter
    def zoom_y(self, y: float) -> None:
        return self.item.SetProperty("ZoomY", y)

    @property
    def rotation_angle(self) -> float:
        return self.item.GetProperty("RotationAngle")

    @rotation_angle.setter
    def rotation_angle(self, angle: float) -> None:
        return self.item.SetProperty("RotationAngle", angle)



@dataclass
class Cropping:
    item: Any

    @property
    def crop(self) -> list[float]:
        """Returns tuple of values: [left, right, top, bottom]"""
        return (
            self.item.GetProperty("CropLeft"),
            self.item.GetProperty("CropRight"),
            self.item.GetProperty("CropTop"),
            self.item.GetProperty("CropBottom")
        )

    @crop.setter
    def crop(self, crop: tuple[float]) -> None:
        for key, v in zip(
            ("CropLeft", "CropRight", "CropTop", "CropBottom"),
            crop
        ):
            self.item.SetProperty(key, v)

    @property
    def softness(self) -> float:
        return self.item.GetProperty("CropSoftness")

    @softness.setter
    def softness(self, softness: float) -> None:
        return self.item.SetProperty("CropSoftness", softness)

    @property
    def retain_image_position(self) -> bool:
        return self.item.GetProperty("CropRetain")

    @retain_image_position.setter
    def retain_image_position(self, enable: bool) -> None:
        return self.item.SetProperty("CropRetain", enable)



class DVRItem:
    def __init__(
        self,
        dvr_timeline_item: Any,
        dvr_timeline: Any,
        project: Any,
        dvr_index: int,
        # timeline_index: int,
    ):
        super().__init__()
        self._dvr_timeline_item = dvr_timeline_item
        self._dvr_timeline = dvr_timeline
        self._dvr_project = project
        self._dvr_index = dvr_index

        self.name: str = dvr_timeline_item.GetName()
        self.start_frame: int = dvr_timeline_item.GetStart()
        self.last_frame: int = dvr_timeline_item.GetEnd() - 1
        self.frame_count: int = dvr_timeline_item.GetDuration()
        self.media_clip: DVRMediaPoolItem = None

        dvr_media_pool_item = None
        try:
            dvr_media_pool_item = dvr_timeline_item.GetMediaPoolItem()
        except:
            warn(f"Failed to get MediaPoolItem for item `{self.name}`")

        if dvr_media_pool_item is not None:
            self.media_clip: DVRMediaPoolItem = DVRMediaPoolItem(
                media_pool_item=dvr_media_pool_item, timeline_item=dvr_timeline_item
            )
        self._dvr_media_pool_item = dvr_media_pool_item
        self._transform = Transform(self._dvr_timeline_item)
        self._cropping = Cropping(self._dvr_timeline_item)


    @property
    def index(self) -> int:
        """Return the index in timeline
        """
        return self._dvr_index


    @property
    def dvr_timeline_item(self):
        """Return the DaVinci Resolve timeline item.\n
            it permits to access to the properties/functions\n
            that are not implemented in this class.
        """
        return self._dvr_timeline_item


    @property
    def dvr_media_pool_item(self) -> Any:
        return self._dvr_media_pool_item


    def get_properties(self) -> dict[str, float | int | str]:
        return self._dvr_timeline_item.GetProperty()


    def get_property(self, name: str) -> Any | dict[str, Any]:
        if not name:
            raise ValueError(f"Not a valid property name: {name}")
        return self._dvr_timeline_item.GetProperty(name)


    def set_property(self, name: str, value: float | int | str) -> bool:
        if not name:
            raise ValueError(f"Not a valid property name: {name}")
        return self._dvr_timeline_item.SetProperty(name, value)


    @property
    def transform(self) -> Transform:
        return self._transform


    @property
    def cropping(self) -> Cropping:
        return self._cropping


    def __str__(self):
        item_str: str = f"""{self.__class__.__name__}(
            name={self.name},
            start_frame={self.start_frame},
            last_frame={self.last_frame},
            frame_count={self.last_frame - self.start_frame + 1},
            media_clip={self.media_clip},\n)
        """
        return item_str.replace ("            ", "  ")


    def stabilize(self) -> bool:
        # Function to reapply stabilization without changing the settings
        # because they're not accessible
        return self._dvr_timeline_item.Stabilize()



# TimelineItem
#   GetName()                                       --> string             # Returns the item name.
#   GetDuration(subframe_precision)                 --> int/float          # Returns the item duration. Returns fractional frames if subframe_precision is True
#   GetEnd(subframe_precision)                      --> int/float          # Returns the end frame position on the timeline. Returns fractional frames if subframe_precision is True
#   GetSourceEndFrame()                             --> int                # Returns the end frame position of the media pool clip in the timeline clip.
#   GetSourceEndTime()                              --> float              # Returns the end time position of the media pool clip in the timeline clip.
#   GetFusionCompCount()                            --> int                # Returns number of Fusion compositions associated with the timeline item.
#   GetFusionCompByIndex(compIndex)                 --> fusionComp         # Returns the Fusion composition object based on given index. 1 <= compIndex <= timelineItem.GetFusionCompCount()
#   GetFusionCompNameList()                         --> [names...]         # Returns a list of Fusion composition names associated with the timeline item.
#   GetFusionCompByName(compName)                   --> fusionComp         # Returns the Fusion composition object based on given name.
#   GetLeftOffset(subframe_precision)               --> int/float          # Returns the maximum extension by frame for clip from left side. Returns fractional frames if subframe_precision is True
#   GetRightOffset(subframe_precision)              --> int/float          # Returns the maximum extension by frame for clip from right side. Returns fractional frames if subframe_precision is True
#   GetStart(subframe_precision)                    --> int/float          # Returns the start frame position on the timeline. Returns fractional frames if subframe_precision is True
#   GetSourceStartFrame()                           --> int                # Returns the start frame position of the media pool clip in the timeline clip.
#   GetSourceStartTime()                            --> float              # Returns the start time position of the media pool clip in the timeline clip.
#   SetProperty(propertyKey, propertyValue)         --> Bool               # Sets the value of property "propertyKey" to value "propertyValue"
#                                                                          # Refer to "Looking up Timeline item properties" for more information
#   GetProperty(propertyKey)                        --> int/[key:value]    # returns the value of the specified key
#                                                                          # if no key is specified, the method returns a dictionary(python) or table(lua) for all supported keys
#   AddMarker(frameId, color, name, note, duration, --> Bool               # Creates a new marker at given frameId position and with given marker information. 'customData' is optional and helps to attach user specific data to the marker.
#             customData)
#   GetMarkers()                                    --> {markers...}       # Returns a dict (frameId -> {information}) of all markers and dicts with their information.
#                                                                          # Example: a value of {96.0: {'color': 'Green', 'duration': 1.0, 'note': '', 'name': 'Marker 1', 'customData': ''}, ...} indicates a single green marker at clip offset 96
#   GetMarkerByCustomData(customData)               --> {markers...}       # Returns marker {information} for the first matching marker with specified customData.
#   UpdateMarkerCustomData(frameId, customData)     --> Bool               # Updates customData (string) for the marker at given frameId position. CustomData is not exposed via UI and is useful for scripting developer to attach any user specific data to markers.
#   GetMarkerCustomData(frameId)                    --> string             # Returns customData string for the marker at given frameId position.
#   DeleteMarkersByColor(color)                     --> Bool               # Delete all markers of the specified color from the timeline item. "All" as argument deletes all color markers.
#   DeleteMarkerAtFrame(frameNum)                   --> Bool               # Delete marker at frame number from the timeline item.
#   DeleteMarkerByCustomData(customData)            --> Bool               # Delete first matching marker with specified customData.
#   AddFlag(color)                                  --> Bool               # Adds a flag with given color (string).
#   GetFlagList()                                   --> [colors...]        # Returns a list of flag colors assigned to the item.
#   ClearFlags(color)                               --> Bool               # Clear flags of the specified color. An "All" argument is supported to clear all flags.
#   GetClipColor()                                  --> string             # Returns the item color as a string.
#   SetClipColor(colorName)                         --> Bool               # Sets the item color based on the colorName (string).
#   ClearClipColor()                                --> Bool               # Clears the item color.
#   AddFusionComp()                                 --> fusionComp         # Adds a new Fusion composition associated with the timeline item.
#   ImportFusionComp(path)                          --> fusionComp         # Imports a Fusion composition from given file path by creating and adding a new composition for the item.
#   ExportFusionComp(path, compIndex)               --> Bool               # Exports the Fusion composition based on given index to the path provided.
#   DeleteFusionCompByName(compName)                --> Bool               # Deletes the named Fusion composition.
#   LoadFusionCompByName(compName)                  --> fusionComp         # Loads the named Fusion composition as the active composition.
#   RenameFusionCompByName(oldName, newName)        --> Bool               # Renames the Fusion composition identified by oldName.
#   AddVersion(versionName, versionType)            --> Bool               # Adds a new color version for a video clip based on versionType (0 - local, 1 - remote).
#   GetCurrentVersion()                             --> {versionName...}   # Returns the current version of the video clip. The returned value will have the keys versionName and versionType(0 - local, 1 - remote).
#   DeleteVersionByName(versionName, versionType)   --> Bool               # Deletes a color version by name and versionType (0 - local, 1 - remote).
#   LoadVersionByName(versionName, versionType)     --> Bool               # Loads a named color version as the active version. versionType: 0 - local, 1 - remote.
#   RenameVersionByName(oldName, newName, versionType)--> Bool             # Renames the color version identified by oldName and versionType (0 - local, 1 - remote).
#   GetVersionNameList(versionType)                 --> [names...]         # Returns a list of all color versions for the given versionType (0 - local, 1 - remote).
#   GetMediaPoolItem()                              --> MediaPoolItem      # Returns the media pool item corresponding to the timeline item if one exists.
#   GetStereoConvergenceValues()                    --> {keyframes...}     # Returns a dict (offset -> value) of keyframe offsets and respective convergence values.
#   GetStereoLeftFloatingWindowParams()             --> {keyframes...}     # For the LEFT eye -> returns a dict (offset -> dict) of keyframe offsets and respective floating window params. Value at particular offset includes the left, right, top and bottom floating window values.
#   GetStereoRightFloatingWindowParams()            --> {keyframes...}     # For the RIGHT eye -> returns a dict (offset -> dict) of keyframe offsets and respective floating window params. Value at particular offset includes the left, right, top and bottom floating window values.
#   SetCDL([CDL map])                               --> Bool               # Keys of map are: "NodeIndex", "Slope", "Offset", "Power", "Saturation", where 1 <= NodeIndex <= total number of nodes.
#                                                                          # Example python code - SetCDL({"NodeIndex" : "1", "Slope" : "0.5 0.4 0.2", "Offset" : "0.4 0.3 0.2", "Power" : "0.6 0.7 0.8", "Saturation" : "0.65"})
#   AddTake(mediaPoolItem, startFrame, endFrame)    --> Bool               # Adds mediaPoolItem as a new take. Initializes a take selector for the timeline item if needed. By default, the full clip extents is added. startFrame (int) and endFrame (int) are optional arguments used to specify the extents.
#   GetSelectedTakeIndex()                          --> int                # Returns the index of the currently selected take, or 0 if the clip is not a take selector.
#   GetTakesCount()                                 --> int                # Returns the number of takes in take selector, or 0 if the clip is not a take selector.
#   GetTakeByIndex(idx)                             --> {takeInfo...}      # Returns a dict (keys "startFrame", "endFrame" and "mediaPoolItem") with take info for specified index.
#   DeleteTakeByIndex(idx)                          --> Bool               # Deletes a take by index, 1 <= idx <= number of takes.
#   SelectTakeByIndex(idx)                          --> Bool               # Selects a take by index, 1 <= idx <= number of takes.
#   FinalizeTake()                                  --> Bool               # Finalizes take selection.
#   CopyGrades([tgtTimelineItems])                  --> Bool               # Copies the current node stack layer grade to the same layer for each item in tgtTimelineItems. Returns True if successful.
#   SetClipEnabled(Bool)                            --> Bool               # Sets clip enabled based on argument.
#   GetClipEnabled()                                --> Bool               # Gets clip enabled status.
#   UpdateSidecar()                                 --> Bool               # Updates sidecar file for BRAW clips or RMD file for R3D clips.
#   GetUniqueId()                                   --> string             # Returns a unique ID for the timeline item
#   LoadBurnInPreset(presetName)                    --> Bool               # Loads user defined data burn in preset for clip when supplied presetName (string). Returns true if successful.
#   CreateMagicMask(mode)                           --> Bool               # Returns True if magic mask was created successfully, False otherwise. mode can "F" (forward), "B" (backward), or "BI" (bidirection)
#   RegenerateMagicMask()                           --> Bool               # Returns True if magic mask was regenerated successfully, False otherwise.
#   Stabilize()                                     --> Bool               # Returns True if stabilization was successful, False otherwise
#   SmartReframe()                                  --> Bool               # Performs Smart Reframe. Returns True if successful, False otherwise.
#   GetNodeGraph(layerIdx)                          --> Graph              # Returns the clip's node graph object at layerIdx (int, optional). Returns the first layer if layerIdx is skipped. 1 <= layerIdx <= project.GetSetting("nodeStackLayers").
#   GetColorGroup()                                 --> ColorGroup         # Returns the clip's color group if one exists.
#   AssignToColorGroup(ColorGroup)                  --> Bool               # Returns True if TiItem to successfully assigned to given ColorGroup. ColorGroup must be an existing group in the current project.
#   RemoveFromColorGroup()                          --> Bool               # Returns True if the TiItem is successfully removed from the ColorGroup it is in.
#   ExportLUT(exportType, path)                     --> Bool               # Exports LUTs from tiItem referring to value passed in 'exportType' (enum) for LUT size. Refer to. 'ExportLUT notes' section for possible values.
#                                                                          # Saves generated LUT in the provided 'path' (string). 'path' should include the intended file name.
#                                                                          # If an empty or incorrect extension is provided, the appropriate extension (.cube/.vlt) will be appended at the end of the path.
#   GetLinkedItems()                                --> [TimelineItems]    # Returns a list of linked timeline items.
#   GetTrackTypeAndIndex()                          --> [trackType, trackIndex] # Returns a list of two values that correspond to the TimelineItem's trackType (string) and trackIndex (int) respectively.
#                                                                            # trackType is one of {"audio", "video", "subtitle"}
#                                                                            # 1 <= trackIndex <= Timeline.GetTrackCount(trackType)
#   GetSourceAudioChannelMapping()                 --> json formatted string # Returns a string with TimelineItem's audio mapping information. Check 'Audio Mapping' section below for more information.
#   GetIsColorOutputCacheEnabled()                  --> cache_value        # Returns if the cache corresponding to cache_type is enabled
#   GetIsFusionOutputCacheEnabled()                 --> cache_value        # Returns if the cache corresponding to cache_type is enabled (or auto)
#   SetColorOutputCache(cache_value)                --> Bool               # Sets caching to enabled or disabled. Equivalent to clip context menu action 'Render Cache Color Output'.
#   SetFusionOutputCache(cache_value)               --> Bool               # Sets caching to auto, enabled or disabled. Equivalent to clip context menu action 'Render Cache Fusion Output'.



# The supported keys with their accepted values are:
#   "Pan" : floating point values from -4.0*width to 4.0*width
#   "Tilt" : floating point values from -4.0*height to 4.0*height
#   "ZoomX" : floating point values from 0.0 to 100.0
#   "ZoomY" : floating point values from 0.0 to 100.0
#   "ZoomGang" : a boolean value
#   "RotationAngle" : floating point values from -360.0 to 360.0
#   "AnchorPointX" : floating point values from -4.0*width to 4.0*width
#   "AnchorPointY" : floating point values from -4.0*height to 4.0*height
#   "Pitch" : floating point values from -1.5 to 1.5
#   "Yaw" : floating point values from -1.5 to 1.5
#   "FlipX" : boolean value for flipping horizontally
#   "FlipY" : boolean value for flipping vertically
#   "CropLeft" : floating point values from 0.0 to width
#   "CropRight" : floating point values from 0.0 to width
#   "CropTop" : floating point values from 0.0 to height
#   "CropBottom" : floating point values from 0.0 to height
#   "CropSoftness" : floating point values from -100.0 to 100.0
#   "CropRetain" : boolean value for "Retain Image Position" checkbox
#   "DynamicZoomEase" : A value from the following constants
#      - DYNAMIC_ZOOM_EASE_LINEAR = 0
#      - DYNAMIC_ZOOM_EASE_IN
#      - DYNAMIC_ZOOM_EASE_OUT
#      - DYNAMIC_ZOOM_EASE_IN_AND_OUT
#   "CompositeMode" : A value from the following constants
#      - COMPOSITE_NORMAL = 0
#      - COMPOSITE_ADD
#      - COMPOSITE_SUBTRACT
#      - COMPOSITE_DIFF
#      - COMPOSITE_MULTIPLY
#      - COMPOSITE_SCREEN
#      - COMPOSITE_OVERLAY
#      - COMPOSITE_HARDLIGHT
#      - COMPOSITE_SOFTLIGHT
#      - COMPOSITE_DARKEN
#      - COMPOSITE_LIGHTEN
#      - COMPOSITE_COLOR_DODGE
#      - COMPOSITE_COLOR_BURN
#      - COMPOSITE_EXCLUSION
#      - COMPOSITE_HUE
#      - COMPOSITE_SATURATE
#      - COMPOSITE_COLORIZE
#      - COMPOSITE_LUMA_MASK
#      - COMPOSITE_DIVIDE
#      - COMPOSITE_LINEAR_DODGE
#      - COMPOSITE_LINEAR_BURN
#      - COMPOSITE_LINEAR_LIGHT
#      - COMPOSITE_VIVID_LIGHT
#      - COMPOSITE_PIN_LIGHT
#      - COMPOSITE_HARD_MIX
#      - COMPOSITE_LIGHTER_COLOR
#      - COMPOSITE_DARKER_COLOR
#      - COMPOSITE_FOREGROUND
#      - COMPOSITE_ALPHA
#      - COMPOSITE_INVERTED_ALPHA
#      - COMPOSITE_LUM
#      - COMPOSITE_INVERTED_LUM
#   "Opacity" : floating point value from 0.0 to 100.0
#   "Distortion" : floating point value from -1.0 to 1.0
#   "RetimeProcess" : A value from the following constants
#      - RETIME_USE_PROJECT = 0
#      - RETIME_NEAREST
#      - RETIME_FRAME_BLEND
#      - RETIME_OPTICAL_FLOW
#   "MotionEstimation" : A value from the following constants
#      - MOTION_EST_USE_PROJECT = 0
#      - MOTION_EST_STANDARD_FASTER
#      - MOTION_EST_STANDARD_BETTER
#      - MOTION_EST_ENHANCED_FASTER
#      - MOTION_EST_ENHANCED_BETTER
#      - MOTION_EST_SPEED_WARP_BETTER
#      - MOTION_EST_SPEED_WARP_FASTER
#   "Scaling" : A value from the following constants
#      - SCALE_USE_PROJECT = 0
#      - SCALE_CROP
#      - SCALE_FIT
#      - SCALE_FILL
#      - SCALE_STRETCH
#   "ResizeFilter" : A value from the following constants
#      - RESIZE_FILTER_USE_PROJECT = 0
#      - RESIZE_FILTER_SHARPER
#      - RESIZE_FILTER_SMOOTHER
#      - RESIZE_FILTER_BICUBIC
#      - RESIZE_FILTER_BILINEAR
#      - RESIZE_FILTER_BESSEL
#      - RESIZE_FILTER_BOX
#      - RESIZE_FILTER_CATMULL_ROM
#      - RESIZE_FILTER_CUBIC
#      - RESIZE_FILTER_GAUSSIAN
#      - RESIZE_FILTER_LANCZOS
#      - RESIZE_FILTER_MITCHELL
#      - RESIZE_FILTER_NEAREST_NEIGHBOR
#      - RESIZE_FILTER_QUADRATIC
#      - RESIZE_FILTER_SINC
#      - RESIZE_FILTER_LINEAR
# Values beyond the range will be clipped
# width and height are same as the UI max limits
