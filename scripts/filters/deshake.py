# -*- coding: utf-8 -*-
import sys
from pprint import pprint
from copy import deepcopy
from filters.deshakers import (
    CV2_deshaker,
    Skimage_deshaker,
)

from utils.hash import (
    log_filter
)
from utils.pretty_print import *



def deshake(shot, images:list, add_border:bool, step_no:int, input_hash:str,
    get_hash:bool=False, do_force:bool=False):

    try:
        segments = deepcopy(shot['deshake'])
        if len(segments) == 0:
            # Not segment defined
            sys.exit(print_red("error: at least one segment shall be defined"))
            return 0, input_hash
    except:
        sys.exit(print_red("error: undefined deshake parameters in shot"))

    # Convert to indexes
    for segment in segments:
        segment['count'] = segment['end'] - segment['start']
        # segment['start'] -= shot['start']

    # Patch segments
    if len(segments) == 2:
        # TODO update this
        if segments[1]['start'] == segments[0]['start'] + segments[0]['count']:
            # segment 1 is adjacent to 0
            segments[0]['ref'] = 'end'
            segments[0]['count'] = segments[1]['start'] - segments[0]['start'] + 1
            segments[1]['ref'] = 'start'
        else:
            # some frames between these 2 segments
            segments[0]['ref'] = 'end'
            segments[1]['ref'] = 'start'

    elif len(segments) == 1:
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
        sys.exit("deshake: more than 2 segments is not supported")


    output_images = list()
    filter_str = ""
    for segment in segments:
        # Start, nb of frames
        start = segment['start']
        count = segment['count']

        # Create a filter
        filter_str += "deshake=%s:%d:%d:%s:%s=" % (
                segment['alg'], start, count,
                segment['ref'] if segment['ref'] is not None else 'none',
                segment['directions'])

        if not get_hash:
            print("\t\t\t%s" % (filter_str))

        # Deshake
        algorithm = segment['alg']
        if algorithm == 'cv2_deshaker':
            deshaker = CV2_deshaker(add_border=add_border)
            __output_images, _filter_str = deshaker.stabilize(
                shot=shot,
                images=images[start:start+count],
                ref=segment['ref'],
                step_no=step_no,
                input_hash=input_hash,
                directions=segment['directions'],
                get_hash=get_hash,
                do_force=do_force,
                do_log=False)
            del deshaker
        elif algorithm == 'skimage_deshaker':
            deshaker = Skimage_deshaker(add_border)
            __output_images, _filter_str = deshaker.stabilize(
                shot=shot,
                images=images[start:start+count],
                ref=segment['ref'],
                step_no=step_no,
                input_hash=input_hash,
                directions=segment['directions'],
                get_hash=get_hash,
                do_force=do_force,
                do_log=False)
            del deshaker
        else:
            sys.exit(print_red("error: deshake: algorithm not recognized: %s" % (algorithm)))
        # To remove from this file and create 'stabilize' function
        # elif algorithm == 'ffmpeg':
        #     stabilizer = FFmpeg_stabilizer()
        #     count, _filter_str = stabilizer.stabilize(
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
        if __output_images is not None:
            # Empty array or get_hash
            if len(segments) > 1 and segment['ref'] == 'end':
                output_images.extend(__output_images[:-1])
            else:
                output_images.extend(__output_images)

        filter_str += "%s," % (_filter_str)

    filter_str = filter_str[:-1]

    # Log hash
    hash = log_filter("%s,%s" % (input_hash, filter_str), shot['hash_log_file'])
    if not get_hash:
        print("\t\t\tdeshake, output hash= %s" % (hash))

    return hash, output_images
