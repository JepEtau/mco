from collections import Counter, UserDict
from pprint import pprint
from typing import Any
from utils.p_print import *



class FrameCache(UserDict):
    def __init__(self, verbose: bool = False):
        super().__init__()
        self.occurences: Counter = Counter()
        self.cached: Counter = Counter()
        self.exceptions: set = set()
        self.verbose: bool = verbose
        self.replacements: dict[int, int] = []
        self.segments: list[tuple[int, int, int]] = []


    def __getitem__(self, key: Any) -> Any:
        if self.verbose:
            print(darkgrey(f"ImageCache: GET {key}"))
        if key not in self.data:
            return None
        item = super().__getitem__(key)
        if item is not None:
            self.cached[key] -= 1
            if self.verbose:
                print(darkgrey(f"  try removing {key}: {self.cached[key]}"))
            if self.cached[key] <= 0:
                del self.cached[key]
                del self.data[key]
                if self.verbose:
                    print("  Delete item from cache")
        elif self.verbose:
            print(darkgrey(f"  ImageCache: not in cache"))
        return item


    def __setitem__(self, key: Any, item: Any) -> None:
        if self.verbose:
            print(darkgrey(f"  ImageCache: Add {key}"))
        if key in self.exceptions:
            if self.verbose:
                print("  not cacheable, discard")
            return
        if key not in self.cached:
            self.cached[key] = self.occurences[key] + 1
            if self.verbose:
                print(darkgrey(f"  set cached item of {key} to {self.cached[key]}"))
        else:
            self.cached[key] += 1
            if self.verbose:
                print(darkgrey(f"  add cached item of {key} -> {self.cached[key]}"))
        return super().__setitem__(key, item)


    def _set_exceptions(self) -> None:
        """Do not cache the frames that will be replaced. save the keys
        """
        exceptions: set[int] | list[int] = list(self.replacements.keys())
        if isinstance(exceptions, set):
            self.exceptions = exceptions
        else:
            self.exceptions = set(exceptions)
        if self.verbose:
            print(yellow("set exceptions"))
            pprint(self.exceptions)


    def set_replaced_frames(self, replacements: dict[int, int]) -> None:
        """Save a counter of times a frame will be retrieved
        """
        self.replacements = replacements
        self.occurences: Counter = Counter(replacements.values())
        if self.verbose:
            print(yellow("set occurences"))
            pprint(self.occurences)
        self._set_exceptions()


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


    def add_loop_segment(self, segment: tuple[int, int, int]) -> None:
        """segment: (start, loop, ref)
        """
        start, loop, ref = segment
        # start, end (inc.), frame used as ref
        self.segments.append(
            (start, start + loop - 1, ref)
        )


    def to_replace(self, f_no: int) -> bool:
        for s in self.segments:
            if s[0] <= f_no <= s[1] and f_no != s[2]:
                # print(darkgrey(f"   discard {f_no} (loop: {s[1] - s[0]}, ref: {s[2]})"))
                return True

        if f_no in self.replacements:
            # print(darkgrey(f"   discard {f_no} (replaced)"))
            return True

        return False


    def get_out_f_no(self, f_no: int) -> int:
        for s in self.segments:
            if s[0] <= f_no <= s[1]:
                # print(darkgrey(f"  ignore {f_no} because replace by loop {s[2]}"))
                return s[2]

        if f_no in self.replacements:
            return self.replacements[f_no]

        return f_no
