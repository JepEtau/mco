from __future__ import annotations
from typing import Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from utils.mco_types import Scene


def scene_no_str(scene: Scene) -> str:
    if (
        ('dst' in scene and scene['dst']['k_ch'] == 'episode')
        or 'k_ch' in scene and scene['k_ch'] == 'episode'
    ):
        return f"{scene['no']:03}"

    return f"{scene['no']:02}"



def ep_key(value: int | str) -> str | None:
    if isinstance(value, int):
        return None if value == 0 else f"ep{value:02}"
    return value


def ep_no(key: str) -> int:
    return int(key[2:])


Chapter = Literal[
    'precedemment',
    'episode',
    'g_asuivre',
    'asuivre',
    'g_doc',
    'doc',
    'g_debut',
    'g_fin',
]

_credits: tuple[str] = (
    'g_debut',
    'g_fin',
    'g_asuivre',
    'g_doc'
)

_main_chapters: tuple[str] = (
    'precedemment',
    'episode',
    'g_asuivre',
    'asuivre',
    'g_doc',
    'doc'
)

_all_chapters: tuple[str] = (
    'g_debut',
    'precedemment',
    'episode',
    'g_asuivre',
    'asuivre',
    'g_doc',
    'doc',
    'g_fin'
)

_non_credit_chapters: tuple[str] = (
    'precedemment',
    'episode',
    'asuivre',
    'doc'
)


_all_unordered_chapters: tuple[str] = (
    'precedemment',
    'asuivre',
    'episode',
    'g_asuivre',
    'g_doc',
    'doc',
    'g_debut',
    'g_fin'
)


def main_chapter_keys() -> tuple[str]:
    return _main_chapters

def credit_chapter_keys() -> tuple[str]:
    return _credits

def all_chapter_keys() -> tuple[str]:
    return _all_chapters

def non_credit_chapter_keys() -> tuple[str]:
    return _non_credit_chapters

def all_unordered_chapter_keys() -> tuple[str]:
    return _all_unordered_chapters
