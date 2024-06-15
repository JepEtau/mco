import os
from parsers import (
    IMG_FILENAME_TEMPLATE,
    task_to_dirname,
    TaskName
)
from utils.mco_types import (
    Scene
)
from utils.p_print import *


def get_in_frame_list(scene: Scene, task: TaskName) -> list[str]:
    # print(orange(f"\t\t\tget_new_image_list: use replace list, task={task}"))
    dirname: str = task_to_dirname[scene['task'].name]

    h: str = scene['task'].hashcode
    filename_template = IMG_FILENAME_TEMPLATE % (
        scene['k_ep'],
        scene['k_ed'],
        int(dirname[:2]),
        f"_{h}" if h != '' else ""
    )
    directory: str = os.path.join(scene['cache'], dirname)

    # Generate the list
    replace: dict[int, int] = scene['replace']
    frames: list[str] = []

    # Deinterlace: use frame no to facilitate the debug
    for no in range(
        scene['start'],
        scene['start'] + scene['count']
    ):
        try:
            new_frame_no = replace[no]
            # print_purple("\t%d -> %d" % (no, new_frame_no))
        except:
            new_frame_no = no
            # print_green("\t%d -> %d" % (no, new_frame_no))

        frames.append(
            os.path.join(
                directory,
                filename_template % (new_frame_no)
            )
        )
    # else:
    #     for no in range(scene['count']):
    #         try:
    #             new_frame_no = replace[scene['start'] + no] - scene['start']
    #             # print_purple("\t%d <- %d" % (no, new_frame_no))
    #         except:
    #             new_frame_no = no
    #             # print_green("\t%d <- %d" % (no, new_frame_no))

    #         image_list.append(os.path.join(os.path.normpath(folder),
    #             filename_template % (new_frame_no)))

    return frames
