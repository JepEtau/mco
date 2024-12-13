from __future__ import annotations
from dataclasses import dataclass, field
from pprint import pprint
import sys
from typing import TypedDict
from utils.mco_types import Effect, Effects, Scene, EffectName
from parsers import (
    db,
)
from typing import Literal, TypedDict, TYPE_CHECKING

from utils.p_print import *
if TYPE_CHECKING:
    from parsers import (
        TaskName,
    )


class SrcScene(TypedDict):
    scene: Scene
    start: int
    count: int
    backward: bool
    k_ed_ep_ch_no: tuple[str, str, str, int]
    effects: Effects


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
        count: int,
        effects: Effects = None,
        backward: bool = False
    ) -> None:
        _scene = None
        try:
            _scene: Scene = db[k_ep]['video'][k_ed][k_ch]['scenes'][no]
        except:
            # print(f"no scene for {':'.join((k_ed, k_ep, k_ch, str(no)))}")
            pass

        if _scene is not None:
            start = _scene['start'] if start == -1 else start
            count = (
                (_scene['count'] - (start - _scene['start']))
                if count == -1
                else count
            )

        self._scenes.append(
            SrcScene(
                scene=_scene,
                start=start,
                count=count,
                k_ed_ep_ch_no=(k_ed, k_ep, k_ch, no),
                effects=effects,
                backward=backward
            )
        )


    def scenes(self) -> list[SrcScene]:
        return self._scenes


    def last_scene(self) -> SrcScene:
        return self._scenes[-1]


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
        try:
            _src_scene: Scene = db[k_ep]['video'][k_ed][k_ch]['scenes'][no]
        except:
            pprint(db[k_ep]['video'][k_ed][k_ch]['scenes'])
            raise ValueError(red(f"cannot access to scene no. {src_scene['k_ed_ep_ch_no']}"))

        start: int = (
            _src_scene['start']
            if src_scene['start'] == -1
            else src_scene['start']
        )
        count: int = src_scene['count']
        if count == -1:
            count = _src_scene['count'] - (start - _src_scene['start'])

        if count < -1:
            count = abs(count)
            start = _src_scene['start'] + _src_scene['count'] - count

        src_scene.update({
            'scene': _src_scene,
            'start': start,
            'count': count,
        })


        # if k_ch == 'g_fin':
        #     print(f"to scene")
        #     pprint(src_scene)
        #     sys.exit()


        if src_scene['effects'] is not None:
            for e in src_scene['effects'].effects:
                if e.name == 'blend':
                    e.frame_ref = src_scene['start']
                elif e.frame_ref == -1:
                    e.frame_ref = src_scene['start'] + src_scene['count'] - 1
                elif e.frame_ref == 0:
                    e.frame_ref = src_scene['start']


    def frame_count(self, exclude_loop: bool = False) -> int:
        count: int = 0
        for src_scene in self._scenes:
            if src_scene['scene'] is None:
                self._consolidate_scene(src_scene)
            count += src_scene['count']

            if not exclude_loop:
                # Exception: do not count loop when upscaling
                if src_scene['effects'] is not None:
                    e: Effect = src_scene['effects'].get_effect('zoom_in')
                    count += e.loop if e is not None else 0

        return count


    def last_frame_no(self) -> int:
        last_scene = self._scenes[-1]
        return last_scene['start'] + last_scene['count'] - 1


    def first_frame_no(self) -> int:
        """Returns the frame no of the 1st source"""
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


    def get_src_scene_from_frame_no(self, frame_no: int) -> SrcScene:
        for src_scene in self._scenes:
            start: int = src_scene['scene']['start']
            end: int = src_scene['scene']['start'] + src_scene['scene']['count'] - 1
            if start <= frame_no <= end:
                return src_scene
        raise ValueError(f"Scene not found for frame no. {frame_no}")
        return None


    def has_effects(self) -> bool:
        for s in self._scenes:
            if (s['effects'] is not None
                and s['effects'].has_effects()
            ):
                return True
        return False


    def has_effect(self, name: EffectName) -> bool:
        for s in self._scenes:
            if (s['effects'] is not None
                and s['effects'].has_effect(name)
            ):
                return True
        return False


    def get_edition(self) -> str:
        k_eds: set[str] = set()
        for s in self._scenes:
            k_eds.add(s['scene']['k_ed'])
        if len(k_eds) > 1:
            raise ValueError(f"{':'.join(s['k_ed_ep_ch_no'])} uses mor than 1 edition: {k_eds}")
        return k_eds.pop()
