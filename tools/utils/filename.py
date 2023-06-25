# -*- coding: utf-8 -*-

import os
import os.path
import re
import sys


from pprint import pprint

from img_toolbox.utils import FILTER_BASE_NO


def filter_filenames_by(filenames:list, k_edition:str='', k_step:str='', filter_id:int=-1, verbose=False):
    if verbose: print("%s.filter_filenames_by: %s, %s, %d" % (__name__, k_edition, k_step, filter_id))

    # pprint(filenames)
    new_filenames = list()
    for f in filenames:
        if verbose: print(f, end='')
        result = re.match(re.compile("ep(\d{2})_(\d{5,6})__([\w_\d]+)__(\d{3})\.(\w{3})"), f)
        if result is not None:
            result_ep = '%02d' % int(result.group(1))
            result_edition = result.group(3)
            result_filter_id = int(result.group(4))
        else:
            continue

        do_append = True

        if verbose: print(" %s:%s filter_id=%d" % (result_edition, result_ep, result_filter_id), end='')
        # Filter by filter id
        if filter_id != -1 and result_filter_id != filter_id:
            do_append = do_append and False

        # Filter by filter step
        if k_step != '' and (100 * int(result_filter_id / 100)) != FILTER_BASE_NO[k_step]:
            do_append = do_append and False

        # Filter by edition
        if k_edition !='' and result_edition != k_edition:
            do_append = do_append and False

        if do_append:
            if verbose: print(" -> append", end='')
            new_filenames.append(f)

        if verbose: print(".")

    new_filenames.sort()
    return new_filenames