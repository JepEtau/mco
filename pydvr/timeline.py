import re
from typing import Any, Literal
from .timeline_item import DVRItem
from utils.p_print import red


TrackType = Literal['video', 'audio', 'subtitle']


class DVRTimeline:
    def __init__(self, dvr_project, timeline_index: int):
        self._dvr_project = dvr_project
        self._dvr_timeline = dvr_project.GetTimelineByIndex(timeline_index)
        self._video_items: list[DVRItem] = None


    @property
    def dvr_timeline(self):
        """Return the DaVinci Resolve timeline.\n
            it permits to access to the properties/functions\n
            that are not implemented in this class.
        """
        return self._dvr_timeline


    def get_settings(self) -> dict[str, float | int | str]:
        return self._dvr_timeline.GetSetting()


    def get_setting(self, name: str) -> Any | dict[str, Any]:
        if not name:
            raise ValueError(f"Not a valid setting name: {name}")
        return self._dvr_timeline.GetSetting(name)


    def set_setting(self, name: str, value: float | int | str) -> bool:
        if not name:
            raise ValueError(f"Not a valid property name: {name}")
        return self._dvr_timeline.SetSetting(name, value)


    @property
    def name(self) -> str:
        return self._dvr_timeline.GetName()


    @name.setter
    def name(self, name: str) -> None:
        self._dvr_timeline.SetName(name)


    def _track_count(self, type: TrackType = 'video') -> int:
        return self._dvr_timeline.GetTrackCount(type)


    def _track_name(self, type: TrackType = 'video', index: int = 1) -> str:
        try:
            return self._dvr_timeline.GetTrackName(type, index)
        except:
            raise ValueError(f"Failed getting track name for index={index}")


    def video_track_count(self) -> int:
        return self._track_count(type='video')


    def video_track_name(self, index: int = 1) -> str:
        return self._track_name(type='video', index=index)


    def flush_video_track(self) -> None:
        self._video_items = None


    def video_track_items(self, track_index: int = 1) -> list[DVRItem]:
        """Returns a list of items of the video track.\n
            This list is cached. The `flush_video_track` function MUST be called\n
            after each modification of the timeline.\n
            info: item no. 1 in timeline -> index no. 0 in this list\n
        """
        if self._video_items is None:
            self._video_items: list[DVRItem] = []
            for item in self._dvr_timeline.GetItemListInTrack("video", track_index):
                self._video_items.append(
                    DVRItem(
                        item,
                        dvr_timeline=self._dvr_timeline,
                        project=self._dvr_project
                    )
                )
        return self._video_items


    def video_item_count(self, track_index: int = 1) -> int:
        return len(self.video_track_items(track_index=track_index))


    def audio_track_count(self) -> int:
        return self._track_count(type='audio')


    def audio_track_name(self, index: int = 1) -> str:
        return self._track_name(type='audio', index=index)


    def audio_track_items(self, index: int = 1) -> list[Any]:
        raise NotImplementedError("To be reworked to work like video items")
        return self._dvr_timeline.GetItemListInTrack("audio", index)


    def set_as_current(self):
        self._dvr_project.SetCurrentTimeline(self._dvr_timeline)


    def set_current_timecode(self, timecode: int) -> None:
        self.set_as_current()
        self._dvr_timeline.SetCurrentTimecode(timecode)


    def start_timecode(self) -> str:
        self.set_as_current()
        return self._dvr_timeline.GetStartTimecode()


    def framerate(self) -> float:
        return float(self._dvr_timeline.GetSetting("timelineFrameRate"))


    def get_current_item(self) -> DVRItem:
        current_item = self._dvr_timeline.GetCurrentVideoItem()
        current_item_start = current_item.GetStart()
        current_item_end = current_item.GetEnd()
        for item in self.video_track_items():
            if (
                item.start_frame == current_item_start
                and item.end_frame == current_item_end
            ):
                return item
        raise ValueError(red("item not found"))


    def timecode_str_to_frame(self, timecode: str) -> float:
        if result := re.search(r"(\d+):(\d+):(\d+):(\d+)", timecode):
            hours, minutes, seconds, frames = result.groups()
            framerate = self.framerate()
            frame = (
                (hours * 3600 + minutes * 60 + seconds) * framerate + frames
            )
            return frame
        raise (red(f"not a valid or recognized timecode: {timecode}"))


    def frame_to_timecode(self, frame: str) -> int:
        framerate = self.framerate()
        hours = frame // (3600 * framerate)
        remainder = frame % (3600 * framerate)
        minutes = remainder // (60 * framerate)
        remainder %= (60 * framerate)
        seconds = remainder // framerate
        frames = remainder % framerate
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}:{int(frames):02}"


    def select_item(self, dvr_index: int) -> DVRItem:
        """Index from 1 to numberf of GetTrackCount()
        """
        try:
            item = self.video_track_items()[dvr_index - 1]
        except:
            raise ValueError(red(f"Not a valid index: {dvr_index}"))
        timecode: str = self.frame_to_timecode(item.start_frame)
        print(timecode)
        self.set_as_current()
        self._dvr_timeline.SetCurrentTimecode(timecode)
        return item


#   GetName()                                       --> string             # Returns the timeline name.
#   SetName(timelineName)                           --> Bool               # Sets the timeline name if timelineName (string) is unique. Returns True if successful.
#   GetStartFrame()                                 --> int                # Returns the frame number at the start of timeline.
#   GetEndFrame()                                   --> int                # Returns the frame number at the end of timeline.
#   SetStartTimecode(timecode)                      --> Bool               # Set the start timecode of the timeline to the string 'timecode'. Returns true when the change is successful, false otherwise.
#   GetStartTimecode()                              --> string             # Returns the start timecode for the timeline.
#   GetTrackCount(trackType)                        --> int                # Returns the number of tracks for the given track type ("audio", "video" or "subtitle").
#   AddTrack(trackType, subTrackType)               --> Bool               # Adds track of trackType ("video", "subtitle", "audio"). Optional argument subTrackType is used for "audio" trackType.
#                                                                          # subTrackType can be one of {"mono", "stereo", lrc, lcr, lrcs, lcrs, quad, "5.0", "5.0film", "5.1", "5.1film", "7.0", "7.0film" ,"7.1", "7.1film", "adaptive1", ... , "adaptive36"}
#                                                                          # subTrackType defaults to 'mono' if skipped and track type is ‘audio’.
#   AddTrack(trackType, newTrackOptions)            --> Bool               # Adds track of trackType ("video", "subtitle", "audio"). Optional newTrackOptions = {'audioType': same as subTrackType above, 'index': 1 <= index <= GetTrackCount(trackType))
#                                                                          # 'audiotype' defaults to 'mono' if arg skipped and track type is ‘audio’.
#                                                                          # 'index' if skipped (or if value not in bounds) appends track.
#   DeleteTrack(trackType, trackIndex)              --> Bool               # Deletes track of trackType ("video", "subtitle", "audio") and given trackIndex. 1 <= trackIndex <= GetTrackCount(trackType).
#   GetTrackSubType(trackType, trackIndex)          --> string             # Returns an audio track's format.
#                                                                          # the return value is one of {"mono", "stereo", lrc, lcr, lrcs, lcrs, quad, "5.0", "5.0film", "5.1", "5.1film", "7.0", "7.0film" ,"7.1", "7.1film", "adaptive1", ... , "adaptive36"}
#                                                                          # and matches the parameters 'subTrackType' and 'audioType' in timeline.AddTrack.
#                                                                          # returns a blank string for non audio tracks

#   SetTrackEnable(trackType, trackIndex, Bool)     --> Bool               # Enables/Disables track with given trackType and trackIndex
#                                                                          # trackType is one of {"audio", "video", "subtitle"}
#                                                                          # 1 <= trackIndex <= GetTrackCount(trackType).
#   GetIsTrackEnabled(trackType, trackIndex)        --> Bool               # Returns True if track with given trackType and trackIndex is enabled and False otherwise.
#                                                                          # trackType is one of {"audio", "video", "subtitle"}
#                                                                          # 1 <= trackIndex <= GetTrackCount(trackType).
#   SetTrackLock(trackType, trackIndex, Bool)       --> Bool               # Locks/Unlocks track with given trackType and trackIndex
#                                                                          # trackType is one of {"audio", "video", "subtitle"}
#                                                                          # 1 <= trackIndex <= GetTrackCount(trackType).
#   GetIsTrackLocked(trackType, trackIndex)         --> Bool               # Returns True if track with given trackType and trackIndex is locked and False otherwise.
#                                                                          # trackType is one of {"audio", "video", "subtitle"}
#                                                                          # 1 <= trackIndex <= GetTrackCount(trackType).
#   DeleteClips([timelineItems], Bool)              --> Bool               # Deletes specified TimelineItems from the timeline, performing ripple delete if the second argument is True. Second argument is optional (The default for this is False)
#   SetClipsLinked([timelineItems], Bool)           --> Bool               # Links or unlinks the specified TimelineItems depending on second argument.
#   GetItemListInTrack(trackType, index)            --> [items...]         # Returns a list of timeline items on that track (based on trackType and index). 1 <= index <= GetTrackCount(trackType).
#   AddMarker(frameId, color, name, note, duration, --> Bool               # Creates a new marker at given frameId position and with given marker information. 'customData' is optional and helps to attach user specific data to the marker.
#             customData)
#   GetMarkers()                                    --> {markers...}       # Returns a dict (frameId -> {information}) of all markers and dicts with their information.
#                                                                          # Example: a value of {96.0: {'color': 'Green', 'duration': 1.0, 'note': '', 'name': 'Marker 1', 'customData': ''}, ...} indicates a single green marker at timeline offset 96
#   GetMarkerByCustomData(customData)               --> {markers...}       # Returns marker {information} for the first matching marker with specified customData.
#   UpdateMarkerCustomData(frameId, customData)     --> Bool               # Updates customData (string) for the marker at given frameId position. CustomData is not exposed via UI and is useful for scripting developer to attach any user specific data to markers.
#   GetMarkerCustomData(frameId)                    --> string             # Returns customData string for the marker at given frameId position.
#   DeleteMarkersByColor(color)                     --> Bool               # Deletes all timeline markers of the specified color. An "All" argument is supported and deletes all timeline markers.
#   DeleteMarkerAtFrame(frameNum)                   --> Bool               # Deletes the timeline marker at the given frame number.
#   DeleteMarkerByCustomData(customData)            --> Bool               # Delete first matching marker with specified customData.
#   GetCurrentTimecode()                            --> string             # Returns a string timecode representation for the current playhead position, while on Cut, Edit, Color, Fairlight and Deliver pages.
#   SetCurrentTimecode(timecode)                    --> Bool               # Sets current playhead position from input timecode for Cut, Edit, Color, Fairlight and Deliver pages.
#   GetCurrentVideoItem()                           --> item               # Returns the current video timeline item.
#   GetCurrentClipThumbnailImage()                  --> {thumbnailData}    # Returns a dict (keys "width", "height", "format" and "data") with data containing raw thumbnail image data (RGB 8-bit image data encoded in base64 format) for current media in the Color Page.
#                                                                          # An example of how to retrieve and interpret thumbnails is provided in 6_get_current_media_thumbnail.py in the Examples folder.
#   GetTrackName(trackType, trackIndex)             --> string             # Returns the track name for track indicated by trackType ("audio", "video" or "subtitle") and index. 1 <= trackIndex <= GetTrackCount(trackType).
#   SetTrackName(trackType, trackIndex, name)       --> Bool               # Sets the track name (string) for track indicated by trackType ("audio", "video" or "subtitle") and index. 1 <= trackIndex <= GetTrackCount(trackType).
#   DuplicateTimeline(timelineName)                 --> timeline           # Duplicates the timeline and returns the created timeline, with the (optional) timelineName, on success.
#   CreateCompoundClip([timelineItems], {clipInfo}) --> timelineItem       # Creates a compound clip of input timeline items with an optional clipInfo map: {"startTimecode" : "00:00:00:00", "name" : "Compound Clip 1"}. It returns the created timeline item.
#   CreateFusionClip([timelineItems])               --> timelineItem       # Creates a Fusion clip of input timeline items. It returns the created timeline item.
#   ImportIntoTimeline(filePath, {importOptions})   --> Bool               # Imports timeline items from an AAF file and optional importOptions dict into the timeline, with support for the keys:
#                                                                          # "autoImportSourceClipsIntoMediaPool": Bool, specifies if source clips should be imported into media pool, True by default
#                                                                          # "ignoreFileExtensionsWhenMatching": Bool, specifies if file extensions should be ignored when matching, False by default
#                                                                          # "linkToSourceCameraFiles": Bool, specifies if link to source camera files should be enabled, False by default
#                                                                          # "useSizingInfo": Bool, specifies if sizing information should be used, False by default
#                                                                          # "importMultiChannelAudioTracksAsLinkedGroups": Bool, specifies if multi-channel audio tracks should be imported as linked groups, False by default
#                                                                          # "insertAdditionalTracks": Bool, specifies if additional tracks should be inserted, True by default
#                                                                          # "insertWithOffset": string, specifies insert with offset value in timecode format - defaults to "00:00:00:00", applicable if "insertAdditionalTracks" is False
#                                                                          # "sourceClipsPath": string, specifies a filesystem path to search for source clips if the media is inaccessible in their original path and if "ignoreFileExtensionsWhenMatching" is True
#                                                                          # "sourceClipsFolders": string, list of Media Pool folder objects to search for source clips if the media is not present in current folder

#   Export(fileName, exportType, exportSubtype)     --> Bool               # Exports timeline to 'fileName' as per input exportType & exportSubtype format.
#                                                                          # Refer to section "Looking up timeline export properties" for information on the parameters.
#   GetSetting(settingName)                         --> string             # Returns value of timeline setting (indicated by settingName : string). Check the section below for more information.
#   SetSetting(settingName, settingValue)           --> Bool               # Sets timeline setting (indicated by settingName : string) to the value (settingValue : string). Check the section below for more information.
#   InsertGeneratorIntoTimeline(generatorName)      --> TimelineItem       # Inserts a generator (indicated by generatorName : string) into the timeline.
#   InsertFusionGeneratorIntoTimeline(generatorName) --> TimelineItem      # Inserts a Fusion generator (indicated by generatorName : string) into the timeline.
#   InsertFusionCompositionIntoTimeline()           --> TimelineItem       # Inserts a Fusion composition into the timeline.
#   InsertOFXGeneratorIntoTimeline(generatorName)   --> TimelineItem       # Inserts an OFX generator (indicated by generatorName : string) into the timeline.
#   InsertTitleIntoTimeline(titleName)              --> TimelineItem       # Inserts a title (indicated by titleName : string) into the timeline.
#   InsertFusionTitleIntoTimeline(titleName)        --> TimelineItem       # Inserts a Fusion title (indicated by titleName : string) into the timeline.
#   GrabStill()                                     --> galleryStill       # Grabs still from the current video clip. Returns a GalleryStill object.
#   GrabAllStills(stillFrameSource)                 --> [galleryStill]     # Grabs stills from all the clips of the timeline at 'stillFrameSource' (1 - First frame, 2 - Middle frame). Returns the list of GalleryStill objects.
#   GetUniqueId()                                   --> string             # Returns a unique ID for the timeline
#   CreateSubtitlesFromAudio({autoCaptionSettings}) --> Bool               # Creates subtitles from audio for the timeline.
#                                                                          # Takes in optional dictionary {autoCaptionSettings}. Check 'Auto Caption Settings' subsection below for more information.
#                                                                          # Returns True on success, False otherwise.
#   DetectSceneCuts()                               --> Bool               # Detects and makes scene cuts along the timeline. Returns True if successful, False otherwise.
#   ConvertTimelineToStereo()                       --> Bool               # Converts timeline to stereo. Returns True if successful; False otherwise.
#   GetNodeGraph()                                  --> Graph              # Returns the timeline's node graph object.
#   AnalyzeDolbyVision([timelineItems]=[],          --> Bool               # Analyzes Dolby Vision on clips present on the timeline. Returns True if analysis start is successful; False otherwise.
#                      analysisType=NONE)                                  # if [timelineItems] is empty, analysis performed on all items. Else, analysis performed on [timelineItems] only.
#                                                                          # set analysisType to resolve.DLB_BLEND_SHOTS for blend setting
#   GetMediaPoolItem()                              --> MediaPoolItem      # Returns the media pool item corresponding to the timeline
#   GetMarkInOut()                                  --> {mark}             # Returns dict of in/out marks set (keys omitted if not set), example:
#                                                                          # {'video': {'in': 0, 'out': 134}, 'audio': {'in': 0, 'out': 134}}
#   SetMarkInOut(in, out, type="all")               --> Bool               # Sets mark in/out of type "video", "audio" or "all" (default).
#   ClearMarkInOut(type="all")                      --> Bool               # Clears mark in/out of type "video", "audio" or "all" (default).
