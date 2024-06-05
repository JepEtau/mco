


from typing import Literal


def key(value: int | str) -> str | None:
    if isinstance(value, int):
        return None if value == 0 else f"ep{value:02}"
    return value


Chapter = Literal[
    'precedemment',
    'episode',
    'g_asuivre',
    'asuivre',
    'g_documentaire',
    'documentaire'
]

_credits: tuple[str] = (
    'g_debut',
    'g_fin',
    'g_asuivre',
    'g_documentaire'
)

_main_chapters: tuple[str] = (
    'precedemment',
    'episode',
    'g_asuivre',
    'asuivre',
    'g_documentaire',
    'documentaire'
)

_all_chapters: tuple[str] = (
    'g_debut',
    'precedemment',
    'episode',
    'g_asuivre',
    'asuivre',
    'g_documentaire',
    'documentaire',
    'g_fin'
)

_non_credit_chapters: tuple[str] = (
    'precedemment',
    'episode',
    'asuivre',
    'documentaire'
)



def main_chapter_keys() -> tuple[str]:
    return _main_chapters

def credit_chapter_keys() -> tuple[str]:
    return _credits

def all_chapter_keys() -> tuple[str]:
    return _all_chapters

def non_credit_chapter_keys() -> tuple[str]:
    return _non_credit_chapters

