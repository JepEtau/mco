from enum import Enum
from typing import Literal
import numpy as np
import cv2
from pprint import pprint
from nn_inference.toolbox.resize import pillow_resize
from utils.p_print import *
from utils.logger import main_logger
from utils.mco_types import Effect, McoFrame, Scene
from PIL import Image



def apply_effect(
    out_f_no: int,
    frame: McoFrame
) -> McoFrame | list[McoFrame]:
    scene: Scene = frame.scene

    if 'effects' in scene:
        effect: Effect = scene['effects'].primary_effect()
        if effect.name == 'loop' and out_f_no == effect.frame_ref:
            print(f"loop count = {effect.loop + 1}")
            return [frame] * (effect.loop + 1)

        elif effect.name == 'fadeout' and out_f_no >= effect.frame_ref:
            if out_f_no >= effect.frame_ref:
                coef: float = float(out_f_no - effect.frame_ref) / effect.fade
                img_black = np.zeros(frame.img.shape, dtype=frame.img.dtype)
                img_out: np.ndarray = cv2.addWeighted(frame.img, 1 - coef, img_black, coef, 0)
                print(f"out_i: {out_f_no}, coef={coef:.06f}")
                return McoFrame(no=frame.no, img=img_out)

        elif effect.name == 'loop_and_fadeout':
            fadeout_start = effect.frame_ref + effect.loop - effect.fade
            # print(f"fadeout_start= {fadeout_start}, out_f_no: {out_f_no}")

            if effect.fade > effect.loop and out_f_no >= fadeout_start:
                print(f"start @{out_f_no} (fadeout_start: {fadeout_start})")
                # print(f"effect.frame_ref: {effect.frame_ref} vs {scene['dst']['start'] + scene['dst']['count']}")
                img_black = np.zeros(frame.img.shape, dtype=frame.img.dtype)

                if out_f_no < effect.frame_ref:
                    i = float(out_f_no - fadeout_start)
                    coef: float = float(i) / effect.fade
                    img_out: np.ndarray = cv2.addWeighted(frame.img, 1 - coef, img_black, coef, 0)
                    print(f"out_i: {out_f_no}, coef={coef:.06f}")
                    return McoFrame(no=frame.no, img=img_out)

                elif out_f_no == effect.frame_ref:
                    out_frames: list[McoFrame] = []
                    for i in range (effect.loop + 1):
                        coef: float = float(effect.frame_ref + i - fadeout_start) / effect.fade
                        print(f"out_i: {out_f_no}, coef={coef:.06f}")
                        out_frames.append(McoFrame(
                            no=frame.no,
                            img=cv2.addWeighted(frame.img, 1 - coef, img_black, coef, 0),
                        ))
                    return out_frames

            elif out_f_no == effect.frame_ref:
                img_black = np.zeros(frame.img.shape, dtype=frame.img.dtype)
                if effect.loop >= effect.fade:
                    out_frames: list[McoFrame] = [frame] * (effect.loop - effect.fade + 1)
                else:
                    out_frames: list[McoFrame] = [frame]

                for i in range (effect.fade):
                    coef: float = float(i) / effect.fade
                    print(f"out_i: {out_f_no}, coef={coef:.06f}")
                    out_frames.append(McoFrame(
                        no=frame.no,
                        img=cv2.addWeighted(frame.img, 1 - coef, img_black, coef, 0),
                    ))
                print(yellow(f"out_frames: {len(out_frames)}"))
                return out_frames
            # else:
            #     raise NotImplementedError(effect.name)


        # else:
        #     raise NotImplementedError(effect.name)

        for effect in scene['effects'].effects:
            if effect.name == 'zoom_in' and out_f_no == effect.frame_ref:
                out_frames: list[McoFrame] = [frame]
                in_h, in_w = frame.img.shape[:2]
                for i in range (effect.loop):
                    zoom: float = float(i + 1) / effect.loop
                    out_h, out_w = int(zoom * in_w), int(zoom * in_h)
                    zoomed: np.ndarray = pillow_resize(
                        out_h, out_w, interpolation=Image.Resampling.LANCZOS
                    )
                    # crop....
                    zoomed = zoomed[out_h, out_w
                              ]

                    out_frames.append(McoFrame(
                        no=frame.no,
                        img=zoomed,
                    ))

    # else:
    #     print("no effect")

    return frame


class FadeCurve(Enum):
    LINEAR = "linear"

def coef_table(
    fade_type: Literal['in', 'out'],
    curve: FadeCurve,
    count: int
) -> np.ndarray[float]:
    if curve == FadeCurve.LINEAR:
        coefs = np.array([float(x) / count for x in range(count)])
    else:
        raise NotImplementedError("not yet implemented")
    return coefs if fade_type == 'in' else 1.0 - coefs


# def effect_loop_and_fadein(scene: Scene, effect: Effect) -> None:
#     # Validate with:
#     #   - ep02: episode

#     sys.exit("effect_loop_and_fadein")

#     # Start and count of frames for the loop
#     fadein_count = effect.fade
#     print(green(f"\tloop and fadein: loop: start={fadein_count}, fadein: count={fadein_count}"))


#     # Get hash to set the suffix
#     hash = scene['last_step']['hash']
#     step_no = scene['last_step']['step_no']
#     if hash == '':
#         # Last filter is null, use previous hash
#         previous_filter = scene['filters'][step_no - STEP_INC]
#         hash = previous_filter['hash']
#         input_filepath = get_input_path_from_shot(
#             scene=scene, task=previous_filter['task'])
#     else:
#         input_filepath = get_input_path_from_shot(
#             scene=scene)
#     suffix = "_%s" % (hash)

#     # Input directory
#     print(lightgrey("\tinput_filepath: %s" % (input_filepath)))

#     # Output directory
#     k_ep_dst = scene['dst']['k_ep']
#     k_ch_dst = scene['dst']['k_part']
#     if k_ch_dst in ['g_debut', 'g_fin']:
#         output_filepath = os.path.join(db[k_ch_dst]['cache_path'])
#     else:
#         output_filepath = os.path.join(db[k_ep_dst]['cache_path'], k_ch_dst)
#     output_filepath = os.path.join(output_filepath,
#         f"{scene['no']:03}", f"{step_no:02}")
#     if not os.path.exists(output_filepath):
#         os.makedirs(output_filepath)
#     print(lightgrey(f"\toutput_filepath: {output_filepath}"))


#     # Input image list
#     if scene['last_task'] == 'edition':
#         image_list = get_image_list_pre_replace(scene=scene,
#             folder=input_filepath,
#             step_no=step_no,
#             hash=hash)
#     elif scene['last_step']['step_no'] == scene['last_step']['step_edition']:
#         image_list = get_new_image_list(scene=scene,
#             step_no=step_no,
#             hash=scene['filters'][step_no - STEP_INC]['hash'])
#     else:
#         image_list = get_image_list(scene=scene,
#             folder=input_filepath,
#             step_no=step_no,
#             hash=hash)
#     img_input = image_list[0]

#     # Output image list
#     filename_template = FILENAME_TEMPLATE % (
#         scene['k_ep'], scene['k_ed'], step_no, suffix)
#     if scene['last_task'] == 'deinterlace':
#         start = scene['start'] + scene['count']
#         end = start + fadein_count
#     else:
#         start = scene['count']
#         end = start + fadein_count
#     output_image_list = list([os.path.join(output_filepath, filename_template % (f_no))
#         for f_no in range(end-1, start-1, -1)])

#     print(lightgrey("\toutput image count: %d" % (len(output_image_list))))
#     # pprint(output_image_list)

#     (height, width, channel_count) = scene['last_step']['shape']

#     # Create a  black image for fadeout
#     img_black = np.zeros([height, width, channel_count], dtype=np.uint8)

#     cache_strlen = len(db['common']['directories']['cache']) + 1
#     img_src = cv2.imread(img_input, cv2.IMREAD_COLOR)
#     print(lightgrey("\tinput image filepath: %s" % (img_input)))
#     for count, img_output in zip(range(fadein_count), output_image_list):
#         coef = 1 - np.power(0.5, (float(count) / fadein_count))
#         # keep print for debug until end of validation
#         print(f"\t{count:02d}: {img_input[cache_strlen:]} -> {img_output[cache_strlen:]}, coef={coef:.02f}")

#         # Mix images
#         img_dst = cv2.addWeighted(img_src, 1 - coef, img_black, coef, 0)
#         img_src = img_dst

#         cv2.imwrite(img_output, img_dst)



# def effect_loop_and_fadeout(scene: Scene, effect: Effect) -> None:
#     # Validate with:
#     #   - ep01: episode
#     #   - ep01: asuivre
#     #   - g_debut
#     verbose: bool = True

#     # Start and count of frames for the loop
#     loop_start = effect.frame_ref
#     loop_count = effect.loop
#     fadeout_count = effect.fade
#     if verbose:
#         print(lightgreen("==========================================================="))
#         pprint(scene)
#         print(green(f"\tloop and fadeout: loop: start={loop_start}, count={loop_count} / fadeout: count={fadeout_count}"))

#     hash: str = scene['task'].hashcode
#     dirname: str = task_to_dirname[scene['task'].name]
#     task_no: int = int(dirname[:2])
#     suffix: str = f"_{hash}"
#     k_ed = scene['k_ed']
#     k_ep_src = scene['k_ep']

#     # Input directory
#     in_dir: str = os.path.join(
#         get_cache_path(scene), get_dirname(scene)[0]
#     )
#     if verbose:
#         print(lightgrey(f"\tinput_filepath: {in_dir}"))

#     # Output directory
#     k_ep_dst: str = scene['dst']['k_ep']
#     k_ch_dst: str = scene['dst']['k_ch']
#     if k_ch_dst in ('g_debut', 'g_fin'):
#         out_dir: str = os.path.join(db[k_ch_dst]['cache_path'])
#     else:
#         out_dir: str = os.path.join(db[k_ep_dst]['cache_path'], k_ch_dst)
#     out_dir = os.path.join(out_dir, f"{scene['no']:03}", dirname)
#     if verbose:
#         print(lightgrey("\toutput_directory: %s" % (out_dir)))
#     os.makedirs(out_dir, exist_ok=True)

#     # Duplicate the last one
#     filename_template = IMG_FILENAME_TEMPLATE % (k_ep_src, k_ed, task_no, suffix)
#     loop_img: str = os.path.join(in_dir, filename_template % (loop_start))
#     if verbose:
#         print(lightgrey(f"\tfile used for the loop effect: {loop_img}"))

#     in_imgs: list[str] = [
#         os.path.join(in_dir, filename_template % (
#             scene['start'] + scene['count'] - (fadeout_count - loop_count) + i
#         ))
#         for i in range(fadeout_count - loop_count)
#     ]
#     in_imgs.extend([loop_img] * loop_count)
#     if verbose:
#         pprint(in_imgs)
#         print(lightgrey(f"\toutput image count: {len(in_imgs)}"))

#     out_imgs: list[str] = scene['out_frames'][-fadeout_count:]
#     if k_ch_dst in ('g_debut', 'g_fin', 'precedemment'):
#         db_video = (
#             db[k_ch_dst]['video']
#             if k_ch_dst in ('g_debut', 'g_fin')
#             else db[k_ep_src]['video']['target'][k_ch_dst]
#         )
#         if 'silence' in db_video:
#             db_video['silence']
#             out_imgs: list[str] = scene['out_frames'][-(fadeout_count + db_video['silence']):]


#     if verbose:
#         print("OUT:")
#         pprint(out_imgs)
#         print(lightgrey(f"\toutput image count: {len(out_imgs)}"))

#     img_src: np.ndarray = cv2.imread(in_imgs[0], cv2.IMREAD_COLOR)
#     img_black = np.zeros(img_src.shape, dtype=img_src.dtype)

#     cache_strlen = len(db['common']['directories']['cache']) + 1
#     for count, img_input, img_output in zip(
#         range(fadeout_count),
#         in_imgs,
#         out_imgs
#     ):
#         # Calculate coefficient: last frame is not completely black because there is always
#         # a silence after this (i.e. black frames)
#         coef = float(count) / fadeout_count
#         # keep print for debug until end of validation
#         if verbose:
#             print(f"\t{count:02d}: {img_input[cache_strlen:]} -> {img_output[cache_strlen:]}, coef={coef:.02f}")

#         # Mix images
#         img_src = cv2.imread(img_input, cv2.IMREAD_COLOR)
#         img_dst = cv2.addWeighted(img_src, 1 - coef, img_black, coef, 0)

#         cv2.imwrite(img_output, img_dst)



# def effect_fadeout(scene: Scene, effect: Effect) -> None:
#     # verified:
#     #   - ep01: documentaire
#     # warning: ep02, 'en' version
#     verbose: bool = True

#     fadeout_start = effect.frame_ref
#     fadeout_count = effect.fade

#     if verbose:
#         pprint(scene)
#         print(green(f"\tfadeout: start={fadeout_start}, count={fadeout_count}"))
#         sys.exit()
#     hash: str = scene['task'].hashcode
#     dirname: str = task_to_dirname[scene['task'].name]
#     task_no: int = int(dirname[:2])
#     suffix: str = f"_{hash}"
#     k_ed = scene['k_ed']
#     k_ep_src = scene['k_ep']

#     # Input directory
#     in_dir: str = os.path.join(
#         get_cache_path(scene),
#         get_dirname(scene)[0]
#     )
#     if verbose:
#         print(lightgrey(f"\tinput_filepath: {in_dir}"))

#     # Output directory
#     k_ep_dst: str = scene['dst']['k_ep']
#     k_ch_dst: str = scene['dst']['k_ch']
#     if k_ch_dst in ('g_debut', 'g_fin'):
#         out_dir: str = os.path.join(db[k_ch_dst]['cache_path'])
#     else:
#         out_dir: str = os.path.join(db[k_ep_dst]['cache_path'], k_ch_dst)
#     out_dir = os.path.join(out_dir, f"{scene['no']:03}", dirname)
#     if verbose:
#         print(lightgrey("\toutput_directory: %s" % (out_dir)))
#     os.makedirs(out_dir, exist_ok=True)

#     filename_template = IMG_FILENAME_TEMPLATE % (k_ep_src, k_ed, task_no, suffix)
#     in_imgs: list[str] = [
#         os.path.join(in_dir, filename_template % (f_no))
#         for f_no in range(fadeout_start, fadeout_start + fadeout_count)
#     ]
#     out_imgs: list[str] = [
#         os.path.join(out_dir, filename_template % (scene['src']['start'] + scene['src']['count'] + i))
#         for i in range(fadeout_count)
#     ]

#     img_src: np.ndarray = cv2.imread(in_imgs[0], cv2.IMREAD_COLOR)
#     img_black = np.zeros(img_src.shape, dtype=img_src.dtype)

#     cache_strlen = len(db['common']['directories']['cache']) + 1
#     for i, img_input, img_output in zip(
#         range(fadeout_count),
#         in_imgs,
#         out_imgs
#     ):
#         # Calculate coefficient: last frame is not completely black because there is always
#         # a silence after this (i.e. black frames)
#         coef = float(i) / fadeout_count
#         # keep print for debug until end of validation
#         if verbose:
#             print(f"\t{i:02d}: {img_input[cache_strlen:]} -> {img_output[cache_strlen:]}, coef={coef:.02f}")

#         # Mix images
#         img_src = cv2.imread(img_input, cv2.IMREAD_COLOR)
#         img_dst = cv2.addWeighted(img_src, 1 - coef, img_black, coef, 0)

#         cv2.imwrite(img_output, img_dst)
