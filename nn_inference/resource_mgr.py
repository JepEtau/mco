from __future__ import annotations
import abc
from collections.abc import Callable
from dataclasses import dataclass, field
from pprint import pprint
from threading import Thread
from rich.progress import Progress
from typing import Any, Iterable, Mapping, Type, TYPE_CHECKING
from torch import Tensor

if TYPE_CHECKING:
    from utils.mco_types import Scene
    from scene.src_scene import SrcScene
    from nn_inference.threads.t_progress import ProgressThread

from denc import NnFrame

@dataclass(slots=True)
class McoFrame(NnFrame):
    # nodes are a sequence
    sequence: list[list | tuple | str] = field(default_factory=list)
    step_no: int = 0
    encoder_step_no: int = 0

    scene: Scene | None = None
    src_scene_index: int = 0

    # save tensor used as ref for color correction
    ccor_ref: Tensor | None = None



class BaseThread(abc.ABC, Thread):
    def __init__(self,
        group: None = None,
        target: Callable[..., object] | None = None,
        name: str | None = None,
        args: Iterable[Any] = ...,
        kwargs: Mapping[str, Any] | None = None,
        *,
        daemon: bool | None = None
    ) -> None:
        super().__init__(group, target, name, args, kwargs, daemon=daemon)
        self._has_error: bool = False
        self._error_msg: str = ''
        self._debug: bool = False

        self.producer: Type[BaseThread] | None = None
        self.consumer: Type[BaseThread] | None = None
        self.progress_thread: ProgressThread | None  = None
        self._processing: bool = True


    @property
    def debug(self) -> bool:
        return self._debug


    @debug.setter
    def debug(self, enabled: bool) -> None:
        self._debug = enabled


    def error_encountered(self) -> tuple[bool, str]:
        return (self._has_error, self._error_msg)


    @abc.abstractmethod
    def stop(self, force: bool=False) -> None:
        pass


    def set_producer(self, producer: Type[BaseThread]) -> None:
        self.producer = producer


    def set_consumer(self, consumer: Type[BaseThread]) -> None:
        self.consumer = consumer


    # @abc.abstractmethod
    def set_produce_flag(self) -> None:
        pass


    def put_tensor(self, frame: Tensor) -> bool:
        pass


    def put(self, data: Any, force: bool=False) -> None:
        pass


    def put_frame(self, frame: McoFrame) -> None:
        pass


    def set_progress_thread(self, progress_thread: ProgressThread) -> None:
        self.progress_thread = progress_thread

    def processing(self) -> bool:
        return self._processing



class Singleton(type):
    _instances: dict[Any] = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]



class ResourceManager(metaclass=Singleton):
    # Simplified  class of ResourceManager

    def __init__(self) -> None:
        self._threads: dict[str, BaseThread] = {}
        self._progesses: list[Progress] = []


    def clean(self):
        for t in self._threads.values():
            if t.is_alive():
                t.stop(force=True)
        for p in self._progesses:
            p.stop()

    def __del__(self):
        print(f"{self.__class__.__name__}: delete")
        self.clean()


    def register_thread(self, thread: BaseThread) -> None:
        if thread.name not in self._threads:
            self._threads[thread.name] = thread

    def register_progress(self, progress: Progress) -> None:
        self._progesses.append(progress)
