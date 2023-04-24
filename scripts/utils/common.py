# -*- coding: utf-8 -*-
import sys
from pprint import pprint
import re

# from utils.pretty_print import *


FPS = 25.0


K_GENERIQUES = [
    'g_debut',
    'g_fin',
    'g_asuivre',
    'g_reportage',
]

K_PARTS_ORDERED = [
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

K_AUDIO_PARTS = K_PARTS_ORDERED
K_PARTS = K_PARTS_ORDERED

# order for processing: generique, then from shortest to longest
K_ALL_PARTS_ORDERED = [
    'g_debut',
    'precedemment',
    'episode',
    'g_asuivre',
    'asuivre',
    'g_reportage',
    'reportage',
    'g_fin',
]



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



def get_k_part_from_frame_no(db, k_ed:str, k_ep:str, frame_no:int):
    verbose = False

    # Returns the part from the frame no.:
    db_ep = db[k_ep]['video'][k_ed]
    for k_p in K_ALL_PARTS:
        if verbose:
            print(f"\tget_k_part_from_frame_no: {frame_no} in {k_ed}:{k_ep}:{k_p}")
        # pprint(db_ep[k_p])
        try:
            if 'start' not in db_ep[k_p].keys():
                print("warning: todo: missing part in database: %s:%s:%s" % (k_ed, k_ep, k_p))
                continue
        except:
            print(f"\twarning: get_k_part_from_frame_no: part not found for frame {frame_no} in %s:%s:%s" % (k_ed, k_ep, k_p))
            return ''
        start = db_ep[k_p]['start']
        count = db_ep[k_p]['count']
        if start <= frame_no < (start + count):
            return k_p
    print("\twarning: %s.get_k_part_from_frame_no: part not found for frame %d in %s:%s" % (__name__, frame_no, k_ed, k_ep))
    return ''





