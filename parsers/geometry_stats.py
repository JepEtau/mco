from __future__ import annotations
from pprint import pprint
from typing import TYPE_CHECKING

import numpy as np

from processing.resize_to_4_3 import TransformationValues
from utils.media import VideoInfo, extract_media_info
from utils.p_print import red

from .geometry import SceneGeometry
from ._types import VideoSettings
from ._db import db

if TYPE_CHECKING:
    from utils.mco_types import Scene


class SceneGeometryStat:

    def __init__(
        self,
        scene: Scene,
        in_size: tuple[int, int] | None
    ) -> None:
        self.geometry: SceneGeometry = scene['geometry']
        self._defined: bool = True

        vsettings: VideoSettings = db['common']['video_format']['hr']
        if any([c <= vsettings.pad for c in self.crop]):
            # Not valid:
            print(red("crop is missing"))
            self._defined = False
            return

        if in_size is None:
            self._is_erroneous = True
            self._defined = False
            return

        # Maximum width this scene can have. Width of the resized crop rectangle
        self.geometry.set_in_size(in_size)
        self.in_size = in_size

        self.transformation: TransformationValues | None = self.geometry.calculate_transformation()

        self._is_erroneous: bool = bool(
            self.transformation is None
            or self.transformation.err_borders is not None
        )


    @property
    def max_width(self) -> int:
        return self.geometry.max_width()


    def resized_to(self) -> tuple[int, int]:
        return self.transformation.resize_to


    @property
    def crop(self) -> tuple[int, int, int, int]:
        return self.geometry.get_crop()


    def is_erroneous(self) -> bool:
        return self._is_erroneous


    def is_defined(self) -> bool:
        return self._defined


    @property
    def keep_ratio(self) -> bool:
        return self.geometry.keep_ratio


    @property
    def fit_to_width(self) -> bool:
        return self.geometry.fit_to_width


    @property
    def autocrop(self) -> bool:
        return self.geometry.use_autocrop


    def update(self, scene_geometry: SceneGeometry) -> None:
        self.geometry: SceneGeometry = scene_geometry
        scene_geometry.set_in_size(self.in_size)
        self.transformation: TransformationValues | None = self.geometry.calculate_transformation()
        self._is_erroneous: bool = self.geometry.is_erroneous()



class ChGeometryStats:

    def __init__(self) -> None:
        self._scenes: dict[str, SceneGeometryStat] = {}
        self._undefined_scenes: list[int] = []
        self._sizes: dict[str, tuple[int, int]] = {}


    @staticmethod
    def _scene_key(scene: Scene) -> str:
        return f"{scene['no']:03}"


    def append(self, scene: Scene) -> None:
        fp: str = scene['task'].in_video_file
        if fp not in self._sizes.keys():
            try:
                in_vi: VideoInfo = extract_media_info(fp)['video']
            except:
                return

            # height, width
            self._sizes['fp'] = in_vi['shape'][:2]

        scene_stats: SceneGeometryStat = SceneGeometryStat(
            scene, self._sizes['fp']
        )
        if scene_stats.is_defined():
            self._scenes[self._scene_key(scene)] = scene_stats
        else:
            self._undefined_scenes.append(scene['no'])


    def crop_values(self) -> np.ndarray:
        return np.array(list([
            s.crop for s in self._scenes.values()
        ]))


    def max_width(self) -> int:
        max_width_list: list[int] = list(
            [s.max_width for s in self._scenes.values() if s.is_defined()]
        )
        return max(max_width_list) if len(max_width_list) > 0 else -1


    def min_max_width_scene(self) -> tuple[int, int]:
        """Returns a tuple of scene no and min of the max width
        """
        min_max_width: int = 1e6
        min_max_width_scene: tuple[int, int] = ()
        for k, s in self._scenes.items():
            if s.max_width < min_max_width:
                min_max_width_scene = (int(k), s.max_width)

        return min_max_width_scene


    def valid_scenes(self) -> list[int]:
        return list([
            int(k) for k, s in self._scenes.items()
            if not s.is_erroneous()
        ])


    def undefined_scenes(self) -> list[int]:
        return self._undefined_scenes


    def erroneous_scenes(self) -> list[int]:
        """Returns a list of erroneous scenes
        """
        erroneous = list([
            int(k) for k, s in self._scenes.items()
            if s.is_erroneous()
        ])
        erroneous.extend(self._undefined_scenes)
        return sorted(list(set(erroneous)))


    def not_initialized_scenes(self) -> tuple[int]:
        return self._undefined_scenes


    def update(self, scene: Scene) -> None:
        if scene['no'] in self._undefined_scenes:
            self._undefined_scenes.remove(scene['no'])
            self.append(scene)

        elif self._scene_key(scene) in self._scenes:
            self._scenes[self._scene_key(scene)].update(
                scene['geometry']
            )


    def fit_to_width_scenes(self) -> tuple[int]:
        return sorted(list([
            int(k) for k, s in self._scenes.items()
            if s.fit_to_width
        ]))


    def anamorphic_scenes(self) -> tuple[int]:
        return sorted(list([
            int(k) for k, s in self._scenes.items()
            if not s.keep_ratio
        ]))


    def get(self, scene_no: int) -> SceneGeometryStat | None:
        try:
            return self._scenes[f"{scene_no:03}"]
        except:
            pass

        return None
