import numpy as np
from nn_inference.toolbox.resize_to_4_3 import (
    calculate_transformation_values,
    ConvertTo43Params,
    dimensions_from_crop,
    TransformationValues,
)
from parsers import (
    db,
    FINAL_HEIGHT,
    FINAL_WIDTH,
    VideoSettings,
)
from utils.mco_types import (
    Scene,
    SceneGeometry,
)
from utils.media import VideoInfo, extract_media_info
from utils.p_print import *

# @dataclass
class SceneStatGeometry:

    def __init__(
        self,
        scene: Scene,
    ) -> None:
        self.geometry: SceneGeometry = scene['geometry']
        crop_values: list[int, int, int, int] = (
            self.geometry.autocrop
            if self.geometry.use_autocrop
            else self.geometry.crop
        )
        self._defined: bool = True

        vsettings: VideoSettings = db['common']['video_format']['hr']
        if any([c <= vsettings.pad for c in crop_values]):
            # Not valid:
            print(red("crop is missing"))
            self._defined = False
            return

        # top, bottom, left, right
        self._crop: tuple[int, int, int, int] = crop_values

        try:
            in_vi: VideoInfo = extract_media_info(scene['task'].in_video_file)['video']
        except:
            self._defined = False
            self._is_erroneous = True
            return

        # height, width
        in_size: tuple[int, int] = in_vi['shape'][:2]

        c_t, c_b, c_l, c_r, c_w, c_h = dimensions_from_crop(
            in_size[1], in_size[0], crop_values
        )
        # print(cyan(f"-> cropped size ({c_w}, {c_h}). Crop values: [{c_t}, {c_b}, {c_l}, {c_r}]"))

        # Maximum width this scene can have. Width of the resized crop rectangle
        self._max_width: int = int(c_w * FINAL_HEIGHT / c_h)

        to_43_params: ConvertTo43Params = ConvertTo43Params(
            crop=crop_values,
            keep_ratio=self.geometry.keep_ratio,
            fit_to_width=self.geometry.fit_to_width,
            final_height=FINAL_HEIGHT,
            scene_width=scene['geometry'].chapter.width,
        )

        self.transformation: TransformationValues | None = None
        try:
            self.transformation = calculate_transformation_values(
                in_w=in_size[1],
                in_h=in_size[0],
                out_w=FINAL_WIDTH,
                params=to_43_params,
                verbose=False
            )
        except:
            pass

        self._is_erroneous: bool = bool(
            self.transformation is None
            or self.transformation.err_borders is not None
        )


    @property
    def max_width(self) -> int:
        return self._max_width


    @property
    def crop(self) -> tuple[int, int, int, int]:
        return self._crop


    def is_erroneous(self) -> bool:
        return self._is_erroneous


    def is_defined(self) -> bool:
        return self._defined


    def keep_ratio(self) -> bool:
        return self.geometry.keep_ratio


    def fit_to_width(self) -> bool:
        return self.geometry.fit_to_width




class ChGeometryStats:

    def __init__(self) -> None:
        self._scenes: dict[str, SceneStatGeometry] = {}
        self._undefined_scenes: list[int] = []


    @staticmethod
    def _scene_key(scene: Scene) -> str:
        return f"{scene['no']:03}"


    def append(self, scene: Scene) -> None:
        scene_stats: SceneStatGeometry = SceneStatGeometry(scene)
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
        return max(max_width_list) if max_width_list else -1


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
        try:
            del self._scenes[self._scene_key(scene)]
        except:
            pass
        try:
            self._undefined_scenes.remove(scene['no'])
        except:
            pass
            self.append(scene)


    def fit_to_width_scenes(self) -> tuple[int]:
        return sorted(list([
            int(k) for k, s in self._scenes.items()
            if s.fit_to_width()
        ]))


    def anamorphic_scenes(self) -> tuple[int]:
        return sorted(list([
            int(k) for k, s in self._scenes.items()
            if not s.keep_ratio()
        ]))
