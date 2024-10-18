from collections import Counter, UserDict, deque
from pprint import pprint
from typing import Any


def frame_occurences(replacements: dict[int, int]) -> dict[int, int]:
    """Returns the occurence of use for each frame used to
        replace another one"""
    return Counter(replacements.values())



def get_frames_to_remove(replacements: dict[int, int]) -> list[int]:
    return sorted(replacements.keys())



def get_frames_to_cache(replacements: dict[int, int]) -> deque[int]:
    return deque(sorted(set(replacements.values())))



class ItemCache(UserDict):
    def __init__(self, verbose: bool = False):
        super().__init__()
        self.occurences: Counter = Counter()
        self.exceptions: set = set()
        self.verbose: bool = verbose


    def __getitem__(self, key: Any) -> Any:
        if self.verbose:
            print(f"ImageCache: GET {key}")
        item = super().__getitem__(key)
        if item is not None:
            if self.verbose:
                print(f"try removing {key}: {self.occurences[key]}")
            self.occurences[key] -= 1
            if self.occurences[key] <= 0:
                del self.occurences[key]
                del self.data[key]
                if self.verbose:
                    print("\tDelete item from cache")
        elif self.verbose:
            print(f"ImageCache: not in cache")
        return item


    def __setitem__(self, key: Any, item: Any) -> None:
        if self.verbose:
            print(f"ImageCache: SET {key}")
        if key in self.exceptions:
            if self.verbose:
                print("\tnot cacheable, discard")
            return
        if key not in self.occurences:
            if self.verbose:
                print(f"set occurence of {key}")
            self.occurences[key] = 1
        else:
            self.occurences[key] += 1
            if self.verbose:
                print(f"add occurence of {key} -> {self.occurences[key]}")
        return super().__setitem__(key, item)


    def set_occurences(self, occurences: Counter)  -> None:
        self.occurences = occurences
        if self.verbose:
            pprint(self.occurences)


    def set_exceptions(self, exceptions: set | list) -> None:
        """Do not cache some items"""
        if isinstance(exceptions, set):
            self.exceptions = exceptions
        else:
            self.exceptions = set(exceptions)


    def add(self, key: Any, item: Any, set_occurence: bool = True) -> None:
        """Add an item to the cache.
            if set_occurence is False, the nb of occurences
            is not modified.
            This boolen is used by the ReplaceNode to not count
            an additionnal occurence if an item is put in cache while
            used
        """
        self.__setitem__(key, item)
        if not set_occurence:
            self.occurences[key] -= 1
