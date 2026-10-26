from collections import deque
from pprint import pprint

from typing import Any
from nn_inference.resource_mgr import McoFrame
from utils.p_print import *


# frame_warp_cache: dict[int, NnFrame] = OrderedDict()

class FrameWarpCache(deque):
    def __init__(self):
        super().__init__()
        self._cached_f_no: list[int] = []

    def append(self, f_no: int, x: McoFrame) -> None:
        self._cached_f_no.append(f_no)
        super().append(x)

    @property
    def cached(self) -> list[int]:
        return self._cached_f_no

    def popleft(self) -> McoFrame:
        self._cached_f_no.pop(0)
        return super().popleft()



# class FrameWarpCache(UserDict):
#     def __init__(self, verbose: bool = False):
#         super().__init__()
#         self.occurences: Counter = Counter()
#         self.cached: Counter = Counter()
#         self.exceptions: set = set()
#         self.verbose: bool = verbose
#         self.replacements: dict[int, int] = []
#         self.cached_frames: list


#     def __getitem__(self, key: Any) -> Any:
#         if self.verbose:
#             print(darkgrey(f"ImageCache: GET {key}"))
#         if key not in self.data:
#             return None
#         item = super().__getitem__(key)
#         if item is not None:
#             self.cached[key] -= 1
#             if self.verbose:
#                 print(darkgrey(f"  try removing {key}: {self.cached[key]}"))
#             if self.cached[key] <= 0:
#                 del self.cached[key]
#                 del self.data[key]
#                 if self.verbose:
#                     print("  Delete item from cache")
#         elif self.verbose:
#             print(darkgrey(f"  ImageCache: not in cache"))
#         return item


#     def __setitem__(self, key: Any, item: Any) -> None:
#         if self.verbose:
#             print(darkgrey(f"  ImageCache: Add {key}"))
#         if key in self.exceptions:
#             if self.verbose:
#                 print("  not cacheable, discard")
#             return
#         if key not in self.cached:
#             self.cached[key] = self.occurences[key] + 1
#             if self.verbose:
#                 print(darkgrey(f"  set cached item of {key} to {self.cached[key]}"))
#         else:
#             self.cached[key] += 1
#             if self.verbose:
#                 print(darkgrey(f"  add cached item of {key} -> {self.cached[key]}"))
#         return super().__setitem__(key, item)


#     def _set_exceptions(self) -> None:
#         """Do not cache the frames that will be replaced. save the keys
#         """
#         exceptions: set[int] | list[int] = list(self.replacements.keys())
#         if isinstance(exceptions, set):
#             self.exceptions = exceptions
#         else:
#             self.exceptions = set(exceptions)
#         if self.verbose:
#             print(yellow("set exceptions"))
#             pprint(self.exceptions)


#     def set_replaced_frames(self, replacements: dict[int, int]) -> None:
#         """Save a counter of times a frame will be retrieved
#         """
#         self.replacements = replacements
#         self.occurences: Counter = Counter(replacements.values())
#         if self.verbose:
#             print(yellow("set occurences"))
#             pprint(self.occurences)
#         self._set_exceptions()


#     def add(self, key: Any, item: Any, set_occurence: bool = True) -> None:
#         """Add an item to the cache.
#             if set_occurence is False, the nb of occurences
#             is not modified.
#             This boolen is used by the ReplaceNode to not count
#             an additionnal occurence if an item is put in cache while
#             used
#         """
#         # if key not in self.occurences:
#         #     return
#         self.__setitem__(key, item)
#         # if not set_occurence:
#         #     self.occurences[key] -= 1



#     def frame_cache_warp(self, f_ref_no):
#         for f in self.cached_frames:
#             if f.
