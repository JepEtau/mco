from pprint import pprint
import sys
from utils.p_print import *
from utils.mco_types import Scene
from parsers import db, Filter


def do_watermark(scene: Scene) -> bool:
    return bool('watermark' in scene['filters'][scene['task'].name].sequence)



def get_filters(scene: Scene) -> list[Filter]:
    verbose = False
    k_ed = scene['k_ed']
    k_ep = scene['k_ep']
    k_ch = scene['k_ch']

    if verbose:
        print(lightgreen(f"get filters from scene: {k_ed}:{k_ep}:{k_ch}, no. {scene['no']:03}, start: {scene['start']}"))

    if scene['filters_id'] == 'default':
        if verbose:
            print(lightgrey(f"\tdefault filter"))
            # pprint(db[k_ep]['video'][k_ed][k_ch]['filters'])

        # This scene uses default filters. Use the one defined in the part
        if (
            'filters' not in db[k_ep]['video'][k_ed][k_ch]
            and scene['task'].name != 'initial'
        ):
            sys.exit(print(red(f"Error: {k_ed}:{k_ep}:{k_ch}: no available filters")))

        try:
            filters = db[k_ep]['video'][k_ed][k_ch]['filters']['default']
        except:
            if scene['task'].name == 'initial':
                return {}
            else:
                print(red(f"Error: default filter is not defined but required by {k_ed}:{k_ep}:{k_ch}, no. {scene['no']:03}"))
                pprint(scene)
                sys.exit()

    elif isinstance(scene['filters_id'], str):
        if verbose:
            print(lightgrey(f"\tcustom filter: {scene['filters']}"))

        # This scene uses a custom filter defined in the 'filters' struct in this part
        try:
            filters = db[k_ep]['video'][k_ed][k_ch]['filters'][scene['filters_id']]
        except:
            print(red(f"Error: {k_ed}:{k_ep}:{k_ch}, no. {scene['no']:03}, filter {scene['filters']} not found"))
            print(red(f"\tdefined filters: {list(db[k_ep]['video'][k_ed][k_ch]['filters'].keys())}"))
            print(orange(f"\tfallback: using default"))
            filters = db[k_ep]['video'][k_ed][k_ch]['filters']['default']
    else:
        # This scene may default filters, but to be validated
        print(red(f"Error: no filters defined for {k_ed}:{k_ep}:{k_ch}, no. {scene['no']:03}"))
        sys.exit()

    return filters

