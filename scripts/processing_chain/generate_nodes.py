# -*- coding: utf-8 -*-
from copy import deepcopy
import sys
sys.path.append('scripts')
import re
from utils.pretty_print import *
import numpy as np

# Dirty, dirty, dirty for quick evaluation puprose


# Create nodes from the filter list
# def generate_nodes_from_list(filter_list:list[dict]):

#     for f in filter_list:
#         if node['id'] is None:
#             print(p_yellow("Not a filter with nodes"))




#         node['in'] = list()

#         if node['str'].startswith('in='):
#             # depenancies
#             node['dep'].append()




def set_input_dependencies(nodes:dict):
    node_id_regex = "([a-z0-9-]+)[,:]"

    for node in nodes.values():
        node['in'] = list()

        if node['type'] in ['avisynth',
                        'scunet',
                        'real_cugan',
                        'pytorch',
                        'ffmpeg']:
            # single input
            result = re.search(re.compile(f"in={node_id_regex}"), node['str'])
            if result is not None:
                node['in'].append(result.group(1))

        elif node['type'] == 'python':
            result = re.search(re.compile(f"in={node_id_regex}"), node['str'])
            if result is not None:
                node['in'].append(result.group(1))

            result = re.search(re.compile(f"ref={node_id_regex}"), node['str'])
            if result is not None:
                node['in'].append(result.group(1))

            result = re.search(re.compile(f"lower={node_id_regex}"), node['str'])
            if result is not None:
                node['in'].append(result.group(1))

            result = re.search(re.compile(f"top={node_id_regex}"), node['str'])
            if result is not None:
                node['in'].append(result.group(1))

        if len(node['in']) == 0 and node['__prev_node_id'] is not None:
            node['in'] = [node['__prev_node_id']]

    # clean
    for node in nodes.values():
        del node['__prev_node_id']



def set_output_dependencies(nodes:dict):
    for node in nodes.values():
        node['out'] = list()
    for node in nodes.values():
        for node_in in node['in']:
            nodes[node_in]['out'].append(node['id'])


def verify_correctness(nodes:dict) -> bool:
    for node in nodes.values():
        if len(node['in']) == 0 and 'begin' not in node.keys():
            print(p_red("Error: node has not input"))
            return False

        if len(node['out']) == 0 and 'end' not in node.keys():
            print(p_red("Error: node has not output"))
            print(node)
            return False

    return True


if __name__ == "__main__":
    import signal

    signal.signal(signal.SIGINT, signal.SIG_DFL)

    filters = [
        {'id': '0', 'save': False, 'str': 'deinterlace', 'type': 'avisynth'},
        {'id': '1', 'save': False, 'str': 'replace', 'type': 'python'},
        {'id': '2', 'save': False, 'str': 'gan', 'type': 'scunet'},
        {'id': '3',
        'save': False,
        'str': '1x_HurrDeblur_SuperUltraCompact_nf24-nc8_244k_net_g',
        'type': 'pytorch'},
        {'id': '4', 'save': False, 'str': 'deshake', 'type': 'python'},
        {'id': '51', 'save': False, 'str': 'in=4,s=2,n=3', 'type': 'real_cugan'},
        {'id': '52',
        'save': False,
        'str': 'in=4,2x_LD-Anime_Compact_330k_net_g',
        'type': 'pytorch'},
        {'id': '6',
        'save': False,
        'str': 'blend,lower=51:opacity=100,top=52:opacity=50,mode=normal',
        'type': 'python'},
        {'id': '7', 'save': False, 'str': 'hqdn3d=0:0:6:6', 'type': 'ffmpeg'},
        {'id': '8',
        'save': False,
        'str': 'color_fix,in=7,ref=4,scale=12.5',
        'type': 'python'},
        {'id': '9', 'save': False, 'str': 'geometry', 'type': 'python'},
        {'id': '10', 'save': False, 'str': 'rgb', 'type': 'python'}
    ]



    node_list = deepcopy(filters)

    # Just to remember
    node_list[0]['begin'] = True
    node_list[-1]['end'] = True

    # keep track of previous node id in list
    prev_node_id = None
    for node in node_list:
        node['__prev_node_id'] = prev_node_id
        prev_node_id = node['id']

    # Convert list into dict
    nodes = {item['id']:item for item in node_list}

    set_input_dependencies(nodes)
    set_output_dependencies(nodes)

    if not verify_correctness(nodes):
        sys.exit()

    pprint(nodes)

    # Add missing nodes
    node

    # Prepare nodes for execution
    for node in nodes.values():
        node.update({
            'state': 'idle',
            'images': list(np.ndarray),
            'hash': '',
            'filepaths': list(),
            'output_folder': "",



        })



