from collections import Counter, UserDict, deque
from copy import deepcopy
from pprint import pprint
import sys
from typing import Any

from utils.p_print import yellow


def frame_occurences(replacements: dict[int, int]) -> dict[int, int]:
    """Returns the occurence of use for each frame used to
        replace another one"""
    counter: Counter = Counter(replacements.values())
    return counter


def get_frames_to_remove(replacements: dict[int, int]) -> list[int]:
    return sorted(replacements.keys())



def get_frames_to_cache(replacements: dict[int, int]) -> deque[int]:
    return deque(sorted(set(replacements.values())))



class ItemCache(UserDict):
    def __init__(self, verbose: bool = False):
        super().__init__()
        self.occurences: Counter = Counter()
        self.cached: Counter = Counter()
        self.exceptions: set = set()
        self.verbose: bool = verbose


    def __getitem__(self, key: Any) -> Any:
        if self.verbose:
            print(f"ImageCache: GET {key}")
        if key not in self.data:
            return None
        item = super().__getitem__(key)
        if item is not None:
            self.cached[key] -= 1
            if self.verbose:
                print(f"  try removing {key}: {self.cached[key]}")
            if self.cached[key] <= 0:
                del self.cached[key]
                del self.data[key]
                if self.verbose:
                    print("  Delete item from cache")
        elif self.verbose:
            print(f"  ImageCache: not in cache")
        return item


    def __setitem__(self, key: Any, item: Any) -> None:
        if self.verbose:
            print(f"  ImageCache: Add {key}")
        if key in self.exceptions:
            if self.verbose:
                print("  not cacheable, discard")
            return
        if key not in self.cached:
            self.cached[key] = self.occurences[key] + 1
            if self.verbose:
                print(f"  set cached item of {key} to {self.cached[key]}")
        else:
            self.cached[key] += 1
            if self.verbose:
                print(f"  add cached item of {key} -> {self.cached[key]}")
        return super().__setitem__(key, item)


    def set_occurences(self, replacements: dict[int, int]) -> None:
        """Save a counter of times a frame will be retrieved
        """
        self.occurences = frame_occurences(replacements)
        if self.verbose:
            print(yellow("set occurences"))
            pprint(self.occurences)


    def set_exceptions(self, exceptions: set[int] | list[int]) -> None:
        """Do not cache the frames that will be replaced. save the keys
        """
        if isinstance(exceptions, set):
            self.exceptions = exceptions
        else:
            self.exceptions = set(exceptions)
        if self.verbose:
            print(yellow("set exceptions"))
            pprint(self.exceptions)


    def add(self, key: Any, item: Any, set_occurence: bool = True) -> None:
        """Add an item to the cache.
            if set_occurence is False, the nb of occurences
            is not modified.
            This boolen is used by the ReplaceNode to not count
            an additionnal occurence if an item is put in cache while
            used
        """
        # if key not in self.occurences:
        #     return
        self.__setitem__(key, item)
        # if not set_occurence:
        #     self.occurences[key] -= 1
