from configparser import ConfigParser
import os
from pathlib import Path, PosixPath
from .helpers import nested_dict_set
from utils.path_utils import absolute_path



def parse_frames_for_study(db, k_ep):
    # Parse the ini file which contains the listf of frames
    # used in study mode

    nested_dict_set(db, dict(), k_ep, 'video', 'frames')
    db_frames = db[k_ep]['video']['frames']

    # Open configuration file
    filepath = os.path.join(db['common']['directories']['config'], k_ep, "%s_frames.ini" % (k_ep))
    if filepath.startswith("~/"):
        filepath = os.path.join(PosixPath(Path.home()), filepath[2:])
    if not os.path.exists(filepath):
        return

    # Parse configuration file
    config = ConfigParser()
    config.read(filepath)
    for k_section in config.sections():
        # Parse only supported sections

        if k_section == 'frames':
            # Parse this section only when in study mode (--frames)
            db_frames['path_output'] =  os.path.join(db['common']['directories']['frames'], f"{k_ep}")

            for k_chapter in config.options(k_section):
                value_str = config.get(k_section, k_chapter)
                value_str = value_str.replace(' ','')

                nested_dict_set(db_frames, list(), k_chapter, 'list')
                parse_framelist(db_frames[k_chapter]['list'], value_str)



def parse_frames_for_study_g(db, k_chapter_g):
    # Parse the ini file which contains the listf of frames
    # used in study mode

    nested_dict_set(db, dict(), k_chapter_g, 'video', 'frames')
    db_frames = db[k_chapter_g]['video']['frames']

    # Open configuration file
    filepath = absolute_path(
        os.path.join(
            db['common']['directories']['config'],
            k_chapter_g,
            "%s_frames.ini" % (k_chapter_g)
        )
    )
    if not os.path.exists(filepath):
        return

    # Parse configuration file
    config = ConfigParser()
    config.read(filepath)
    for k_section in config.sections():
        # Parse only supported sections

        if k_section == 'frames':
            # Parse this section only when in study mode (--frames)
            db_frames['path_output'] =  os.path.join(db['common']['directories']['frames'], f"{k_chapter_g}")

            for k_chapter in config.options(k_section):
                value_str = config.get(k_section, k_chapter)
                value_str = value_str.replace(' ','')

                nested_dict_set(db_frames, list(), k_chapter, 'list')
                parse_framelist(db_frames[k_chapter]['list'], value_str)




def parse_framelist(db_frames: list[int], framelist_str: str):
    framelist = framelist_str.split()

    for frame_no, frame in enumerate(framelist):
        # print(scene)
        frame_properties = frame.split(',')
        db_frames.append(int(frame_properties[0]))

        # precedemment
        # f_tmp = {
        #     'no': int(frame_properties[0])
        # }
        # if len(frame_properties) > 1:
        #     for f in frame_properties:
        #         d = f.split('=')
        #         if d[0] == 'filters':
        #             # custom filter
        #             f_tmp['filters'] = d[1]
        #         elif d[0] == 'ep':
        #             # custom episode
        #             if d[1] == '*':
        #                 f_tmp['k_ep'] = d[1]
        #             else:
        #                 f_tmp['k_ep'] = 'ep%02d' % (int(d[1]))
        #         elif d[0] == 'ed':
        #             # custom edition
        #             f_tmp['k_ed'] = d[1]
        # try:
        #     if f_tmp['k_ep'] == '*':
        #         for i in range(1,40):
        #             f_tmp['k_ep'] = 'ep%02d' % (i)
        #             db_frames.append(f_tmp)
        #     else:
        #         db_frames.append(f_tmp)
        # except:
        #     db_frames.append(f_tmp)

