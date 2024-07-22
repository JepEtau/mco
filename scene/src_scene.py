from __future__ import annotations
from dataclasses import dataclass, field
from typing import TypedDict
from utils.mco_types import Scene
from parsers import (
    db,
)
from typing import Literal, TypedDict, TYPE_CHECKING
if TYPE_CHECKING:
    from parsers import (
        TaskName,
    )


class SrcScene(TypedDict):
    scene: Scene
    start: int
    count: int
    k_ed_ep_ch_no: tuple[str, str, str, int]


@dataclass
class SrcScenes:
    _scenes: list[SrcScene] = field(default_factory=list)

    def add_scene(
        self,
        k_ed: str,
        k_ep: str,
        k_ch: str,
        no: int,
        start: int,
        count: int
    ) -> None:
        try:
            _scene: Scene = db[k_ep]['video'][k_ed][k_ch]['scenes'][no]
            start = _scene['start'] if start == -1 else start
            count = _scene['count'] if count == -1 else count
        except:
            _scene = None
        self._scenes.append(
            SrcScene(
                scene=_scene,
                start=start,
                count=count,
                k_ed_ep_ch_no=(k_ed, k_ep, k_ch, no)
            )
        )


    def scenes(self) -> list[SrcScene]:
        return self._scenes


    def get_dependencies(self) -> dict[str, set[str]]:
        """returns a dict of ed, ep
        """
        dependencies: dict[str, set[str]] = {}
        for scene in self._scenes:
            k_ed, k_ep = scene['k_ed_ep_ch_no'][:2]
            if k_ed not in dependencies:
                dependencies[k_ed] = set()
            dependencies[k_ed].add(k_ep)
        return dependencies


    def _consolidate_scene(self, src_scene: SrcScene) -> None:
        k_ed, k_ep, k_ch, no = src_scene['k_ed_ep_ch_no']
        _src_scene = db[k_ep]['video'][k_ed][k_ch]['scenes'][no]
        src_scene.update({
            'scene': _src_scene,
            'start': _src_scene['start'] if src_scene['start'] == -1 else src_scene['start'],
            'count': _src_scene['count'] if src_scene['count'] == -1 else src_scene['count'],
        })


    def frame_count(self) -> int:
        count: int = 0
        for src_scene in self._scenes:
            if src_scene['scene'] is None:
                self._consolidate_scene(src_scene)
            count += src_scene['count']
        return count


    def last_frame_no(self) -> int:
        last_scene = self._scenes[-1]
        return last_scene['start'] + last_scene['count'] - 1


    def first_frame_no(self) -> int:
        return self._scenes[0]['start']

    def primary_scene(self) -> SrcScene:
        primary_scene = self._scenes[0]
        if primary_scene['scene'] is None:
            self._consolidate_scene(primary_scene)
        return primary_scene

    def __len__(self) -> int:
        return len(self._scenes)


    def get_frame_replace(self) -> dict[int, int]:
        frame_replace: dict[int, int] = {}
        for s in self._scenes:
            frame_replace.update(s['scene']['replace'])
        return frame_replace

    def consolidate(self, task_name: TaskName, watermark: bool) -> None:
        from scene.consolidate_src import consolidate_src_scene
        for src_scene in self._scenes:
            if src_scene['scene'] is None:
                self._consolidate_scene(src_scene)
            consolidate_src_scene(
                scene=src_scene['scene'],
                task_name=task_name,
                watermark=watermark
            )


