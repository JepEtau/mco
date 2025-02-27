from __future__ import annotations
from ._db import db


def get_frame_rate() -> float:
    return float(db['vsettings']['common']['frame_rate'])


def nested_dict_set(d: dict, keys: tuple[str], o: object) -> None:
    nested_d = d
    for k in keys:
        if k == keys[-1]:
            break
        if k not in nested_d.keys():
            nested_d[k] = dict()
        nested_d = nested_d[k]
    nested_d[k] = o

