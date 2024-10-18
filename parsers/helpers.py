from __future__ import annotations


def get_fps(db: dict) -> float:
    return float(db['common']['settings']['fps'])


def nested_dict_set(d: dict, o: object, *keys) -> None:
    nested_d = d
    for k in keys:
        if k == keys[-1]:
            break
        if k not in nested_d.keys():
            nested_d[k] = dict()
        nested_d = nested_d[k]
    nested_d[k] = o

