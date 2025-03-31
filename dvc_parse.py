import os
from pprint import pprint
import sys

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
sys.path.append(dvr_python)

import DaVinciResolveScript as dvr



def get_metadata_dictionary(media_pool_item):
    """
    Try to get all available metadata from a media pool item.

    Args:
        media_pool_item: MediaPoolItem object

    Returns:
        dict: Dictionary of metadata key-value pairs
    """
    if not media_pool_item:
        return {}

    # Common metadata fields to try
    metadata_fields = [
        "File Path", "Resolution", "Frame Rate", "Codec", "Bit Depth",
        "Duration", "Media Type", "Start TC", "End TC", "Reel", "Scene",
        "Shot", "Take", "Camera Type", "Audio Channels", "Sample Rate"
    ]

    metadata = {}
    print(f"Trying to get metadata for: {media_pool_item.GetName()}")

    # Try each metadata field
    for field in metadata_fields:
        try:
            value = media_pool_item.GetMetadata(field)
            if value:
                metadata[field] = value
                print(f"  ✓ {field}: {value}")
            else:
                print(f"  ✗ {field}: No value")
        except Exception as e:
            print(f"  ! Error getting '{field}': {str(e)}")

    return metadata



print("start")
resolve = dvr.scriptapp("Resolve")
print("got it")
print(f"DaVinci Resolve version: {resolve.GetVersionString()}")

project_manager = resolve.GetProjectManager()
# # Get a list of all projects
# projects = project_manager.GetProjects()
# if projects:
#     # Print the names of all available projects
#     print("Available Projects:")
#     for project in projects:
#         print(project)

# Add this to your script


# currentProject = projectManager.GetCurrentProject()
# currentTimeline = currentProject.GetCurrentTimeline()
# offset = currentTimeline.GetStartFrame()
project_name = "ep01_python"
project = project_manager.LoadProject(project_name)
print(f"Project loaded: {project.GetName()}")
# project = project_manager.GetCurrentProject()

if False:
    # Get a simple list of media pool items and their metadata
    media_pool = project.GetMediaPool()
    root_folder = media_pool.GetRootFolder()
    clips = root_folder.GetClipList()

    print("Media Pool Items:")
    for clip in clips[:5]:  # Just test the first 5
        print(f"Clip: {clip.GetName()}")
        try:
            path = clip.GetMetadata("File Path")
            print(f"  File Path: {path}")
            print(f"  id: {clip.GetMediaId()}")

        except Exception as e:
            print(f"  Error: {e}")

if True:
    # timeline = project.GetCurrentTimeline()
    timeline = project.GetTimelineByIndex(1)
    # timeline.SetName("ep01_episode")
    # print(f"got timeline: {timeline.GetName()}")
    # if not timeline.SetTrackName("video", 1, "episode"):
    #     print("failed naming track name")
    print(f"    track count: {timeline.GetTrackCount("video")}")
    print(f"    track name: {timeline.GetTrackName("video", 1)}")

    # media_pool = project.GetMediaPool()
    # root_folder = media_pool.GetRootFolder()
    # clip_list = root_folder.GetClipList()
    # first_clip_name = clip_list[0].GetName()
    # print(clip_list[0].GetMetadata("Codec"))
    track_index = 1
    track_items = timeline.GetItemListInTrack("video", track_index)
    track_clips = []
    for item in track_items[:5]:
        clip_info = {
            "name": item.GetName(),
            "start_frame": item.GetStart(),
            "end_frame": item.GetEnd(),
            "duration": item.GetDuration(),
        }

        # Try to get the media pool item (original clip)
        media_pool_item = item.GetMediaPoolItem()
        if media_pool_item:
            # print(f"  ✓ Found media pool item: {media_pool_item.GetName()}")
            clip_info["media_pool_item"] = {
                "name": media_pool_item.GetName(),
                # "metadata": get_metadata_dictionary(media_pool_item),
                "media_id": media_pool_item.GetMediaId(),
                "filepath": media_pool_item.GetClipProperty('File Path')
            }
        # print(f"Timeline item type: {type(item).__name__}")
        # print(f"Has fusion comp: {item.GetFusionCompCount() > 0}")
        #     clip_info["media_pool_item"] = {
        #         "name": media_pool_item.GetName(),
        #         "metadata": {
        #             "File Path": media_pool_item.GetMetadata("File Path"),
        #             "Resolution": media_pool_item.GetMetadata("Resolution"),
        #             "Frame Rate": media_pool_item.GetMetadata("Frame Rate"),
        #             "Codec": media_pool_item.GetMetadata("Codec")
        #         }
        #     }

        #     media_pool_item = item.GetMediaPoolItem()
        #     if media_pool_item:
        #         print(f"  ✓ Found media pool item: {media_pool_item.GetName()}")
        #         clip_info["media_pool_item"] = {
        #             "name": media_pool_item.GetName(),
        #             "metadata": get_metadata_dictionary(media_pool_item)
        #         }
        #     else:
        #         print(f"  ✗ No media pool item found (might be a compound clip or generator)")
        # except Exception as e:
        #     print(f"  ! Error getting media pool item: {str(e)}")


        track_clips.append(clip_info)
    pprint(track_clips)
        # all_clips[f"V{track_index}"] = track_clips

        # # Check if the clip is valid
        # if clip:

        #     # Get clip name
        #     clip_name = clip.GetName()
        #     print(f"  Clip Name: {clip_name}")

        #     # Get clip start time
        #     start_time = clip.GetStart()
        #     print(f"  Start Time: {start_time}")

        #     # Get clip end time
        #     end_time = clip.GetEnd()
        #     print(f"  End Time: {end_time}")

        #     # Get clip duration
        #     duration = clip.GetDuration()
        #     print(f"  Duration: {duration}")

        #     # Check if the clip has a media source (for file-based clips)
        #     try:
        #         media_source = clip.GetMediaSource()
        #         if media_source:
        #             file_path = media_source.GetFilePath()
        #             print(f"  File Path: {file_path}")
        #         else:
        #             print("  This clip has no media source (possibly an effect or title).")
        #     except Exception as e:
        #         print(f"  Error accessing media source: {e}")
        # else:
        #     print(f"Clip not found in Track {track_index}.")

    # print(f"Clips: {project.GetName()}")
    # track = timeline.GetItemListInTrack("video", 1)
    # for clip in track:
    #     clip_name = clip.GetName()
    #     print(f"   {clip_name}: {clip.GetDuration()}")
    #     # Get and print basic clip information
    #     print(f"Clip Name: {clip.GetName()}")
    #     print(f"  Start Time: {clip.GetStart()}")
    #     print(f"  End Time: {clip.GetEnd()}")
    #     print(f"  Duration: {clip.GetDuration()}")

    #     media_source = clip.GetMediaSource()
    #     file_path = media_source.GetFilePath()
    #     print(f"  File Path: {file_path}")

        # in_clip = clip.GetMediaId()
        # pprint(clip.GetMediaId())
        # print(f"       {in_clip.GetMetadata("Codec")}")
        # pprint(in_clip.GetMetadata())
        # # print(clip.GetMediaSource().GetFilePath())

    # all_clips = []
    # media_pool = project.GetMediaPool()
    # bins = media_pool.GetRootFolder().GetSubFolders()
    # print("got bins")
    # for bin in bins:
    #     clips = bin.GetClips()
    #     all_clips.extend(clips.values())

    # for clip in all_clips:
    #     print(clip.GetName())

    # for track_index in range(1, timeline.GetTrackCount("video") + 1):
    #     track = timeline.GetTrackItems("video", track_index)
    #     for clip in track:
    #         print(clip.GetName())


# project_manager.CloseProject(project)
print("done")
# import DaVinciResolveScript as dvr_script

# # Connect to DaVinci Resolve
# resolve = dvr_script.scriptapp("Resolve")

# # Get the current project
# project_manager = resolve.GetProjectManager()
# project = project_manager.GetCurrentProject()

# # Access the media pool
# media_pool = project.GetMediaPool()

# # Get the list of all clips in the media pool (for all bins)
# def get_all_clips():
#     all_clips = []

#     # Retrieve all bins in the media pool
#     bins = media_pool.GetRootFolder().GetSubFolders()

#     # Traverse through all bins to collect clips
#     for bin in bins:
#         clips = bin.GetClips()
#         all_clips.extend(clips.values())

#     return all_clips
