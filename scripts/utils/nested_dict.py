# -*- coding: utf-8 -*-


# def nested_dict_set(d:dict, o:object, *keys):
def nested_dict_set(d, o:object, *keys):
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
    # Awfull but working
    try:
        for k0, v0 in d.items():
            for k1, v1 in v0.items():
                for k2, v2 in v1.items():
                    for k3, v3 in v1.items():
                        if type(v3) is dict and len(v3.keys()) == 0:
                            del d[k0][k1][k2][k3]
    except: pass

    try:
        for k0, v0 in d.items():
            for k1, v1 in v0.items():
                for k2, v2 in v1.items():
                    if type(v2) is dict and len(v2.keys()) == 0:
                        del d[k0][k1][k2]
    except: pass


    try:
        for k0, v0 in d.items():
            for k1, v1 in v0.items():
                if type(v1) is dict and len(v1.keys()) == 0:
                    del d[k0][k1]
    except: pass

    try:
        for k0, v0 in d.items():
            if type(v0) is dict and len(v0.keys()) == 0:
                del d[k0]
    except: pass


