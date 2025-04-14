from typing import Any


class DVRMediaPoolItem:
    def __init__(self, media_pool_item: Any, timeline_item: Any):
        self._item = media_pool_item
        self._timeline_item = timeline_item

    @property
    def dvr_media_pool_item(self):
        """Return the DaVinci Resolve MediaPoolItem.\n
            it permits to access to the properties/functions\n
            that are not implemented in this class.
        """
        return self._timeline_item


    @property
    def start_frame(self) -> int | float:
        return self._item.GetSourceStartFrame()


    @property
    def end_frame(self) -> int | float:
        return self._item.GetSourceEndFrame()


    @property
    def name(self) -> str:
        return self._item.GetName()


    @property
    def media_id(self) -> str:
        return self._item.GetMediaId()


    @property
    def filepath(self) -> str:
        return self._item.GetClipProperty("File Path")


    @property
    def filename(self) -> str:
        return self._item.GetClipProperty("Filename")


    @property
    def frame_count(self) -> int:
        return self.end_frame - self.start_frame + 1


    def get_properties(self) -> dict[str, float | int | str]:
        return self._item.GetProperty()


    def get_property(self, name: str) -> Any | dict[str, Any]:
        if not name:
            raise ValueError(f"Not a valid property name: {name}")
        return self._item.GetProperty(name)


    def set_property(self, name: str, value: float | int | str) -> bool:
        if not name:
            raise ValueError(f"Not a valid property name: {name}")
        return self._item.SetProperty(name, value)


# MediaPoolItem
#   GetName()                                       --> string             # Returns the clip name.
#   GetMetadata(metadataType=None)                  --> string|dict        # Returns the metadata value for the key 'metadataType'.
#                                                                          # If no argument is specified, a dict of all set metadata properties is returned.
#   SetMetadata(metadataType, metadataValue)        --> Bool               # Sets the given metadata to metadataValue (string). Returns True if successful.
#   SetMetadata({metadata})                         --> Bool               # Sets the item metadata with specified 'metadata' dict. Returns True if successful.
#   GetThirdPartyMetadata(metadataType=None)        --> string|dict        # Returns the third party metadata value for the key 'metadataType'.
#                                                                          # If no argument is specified, a dict of all set third party metadata properties is returned.
#   SetThirdPartyMetadata(metadataType, metadataValue) --> Bool            # Sets/Add the given third party metadata to metadataValue (string). Returns True if successful.
#   SetThirdPartyMetadata({metadata})               --> Bool               # Sets/Add the item third party metadata with specified 'metadata' dict. Returns True if successful.
#   GetMediaId()                                    --> string             # Returns the unique ID for the MediaPoolItem.
#   AddMarker(frameId, color, name, note, duration, --> Bool               # Creates a new marker at given frameId position and with given marker information. 'customData' is optional and helps to attach user specific data to the marker.
#             customData)
#   GetMarkers()                                    --> {markers...}       # Returns a dict (frameId -> {information}) of all markers and dicts with their information.
#                                                                          # Example of output format: {96.0: {'color': 'Green', 'duration': 1.0, 'note': '', 'name': 'Marker 1', 'customData': ''}, ...}
#                                                                          # In the above example - there is one 'Green' marker at offset 96 (position of the marker)
#   GetMarkerByCustomData(customData)               --> {markers...}       # Returns marker {information} for the first matching marker with specified customData.
#   UpdateMarkerCustomData(frameId, customData)     --> Bool               # Updates customData (string) for the marker at given frameId position. CustomData is not exposed via UI and is useful for scripting developer to attach any user specific data to markers.
#   GetMarkerCustomData(frameId)                    --> string             # Returns customData string for the marker at given frameId position.
#   DeleteMarkersByColor(color)                     --> Bool               # Delete all markers of the specified color from the media pool item. "All" as argument deletes all color markers.
#   DeleteMarkerAtFrame(frameNum)                   --> Bool               # Delete marker at frame number from the media pool item.
#   DeleteMarkerByCustomData(customData)            --> Bool               # Delete first matching marker with specified customData.
#   AddFlag(color)                                  --> Bool               # Adds a flag with given color (string).
#   GetFlagList()                                   --> [colors...]        # Returns a list of flag colors assigned to the item.
#   ClearFlags(color)                               --> Bool               # Clears the flag of the given color if one exists. An "All" argument is supported and clears all flags.
#   GetClipColor()                                  --> string             # Returns the item color as a string.
#   SetClipColor(colorName)                         --> Bool               # Sets the item color based on the colorName (string).
#   ClearClipColor()                                --> Bool               # Clears the item color.
#   GetClipProperty(propertyName=None)              --> string|dict        # Returns the property value for the key 'propertyName'.
#                                                                          # If no argument is specified, a dict of all clip properties is returned. Check the section below for more information.
#   SetClipProperty(propertyName, propertyValue)    --> Bool               # Sets the given property to propertyValue (string). Check the section below for more information.
#   LinkProxyMedia(proxyMediaFilePath)              --> Bool               # Links proxy media located at path specified by arg 'proxyMediaFilePath' with the current clip. 'proxyMediaFilePath' should be absolute clip path.
#   UnlinkProxyMedia()                              --> Bool               # Unlinks any proxy media associated with clip.
#   ReplaceClip(filePath)                           --> Bool               # Replaces the underlying asset and metadata of MediaPoolItem with the specified absolute clip path.
#   GetUniqueId()                                   --> string             # Returns a unique ID for the media pool item
#   TranscribeAudio()                               --> Bool               # Transcribes audio of the MediaPoolItem. Returns True if successful; False otherwise
#   ClearTranscription()                            --> Bool               # Clears audio transcription of the MediaPoolItem. Returns True if successful; False otherwise.
#   GetAudioMapping()                               --> json formatted string # Returns a string with MediaPoolItem's audio mapping information. Check 'Audio Mapping' section below for more information.
#   GetMarkInOut()                                  --> {mark}             # Returns dict of in/out marks set (keys omitted if not set), example:
#                                                                          # {'video': {'in': 0, 'out': 134}, 'audio': {'in': 0, 'out': 134}}
#   SetMarkInOut(in, out, type="all")               --> Bool               # Sets mark in/out of type "video", "audio" or "all" (default).
#   ClearMarkInOut(type="all")                      --> Bool               # Clears mark in/out of type "video", "audio" or "all" (default).


# MediaPool
#   GetRootFolder()                                 --> Folder             # Returns root Folder of Media Pool
#   AddSubFolder(folder, name)                      --> Folder             # Adds new subfolder under specified Folder object with the given name.
#   RefreshFolders()                                --> Bool               # Updates the folders in collaboration mode
#   CreateEmptyTimeline(name)                       --> Timeline           # Adds new timeline with given name.
#   AppendToTimeline(clip1, clip2, ...)             --> [TimelineItem]     # Appends specified MediaPoolItem objects in the current timeline. Returns the list of appended timelineItems.
#   AppendToTimeline([clips])                       --> [TimelineItem]     # Appends specified MediaPoolItem objects in the current timeline. Returns the list of appended timelineItems.
#   AppendToTimeline([{clipInfo}, ...])             --> [TimelineItem]     # Appends list of clipInfos specified as dict of "mediaPoolItem", "startFrame" (float/int), "endFrame" (float/int), (optional) "mediaType" (int; 1 - Video only, 2 - Audio only), "trackIndex" (int) and "recordFrame" (float/int). Returns the list of appended timelineItems.
#   CreateTimelineFromClips(name, clip1, clip2,...) --> Timeline           # Creates new timeline with specified name, and appends the specified MediaPoolItem objects.
#   CreateTimelineFromClips(name, [clips])          --> Timeline           # Creates new timeline with specified name, and appends the specified MediaPoolItem objects.
#   CreateTimelineFromClips(name, [{clipInfo}])     --> Timeline           # Creates new timeline with specified name, appending the list of clipInfos specified as a dict of "mediaPoolItem", "startFrame" (float/int), "endFrame" (float/int), "recordFrame" (float/int).
#   ImportTimelineFromFile(filePath, {importOptions}) --> Timeline         # Creates timeline based on parameters within given file (AAF/EDL/XML/FCPXML/DRT/ADL/OTIO) and optional importOptions dict, with support for the keys:
#                                                                          # "timelineName": string, specifies the name of the timeline to be created. Not valid for DRT import
#                                                                          # "importSourceClips": Bool, specifies whether source clips should be imported, True by default. Not valid for DRT import
#                                                                          # "sourceClipsPath": string, specifies a filesystem path to search for source clips if the media is inaccessible in their original path and if "importSourceClips" is True
#                                                                          # "sourceClipsFolders": List of Media Pool folder objects to search for source clips if the media is not present in current folder and if "importSourceClips" is False. Not valid for DRT import
#                                                                          # "interlaceProcessing": Bool, specifies whether to enable interlace processing on the imported timeline being created. valid only for AAF import
#   DeleteTimelines([timeline])                     --> Bool               # Deletes specified timelines in the media pool.
#   GetCurrentFolder()                              --> Folder             # Returns currently selected Folder.
#   SetCurrentFolder(Folder)                        --> Bool               # Sets current folder by given Folder.
#   DeleteClips([clips])                            --> Bool               # Deletes specified clips or timeline mattes in the media pool
#   ImportFolderFromFile(filePath, sourceClipsPath="") --> Bool            # Returns true if import from given DRB filePath is successful, false otherwise
#                                                                          # sourceClipsPath is a string that specifies a filesystem path to search for source clips if the media is inaccessible in their original path, empty by default
#   DeleteFolders([subfolders])                     --> Bool               # Deletes specified subfolders in the media pool
#   MoveClips([clips], targetFolder)                --> Bool               # Moves specified clips to target folder.
#   MoveFolders([folders], targetFolder)            --> Bool               # Moves specified folders to target folder.
#   GetClipMatteList(MediaPoolItem)                 --> [paths]            # Get mattes for specified MediaPoolItem, as a list of paths to the matte files.
#   GetTimelineMatteList(Folder)                    --> [MediaPoolItems]   # Get mattes in specified Folder, as list of MediaPoolItems.
#   DeleteClipMattes(MediaPoolItem, [paths])        --> Bool               # Delete mattes based on their file paths, for specified MediaPoolItem. Returns True on success.
#   RelinkClips([MediaPoolItem], folderPath)        --> Bool               # Update the folder location of specified media pool clips with the specified folder path.
#   UnlinkClips([MediaPoolItem])                    --> Bool               # Unlink specified media pool clips.
#   ImportMedia([items...])                         --> [MediaPoolItems]   # Imports specified file/folder paths into current Media Pool folder. Input is an array of file/folder paths. Returns a list of the MediaPoolItems created.
#   ImportMedia([{clipInfo}])                       --> [MediaPoolItems]   # Imports file path(s) into current Media Pool folder as specified in list of clipInfo dict. Returns a list of the MediaPoolItems created.
#                                                                          # Each clipInfo gets imported as one MediaPoolItem unless 'Show Individual Frames' is turned on.
#                                                                          # Example: ImportMedia([{"FilePath":"file_%03d.dpx", "StartIndex":1, "EndIndex":100}]) would import clip "file_[001-100].dpx".
#   ExportMetadata(fileName, [clips])               --> Bool               # Exports metadata of specified clips to 'fileName' in CSV format.
#                                                                          # If no clips are specified, all clips from media pool will be used.
#   GetUniqueId()                                   --> string             # Returns a unique ID for the media pool
#   CreateStereoClip(LeftMediaPoolItem,
#                    RightMediaPoolItem)            --> MediaPoolItem      # Takes in two existing media pool items and creates a new 3D stereoscopic media pool entry replacing the input media in the media pool.
#   AutoSyncAudio([MediaPoolItems], {audioSyncSettings}) --> Bool          # Syncs audio for specified [MediaPoolItems] (list). The list must contain a minimum of two MediaPoolItems - at least one video and one audio clip.
#                                                                          # Returns True if successful. Refer to 'Audio Sync Settings' section for details.
#   GetSelectedClips()                              --> [MediaPoolItems]   # Returns the current selected MediaPoolItems
#   SetSelectedClip(MediaPoolItem)                  --> Bool               # Sets the selected MediaPoolItem to the given MediaPoolItem
