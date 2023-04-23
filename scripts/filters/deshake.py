# -*- coding: utf-8 -*-
import cv2
import sys
from pprint import pprint
from copy import deepcopy
from filters.deshakers import (
    CV2_deshaker,
    Skimage_deshaker,
    apply_cv2_transformation,
)
from utils.hash import (
    calculate_hash,
    log_filter
)
from utils.pretty_print import *


def consolidate_stabilize_segments(segments):
    if len(segments) < 2:
        return segments
    return sorted(segments, key=lambda s: s['start'])


def verify_stabilize_segments(shot, segments):
    if len(segments) == 0:
        return True

    # 1st segment
    previous_segment = segments[0]
    if (previous_segment['start'] < shot['start']
        or previous_segment['end'] >= shot['start'] + shot['count']):
        # Segment shall fit in shot
       return False

    if len(segments) == 1:
        # Single segment
        return True

    for segment in segments [1:]:
        if segment['end'] >= shot['start'] + shot['count']:
            # Segment shall fit in shot
            return False

        if previous_segment['start'] <= segment['start'] <= previous_segment['end']:
            # Segment shall not overlap the previous one
            return False

        previous_segment = segment

    return True



def deshake(shot, images:list, image_list:list,
    step_no:int, input_hash:str,
    get_hash:bool=False, do_force:bool=False):

    try:
        if shot['deshake']['enable'] == True:
            print_lightgrey("\t\t\tdeshake is enabled")
        else:
            print_lightgrey("\t\t\tdeshake is disabled")
            return '', images
    except:
        print_lightgrey("\t\t\tdeshake is disabled")
        return '', images

    try:
        segments = deepcopy(shot['deshake']['segments'])
        if len(segments) == 0:
            # Not segment defined
            sys.exit(print_red("error: at least one segment shall be defined"))
            return '', images
    except:
        print_red("\t\t\terror: undefined deshake parameters in shot")
        return '', images

    # Convert to indexes
    for segment in segments:
        segment['count'] = segment['end'] - segment['start'] + 1
        segment['start'] -= shot['start']

    # Patch segments
    # if len(segments) == 2:
    #     # TODO update this
    #     if segments[1]['start'] == segments[0]['start'] + segments[0]['count']:
    #         # segment 1 is adjacent to 0
    #         print_yellow("warning: changed segment 1 ref to end")
    #         segments[0]['ref'] = 'end'
    #         segments[0]['count'] = segments[1]['start'] - segments[0]['start'] + 1
    #         segments[1]['ref'] = 'start'
    #     else:
    #         # some frames between these 2 segments
    #         segments[0]['ref'] = 'end'
    #         segments[1]['ref'] = 'start'


    if len(segments) == 1:
        if segments[0]['ref'] == 'auto':
            # Single segment
            if (segments[0]['start'] == 0
                and (segments[0]['start'] + segments[0]['count']) == shot['count']):
                # segment = shot
                segments[0]['ref'] = 'middle'
            elif segments[0]['start'] == 0:
                # segment starts from the beginning of the shot,
                #  use the last frame of this segment as the first reference
                segments[0]['ref'] = 'end'
            elif segments[0]['start'] + segments[0]['count'] == shot['count']:
                # segment ends to the last frame of the shot,
                #  use the first frame of this segment as the first reference
                segments[0]['ref'] = 'start'
            else:
                # remaining frames before and after!
                #  cannot select a reference
                sys.exit("segment 0 shall start at the beginning or a the end of the shot")
    elif len(segments) > 2:
        print_orange("warning: deshake: %d segments" % len(segments))



    output_images = list()
    filter_str = ""
    start = count = 0
    transformations = {'start': None, 'end': None}
    if segments[0]['start'] == 0:
        inserted_first_frames = True
    else:
        inserted_first_frames = False
    for segment in segments:

        if not get_hash:
            # Append images until start of next segment
            if not inserted_first_frames:
                if segment['start'] > 0:
                    if segment['ref'] == 'start':
                        # No need to apply transformation because ref of this segment is start
                        # i.e. last_transformation=None
                        print_lightcyan("Append %d images before 1st segment" % (segment['start']))
                        for i in range(segment['start']):
                            output_images.append(images[i])
                        inserted_first_frames = True
                    # else:
                    #   ref is middle or end, apply transformation to the first frames
            else:
                if start + count < segment['start']:
                    # Between 2 segments, apply the previous transformation
                    print_lightcyan("Append %d images between 2 segments" % (segment['start'] - (start + count)))
                    for i in range(start + count, segment['start']):
                        output_images.append(apply_cv2_transformation(images[i], transformations['end']))


        # Start, nb of frames, initial transformation
        start = segment['start']
        count = segment['count']
        previous_transformation = transformations['end']

        # Create a filter
        filter_str += "deshake=%s:%d:%d:%s:%s" % (
                segment['alg'], start, count,
                segment['ref'] if segment['ref'] is not None else 'none',
                segment['mode'])

        if not get_hash:
            print("\t\t\t%s" % (filter_str))

        # Deshake
        algorithm = segment['alg']
        if algorithm == 'cv2_deshaker':
            deshaker = CV2_deshaker()
            __filter_str, __output_images, transformations = deshaker.stabilize(
                shot=shot,
                images=images[start:start+count],
                ref=segment['ref'],
                mode=segment['mode'],
                last_transformation=previous_transformation,
                step_no=step_no,
                input_hash=input_hash,
                get_hash=get_hash,
                do_force=do_force)
            del deshaker

        elif algorithm == 'skimage_deshaker':
            deshaker = Skimage_deshaker()
            __output_images, __filter_str = deshaker.stabilize(
                shot=shot,
                images=images[start:start+count],
                image_list=image_list[start:start+count],
                ref=segment['ref'],
                step_no=step_no,
                input_hash=input_hash,
                mode=segment['mode'],
                get_hash=get_hash,
                do_force=do_force)
            del deshaker
        else:
            sys.exit(print_red("error: deshake: algorithm not recognized: %s" % (algorithm)))
        # To remove from this file and create 'stabilize' function
        # elif algorithm == 'ffmpeg':
        #     stabilizer = FFmpeg_stabilizer()
        #     count, __filter_str = stabilizer.stabilize(
        #         image_list=images,
        #         output=output_path,
        #         input_hash=input_hash,
        #         do_log=False)

        # elif algorithm == 'ffmpeg':
        #     # Bad results:
        #     homography = Homography()
        #     count, hash = homography.stabilize(
        #         image_list=image_list,
        #         output=os.path.abspath(shot['paths']['stabilized']),
        #         frame_ref_index=None,
        #         input_hash=hash,
        #         do_log=False)

        if not get_hash:
            if not inserted_first_frames:
                # frames have not been inserted because we were waiting for the first transformation
                if segment['ref'] in 'start' or len(output_images) > 0:
                    sys.exit(print_red("bug: deshake!!! segment[ref]=%s, output images: %d" % (segment['ref'], len(output_images))))

                print_lightcyan("Append %d images at the beggining" % (segment['start']))
                for i in range(segment['start']):
                    output_images.append(apply_cv2_transformation(images[i], transformations['start']))
                inserted_first_frames = True

            print_lightcyan("Append %d stabilized images" % (len(__output_images)))
            output_images.extend(__output_images)


        filter_str += "%s," % (__filter_str)


    # Calculate hash
    filter_str = "%s,%s" % (input_hash, filter_str[:-1])
    if get_hash:
        hash = calculate_hash(filter_str=filter_str)
        return hash, None


    # Append last non-stabilized images
    last_segment_end = segments[-1]['start'] + segments[-1]['count']
    if last_segment_end < shot['count']:
        print_lightcyan("Append %d images after the last segment" % (shot['count'] - last_segment_end))
        for i in range(last_segment_end, shot['count']):
            output_images.append(apply_cv2_transformation(images[i], transformations['end']))


    # Log hash
    hash = log_filter(filter_str, shot['hash_log_file'])
    print("\t\t\tdeshake, output hash= %s" % (hash))

    return hash, output_images
