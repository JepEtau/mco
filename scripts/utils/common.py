# -*- coding: utf-8 -*-
import sys
from pprint import pprint
import subprocess
import re

K_GENERIQUES = [
    'g_debut',
    'g_fin',
    'g_asuivre',
    'g_reportage',
]

K_PARTS = [
    'precedemment',
    'episode',
    'g_asuivre',
    'asuivre',
    'g_reportage',
    'reportage',
]

K_ALL_PARTS = [
    'g_debut',
    'precedemment',
    'episode',
    'g_asuivre',
    'asuivre',
    'g_reportage',
    'reportage',
    'g_fin',
]

K_NON_GENERIQUE_PARTS = [
    'precedemment',
    'episode',
    'asuivre',
    'reportage',
]

K_AUDIO_PARTS = K_PARTS


# order for processing: generique, then from shortest to longest
K_ALL_PARTS_ORDERED = [
    'g_debut',
    'g_fin',
    'g_asuivre',
    'g_reportage',
    'precedemment',
    'asuivre',
    'reportage',
    'episode',
]


FPS = 25.0




def nested_dict_set(d:dict, o:object, *keys):
    nested_d = d
    for k in keys:
        if k == keys[-1]:
            break
        if k not in nested_d.keys():
            nested_d[k] = dict()
        nested_d = nested_d[k]
    nested_d[k] = o


def nested_dict_get(d:dict, *keys):
    # Return the value
    nested_d = d
    for k in keys[:-1]:
        if k == keys[-1]:
            break
        try: nested_d = nested_d[k]
        except: return None
    try: return nested_d[k]
    except: return None

def nested_dict_clean(d:dict):
    for k in d.keys():
        if isinstance(d[k], dict):
            nested_dict_clean(d[k])
        else:
            del d[k]

def recursive_update(out_dict:dict, in_dict:dict):
    for k in in_dict.keys():
        if isinstance(in_dict[k], dict):
            if k not in out_dict.keys():
                out_dict[k] = dict()
            recursive_update(out_dict=out_dict[k], in_dict=in_dict[k])
        else:
            out_dict[k] = in_dict[k]


def delete_items(d:dict, key):
    if key in d.keys():
        del d[key]
    for k, v in d.items():
        if isinstance(v, dict):
            item = delete_items(v, key)



def pprint_dict(db_video, first_indent:int=0, ignore=list()):
    if isinstance(ignore, list):
        ignore_list = ignore
    else:
        ignore_list = [ignore]

    first_indent_str = " ".ljust(first_indent) if first_indent > 0 else ""
    indent = "    "
    print("%s{" % (first_indent_str))
    for k_item_0, item_0 in db_video.items():
        print("%s\'%s\': " % (first_indent_str+indent, k_item_0), end='')
        if k_item_0 in ignore_list:
            print("%s..." % (first_indent_str+indent))
            continue

        if isinstance(item_0, dict):
            # print for small dict
            if len(item_0.keys()) < 4:
                print(item_0)

            else:
                print('{')
                for k_item_1, item_1 in item_0.items():

                    print("%s\'%s\':" % (first_indent_str+2*indent, k_item_1), end='')
                    if isinstance(item_1, list):
                        print(" [")
                    elif isinstance(item_1, dict):
                        print(" {")
                    else:
                        print("")

                    if k_item_1 in ignore_list:
                        print("%s..." % (first_indent_str+3*indent))
                    else:
                        if k_item_1 == 'shots':
                            for shot in item_1:
                                print("%s" % (first_indent_str+3*indent), shot)

                    if isinstance(item_1, list):
                        print("%s]" % (first_indent_str+2*indent))
                    elif isinstance(item_1, dict):
                        print("%s}" % (first_indent_str+2*indent))

                    if k_item_1 in ignore_list:
                        print("%s..." % (first_indent_str+2*indent))
                    else:
                        print("%s\'%s\':" % (first_indent_str+2*indent, k_item_1), item_1)

                print("%s}" % (first_indent_str+indent))
        else:
            print(item_0)
    print("%s}" % (first_indent_str))


def pprint_video(db_video, first_indent:int=0, ignore=list()):
    if isinstance(ignore, list):
        ignore_list = ignore
    else:
        ignore_list = [ignore]

    first_indent_str = " ".ljust(first_indent) if first_indent > 0 else ""
    indent = "    "
    print("%s{" % (first_indent_str))
    for k_item_0, item_0 in db_video.items():
        print("%s\'%s\': " % (first_indent_str+indent, k_item_0), end='')
        if k_item_0 in ignore_list:
            continue

        if isinstance(item_0, dict):
            # print for small dict
            if len(item_0.keys()) < 4:
                print(item_0)

            else:
                print('{')
                for k_item_1, item_1 in item_0.items():

                    if k_item_1 in ignore_list:
                        print("%s\'%s\': " % (first_indent_str+2*indent, k_item_1), end='')
                        if isinstance(item_1, list):
                            print("[...]")
                        elif isinstance(item_1, dict):
                            print("{...}")
                        else:
                            print("")
                        continue

                    if k_item_1 == 'segments':
                        print("%s\'%s\':" % (first_indent_str+2*indent, k_item_1), end='')
                        if isinstance(item_1, list):
                            print(" [")
                        elif isinstance(item_1, dict):
                            print(" {")
                        else:
                            print("")

                        for segment in item_1:
                            print("%s" % (first_indent_str+3*indent), segment)

                        if isinstance(item_1, list):
                            print("%s]" % (first_indent_str+2*indent))
                        elif isinstance(item_1, dict):
                            print("%s}" % (first_indent_str+2*indent))

                        continue

                    if k_item_1 == 'shots':
                        print("#########################################")
                        print("%s\'%s\':" % (first_indent_str+2*indent, k_item_1), end='')
                        if isinstance(item_1, list):
                            print(" [")
                            item_1_count = len(item_1)
                            if item_1_count> 0:
                                for shot in item_1:
                                    print("%s" % (first_indent_str+3*indent), shot)
                            else:
                                print("")

                        elif isinstance(item_1, dict):
                            print(" {")
                            item_1_count = len(item_1.keys())
                            if item_1_count> 0:
                                for k_shot, shot in item_1.items():
                                    print("%s" % (first_indent_str+3*indent), shot)
                            else:
                                print("")

                        else:
                            print("")
                            item_1_count = 0



                        if isinstance(item_1, list):
                            print("%s]" % (first_indent_str+2*indent))
                        elif isinstance(item_1, dict):
                            print("%s}" % (first_indent_str+2*indent))

                        continue

                    print("%s\'%s\':" % (first_indent_str+2*indent, k_item_1), item_1)

                print("%s}" % (first_indent_str+indent))

        else:
            print(item_0)
    print("%s}" % (first_indent_str))


def pprint_audio(db_audio, first_indent:int=0, ignore=list()):
    if isinstance(ignore, list):
        ignore_list = ignore
    else:
        ignore_list = [ignore]

    first_indent_str = " ".ljust(first_indent) if first_indent > 0 else ""
    indent = "    "
    print("%s{" % (first_indent_str))
    for k_item_0, item_0 in db_audio.items():
        print("%s\'%s\': " % (first_indent_str+indent, k_item_0), end='')
        if k_item_0 in ignore_list:
            continue

        if isinstance(item_0, dict):
            # print for small dict
            if len(item_0.keys()) < 4:
                print(item_0)

            else:
                print('{')
                for k_item_1, item_1 in item_0.items():

                    if k_item_1 in ignore_list:
                        continue

                    if k_item_1 == 'segments':
                        print("%s\'%s\':" % (first_indent_str+2*indent, k_item_1), end='')
                        if isinstance(item_1, list):
                            print(" [")
                        elif isinstance(item_1, dict):
                            print(" {")
                        else:
                            print("")

                        for segment in item_1:
                            print("%s" % (first_indent_str+3*indent), segment)

                        if isinstance(item_1, list):
                            print("%s]" % (first_indent_str+2*indent))
                        elif isinstance(item_1, dict):
                            print("%s}" % (first_indent_str+2*indent))

                        continue

                    print("%s\'%s\':" % (first_indent_str+2*indent, k_item_1), item_1)

                print("%s}" % (first_indent_str+indent))
        else:
            print(item_0)
    print("%s}" % (first_indent_str))








def get_database_size(obj, seen=None):
    """Recursively finds size of objects"""
    size = sys.getsizeof(obj)
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    # Important mark as seen *before* entering recursion to gracefully handle
    # self-referential objects
    seen.add(obj_id)
    if isinstance(obj, dict):
        size += sum([get_database_size(v, seen) for v in obj.values()])
        size += sum([get_database_size(k, seen) for k in obj.keys()])
    elif hasattr(obj, '__dict__'):
        size += get_database_size(obj.__dict__, seen)
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
        size += sum([get_database_size(i, seen) for i in obj])
    return size


def get_dimensions_from_crop_values(width, height, crop) -> list:
    c_t, c_b, c_l, c_r = crop
    c_w = width - (c_l + c_r)
    c_h = height - (c_t + c_b)
    return [c_t, c_b, c_l, c_r, c_w, c_h]


def set_edition_layer(database, edition:str, layer='fgd'):
    # Set the edition that will be used as a background or foreground
    if 'editions' not in database.keys():
        database['editions'] = dict()
    database['editions'][layer] = edition

def get_edition_layer(database, edition:str):
    # Returns the layer for this edition
    for layer in ['bgd', 'fgd']:
        if database['editions'][layer] == edition:
            return layer
    return ''

def get_layer_edition(database, layer:str):
    # Returns the edition used by the specified layer
    if layer in database['editions'].keys():
        return database['editions'][layer]
    return ''


def get_frame_no_from_filepath(filepath):
    result = re.search(re.compile(".*_(\d{5,6})__([\w_\d]+)__(\d{3})\.(\w{3})"), filepath)
    if result:
        return int(result.group(1))
    return 0
    # sys.exit("get_frame_no_from_filepath: cannot find frame no. from [%s]" % (filepath))


def get_k_part_from_frame_no(db, k_ed:str, k_ep:str, frame_no:int):
    # Returns the part from the frame no.:
    db_ep = db[k_ep][k_ed]
    for k_p in K_ALL_PARTS:
        # print("%s.get_k_part_from_frame_no: %d in %s:%s:%s ?" % (__name__, frame_no, k_ed, k_ep, k_p))
        # pprint(db_ep[k_p]['video'])
        if 'start' not in db_ep[k_p]['video'].keys():
            # print("warning: todo: missing part in database: %s:%s:%s" % (k_ed, k_ep, k_p))
            continue
        start = db_ep[k_p]['video']['start']
        count = db_ep[k_p]['video']['count']
        if start <= frame_no < (start + count):
            return k_p
    # sys.exit("error: %s.get_k_part_from_frame_no: part not found for frame %d in %s:%s" % (__name__, frame_no, k_ed, k_ep))
    return ''


def get_shot_from_frame(db, edition:str, frame:dict, k_part:str=''):
    # Returns the shot from a frame
    # the section [parts] must be defined in each ep##.ini file if the
    # argument 'part' is not passed

    # TODO: use the edition that is defined as a reference
    k_episode = frame['k_ep']
    if k_part == '':
        # Argument 'part' is not passed
        k_part = get_k_part_from_frame_no(db, edition, k_episode, frame['no'])
        if k_part == '':
            sys.exit("part is not found from frame no. %d" % frame['no'])

    db_video = db[k_episode][edition][k_part]['video']
    if 'shots' not in db_video.keys():
        # print("USE REFERENCE")
        db_video = db[k_episode][db['editions']['fgd']][k_part]['video']
        frame_no = frame['ref']
    else:
        frame_no = frame['no']

    if k_part in ['precedemment', 'asuivre']:
        # 'precedemment' and 'asuivre' may use another episode, sot use this
        # other episode to find the shot no.
        for s in db_video['shots']:
            if frame['ep'] == s['new_episode']:
                if s['new_start'] <= frame_no < s['new_start'] + s['new_framesCount']:
                    return s
            else:
                if s['original_start'] <= frame_no < s['original_start'] + s['original_framesCount']:
                    return s
    else:
        for s in db_video['shots']:
            if s['start'] <= frame_no < s['start'] + s['count']:
                return s

    return None



def get_shot_no_from_frame_no(db_video, frame_no:int, k_part='') -> int:
    """This function returns the shot no. from a frame no.

    Args:
        db_video: structure that contains shots
        k_part: tkey of the part to find the frame no.
        frame_no: the frame no. to find

    Returns:
        the shot no. Returns None if not found

    """
    # print("++++ %s.get_shot_no_from_frame_no" % (__name__))
    # print(k_part)
    # pprint(db_video)

    if 'shots' not in db_video.keys():
        # This db_video has no shots: usefull when there is
        # no shot in a part, i.e. this is a part (e.g. 'reportage')
        return 0

    shots = db_video['shots']
    # pprint(shots)
    for shot in shots:
        if frame_no >= shot['start'] and frame_no < (shot['start'] + shot['count']):
            # print("%d in [%d; %d]" % (frame_no, shot['start'], shot['start'] + shot['count']))
            if shots[shot['no']]['no'] == shot['no']:
                return shot['no']
            else:
                print("Error: get_shot_from_frame_no, shotsNo!=no")
                return None
    print("Error: %s.get_shot_no_from_frame_no: not found for frame %d" % (__name__, frame_no))
    # pprint(db_video)
    return None



def get_shot_from_frame_no(db_ep_or_g, frame_no:int, k_part='') -> dict:
    """This function returns the shot structure from a frame no.

    Args:
        db_ep_or_g: database for this ep or generique
        k_part: key of the part to find the frame no. or k_edition when used for a generique
        frame_no: the frame no. to find

    Returns:
        the shot structure. Returns None if not found

    """
    # print("get_shot_from_frame_no: %d, k_part=[%s]" % (frame_no, k_part))
    if k_part == '':
        # Get part from frame_no
        is_part_found = False
        for k_p in K_PARTS:
            db_video = db_ep_or_g[k_p]['video']
            print('%s' % (k_p))
            print("%d->%d" % (db_video['start'], (db_video['start']+db_video['count'])))
            if frame_no >= db_video['start'] and frame_no < (db_video['start']+db_video['count']):
                is_part_found = True
                break

        if not is_part_found:
            sys.exit("get_shot_from_frame_no: part is not found for frame no. %d" % (frame_no))
        k_part = k_p

    if k_part in K_GENERIQUES:
        shots = db_ep_or_g['video']['shots']
    else:
        shots = db_ep_or_g[k_part]['video']['shots']
    # pprint(shots)
    for shot in shots:
        if frame_no >= shot['start'] and frame_no < (shot['start'] + shot['count']):
            # print("%d in [%d; %d]" % (frame_no, shot['start'], shot['start'] + shot['count']))
            if shots[shot['no']]['no'] == shot['no']:
                # Verify that the shot no. defined in the structure is equal to the index in the array
                return shot
            else:
                print("Error: get_shot_from_frame_no, shotsNo!=no")
                return None
    print("Warning: %s:get_shot_from_frame_no: not found, frame no. %d, continue" % (__name__, frame_no))
    return None



def get_shot_from_frame_no_new(db, frame_no:int, k_ed, k_ep, k_part) -> dict:
    """This function returns the shot structure from a frame no.

    Args:
        db: global database
        frame_no: the frame no. to find
        k_ed: edition
        k_ep_or_g: episode or generique
        k_part: key of the part to find the frame no. or k_edition when used for a generique

    Returns:
        the shot structure. Returns None if not found

    """
    # Use the ed:ep defined as reference to calculate offsets

    if k_part in K_GENERIQUES:
        # TODO: replace this but the edition set as reference once the shots
        # are defined in g_fin, g_asuivre for edition k
        k_ed_ref = db[k_part]['target']['video']['src']['k_ed']
        k_ep_ref = db[k_part]['target']['video']['src']['k_ep']
        print("%s: use %s:%s as reference to calculate new frame no." % (k_part, k_ed_ref, k_ep_ref))
    else:
        k_ed_ref = db['editions']['k_ed_ref']
        k_ep_ref = k_ep
    # print("get_shot_from_frame_no_new: %s:%s:%s" % (k_ed_ref, k_ep_ref, k_part))

    shots = db[k_ep_ref][k_ed_ref][k_part]['video']['shots']
    for shot in shots:
        # print("%d in [%d; %d] ?" % (frame_no, shot['start'], shot['start'] + shot['count']))
        if shot['start'] <= frame_no < (shot['start'] + shot['count']):
            return shot
    print("\nWarning: %s:get_shot_from_frame_no_new: not found, frame no. %d in %s:%s:%s continue" % (__name__, frame_no, k_ed, k_ep, k_part))
    pprint_video(db[k_ep_ref][k_ed_ref][k_part]['video'], ignore='')
    print("-----------------------------------------------")
    # pprint(db[k_ep_ref][k_ed][k_part]['video']['shots'])
    sys.exit()

    return None




def create_pipe_in(command, process_cfg, mode=''):
    if mode == 'debug':
        print("\n*** FFMPEG command ***")
        for elem in command:
            if elem.startswith("-"):
                print("\n\t", end="")
            else:
                print("\t", end="")
            print(elem, end="")
        print("\n")

    if sys.platform == 'win32':
        pipe_in = subprocess.Popen(command,
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=False,
                            env=process_cfg['osEnvironment'],
                            startupinfo=process_cfg['startupInfo'],
                            )
    elif sys.platform == 'linux':
        pipe_in = subprocess.Popen(command,
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=False,
                            env=process_cfg['osEnvironment'],
                            startupinfo=process_cfg['startupInfo'],
                            bufsize=10**8
                            )
                            # cwd=self._buildPath,
    return pipe_in


