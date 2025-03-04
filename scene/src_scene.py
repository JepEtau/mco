from __future__ import annotations
from dataclasses import dataclass, field
from pprint import pprint
from typing import Any
from utils.mco_types import Scene
from parsers import (
    db,
)
from typing import TYPE_CHECKING

from utils.p_print import *
if TYPE_CHECKING:
    from parsers import (
        TaskName,
        Effect,
        Effects,
        EffectName,
    )


class SrcScene:
    """This class is used to defined src scene in target scenelist
        It contains a pointer to the original scene ep/ed/chapter/scenes/scene_no
    """

    def __init__(
        self,
        in_scene: Scene,
        start: int,
        count: int,
        backward: bool,
        k_ed_ep_ch_no: tuple[str, str, str, int],
        effects: Effects | None,
    ):
        self.__dict__.update({
            'backward': backward,
            'k_ed_ep_ch_no': k_ed_ep_ch_no,
        })
        self._start: int = start
        self._count: int = count
        self._effects: Effects | None = effects

        # scene is the original scene
        self._in_scene: Scene = in_scene

        if in_scene is not None and 'effects' in in_scene is not None:
            pprint(in_scene['effects'])

            # Point to the effects of the original scene
            if effects is None:
                self._effects: Effects = in_scene['effects']
            else:
                for e in in_scene['effects'].effects:
                    self.effects.append(e)


    def __getitem__(self, key: str) -> Any:
        if key in ('start', 'count', 'effects', 'scene'):
            raise
        return getattr(self, key)


    def update(self, values: dict[str, Any]) -> None:
        keys = list(values.keys())
        if 'start' in keys or 'count' in keys or 'scene' in keys:
            raise ValueError("not allowed to access")
        self.__dict__.update(values)


    @property
    def count(self) -> int:
        v = self._count
        if self._effects is not None:
            if e := self._effects.get_effect(name='decimate'):
                factor: int = e.extra_param[0]
                # e.extra_param[1] = v
                return int(v * (factor - 1 ) / factor + 0.5)

            elif e := self._effects.get_effect(name='decimate2'):
                factor: int = e.extra_param[0]
                # e.extra_param[1] = v
                return int((v * (factor - 1 ) / factor + 0.5) / e.extra_param[1])

        return v


    @count.setter
    def count(self, v: int) -> None:
        self._count = v


    @property
    def start(self) -> int:
        return self._start


    @start.setter
    def start(self, v: int) -> None:
        self._start = v


    @property
    def to_decode(self) -> int:
        return self._count

    @property
    def in_scene(self) -> Scene:
        """Returns the scene specific to an edition.
        It's used to generate a 'source' scene which can use
        the full or a partial length of this scene
        """
        return self._in_scene


    def set_initial_scene(self, scene: Scene) -> None:
        self._in_scene = scene


    @property
    def effects(self) -> Effects | None:
        return self._effects


    def to_dict(self) -> dict:
        class_dict = {k: v for k, v in self.__dict__.items() if k not in ('scene', '_scene')}
        class_dict['count'] = self.count
        class_dict['to_decode'] = self.to_decode
        return class_dict


    def __repr__(self):
        class_dict = {k: v for k, v in self.__dict__.items() if k not in ('scene', '_scene')}
        class_dict['count'] = self.count
        class_dict['to_decode'] = self.to_decode
        ed_scene = self.in_scene
        class_dict['scene'] = (
            "{" + f"{ed_scene['k_ed']}:{ed_scene['k_ep']}:{ed_scene['k_ch']}:{ed_scene['no']}..." + "}"
        )

        class_str = "\n        {\n"
        class_str += "\n".join([f"            \'{k}\': {v}" for k, v in class_dict.items()])
        class_str += "\n        }"
        return class_str



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

        src_scene: SrcScene = SrcScene(
            in_scene=_scene,
            start=start,
            count=count,
            k_ed_ep_ch_no=(k_ed, k_ep, k_ch, no),
            effects=effects,
            backward=backward,
        )
        self._scenes.append(src_scene)


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
            _src_scene['start'] if src_scene.start == -1 else src_scene.start
        )
        count: int = src_scene.count
        if count == -1:
            count = _src_scene['count'] - (start - _src_scene['start'])

        if count < -1:
            count = abs(count)
            start = _src_scene['start'] + _src_scene['count'] - count

        src_scene.set_initial_scene(_src_scene)
        src_scene.start = start
        src_scene.count = count

        # if k_ch == 'g_fin':
        #     print(f"to scene")
        #     pprint(src_scene)
        #     sys.exit()


        if src_scene.effects is not None:
            effects: Effects = src_scene.effects
            for e in effects.effects:
                if e.name == 'blend':
                    e.frame_ref = src_scene.start
                elif e.f_ref == -1:
                    e.f_ref = src_scene.start + src_scene.start - 1
                elif e.f_ref == 0:
                    e.f_ref = src_scene.start

            if effects.has_effect('title'):
                e: Effect = effects.get_effect('title')
                if effects.has_effect('zoom_in'):
                    e.f_ref = src_scene.start - 1
                    e = src_scene.effects.get_effect('zoom_in')
                    e.f_ref = src_scene.start - 1
                else:
                    e.f_ref = 0
                    if e.loop <= 0:
                        e.loop = 1

            if e := effects.get_effect('fadein'):
                e.f_ref = 0


    def frame_count(self, exclude_loop: bool = False) -> int:
        count: int = 0
        for src_scene in self._scenes:
            if src_scene.in_scene is None:
                self._consolidate_scene(src_scene)
            count += src_scene.count

            if (
                src_scene.in_scene is not None
                and 'effects' in src_scene.in_scene
                and src_scene.in_scene['effects'] is not None
            ):
                e: Effect = src_scene.in_scene['effects'].get_effect('se_loop')
                if e is not None:
                    print(yellow(e))
                    count += sum(e.extra_param)

            if not exclude_loop:
                # Exception: do not count loop when upscaling
                if src_scene.effects is not None:
                    e: Effect = src_scene.effects.get_effect('zoom_in')
                    count += e.loop if e is not None else 0

        return count


    def last_frame_no(self) -> int:
        """Return the last frame no of the scene.
        Do not forget to add 1 to calculate the number of frames
        """
        last_scene = self._scenes[-1]
        return last_scene.start + last_scene.count - 1


    def first_frame_no(self) -> int:
        """Returns the frame no of the 1st source"""
        return self._scenes[0].start


    def primary_scene(self) -> SrcScene:
        primary_scene = self._scenes[0]
        if primary_scene.in_scene is None:
            self._consolidate_scene(primary_scene)
        return primary_scene


    def __len__(self) -> int:
        return len(self._scenes)


    def get_frame_replace(self) -> dict[int, int]:
        frame_replace: dict[int, int] = {}
        for s in self._scenes:
            frame_replace.update(s.in_scene['replace'])
        return frame_replace


    def consolidate(self, task_name: TaskName, watermark: bool) -> None:
        from scene.consolidate_src import consolidate_src_scene
        for src_scene in self._scenes:
            if src_scene.in_scene is None:
                self._consolidate_scene(src_scene)

            consolidate_src_scene(
                scene=src_scene.in_scene,
                task_name=task_name,
                watermark=watermark
            )


    def get_src_scene_from_frame_no(self, frame_no: int) -> SrcScene:
        for src_scene in self._scenes:
            start: int = src_scene.in_scene['start']
            end: int = src_scene.in_scene['start'] + src_scene.in_scene['count'] - 1
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
            k_eds.add(s.in_scene['k_ed'])
        if len(k_eds) > 1:
            raise ValueError(f"{':'.join(s['k_ed_ep_ch_no'])} uses mor than 1 edition: {k_eds}")
        return k_eds.pop()


    def __repr__(self):
        class_str = "SrcScenes("
        for s in self.scenes():
            class_str += s.__repr__() + ","
        return class_str + "\n    )"

