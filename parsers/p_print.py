
from ._keys import main_chapter_keys
from utils.mco_types import Scene
from .helpers import get_fps
from utils.p_print import *
from utils.time_conversions import ms_to_frame
from ._db import db


def pprint_episode(k_ep) -> dict[str, tuple[int]]:
    """Return nb of frames of video and audio tracks"""
    fps = get_fps(db)

    # Do not show silences to fit terminal width
    show_silence: bool = False

    if False:
        # print last scene of every part
        for k_chapter in K_PARTS_ORDERED:
            print(f"{k_chapter}")
            db_video = db[k_ep]['target']['video'][k_chapter]
            if db_video['count'] == 0:
                continue
            print("  ", db_video['scenes'][-1])

    print(lightcyan("\n                "), end='')
    print(lightcyan("Video".rjust(10)), end='')
    print(lightcyan("Audio".rjust(10)), end='')
    print(lightcyan("AVsync".rjust(10)), end='')
    if show_silence:
        print(lightcyan("silence(A)".rjust(12)), end='')
    print(lightcyan("+adjust(A)".rjust(12)), end='')
    if show_silence:
        print(lightcyan("silence(V)".rjust(12)), end='')
    print(lightcyan("1st scene".rjust(12)), end='')
    print(lightcyan("frames".rjust(10)), end='')
    print(lightcyan("loop".rjust(12)), end='')
    print(lightcyan(""))
    audio_count: int = 0
    video_count: int = 0
    for k_chapter in main_chapter_keys():
        db_video = db[k_ep]['video']['target'][k_chapter]
        db_audio = db[k_ep]['audio'][k_chapter]
        frame_count = 0
        print(lightcyan("  %s" % (k_chapter.ljust(14))), end='')

        if db_video['count'] < 1:
            print("%s%s" % ("0".rjust(12), "0".rjust(8)))
            continue

        # print(red(db_video['count']))

        chapter_frame_count = db_video['avsync']

        first_scene: Scene = db_video['scenes'][0]
        for scene in db_video['scenes']:
            frame_count += scene['dst']['count']
        last_scene: Scene = db_video['scenes'][-1]

        chapter_frame_count += frame_count

        loop_count: int = 0
        if 'effects' in last_scene:
            effect = last_scene['effects'].primary_effect()
            print(f"\teffect:{last_scene['effects']}")
            if 'loop' in effect.name:
                loop_count = effect.loop
        if 'effects' in first_scene:
            effect = first_scene['effects'].primary_effect()
            if effect.name == 'loop_and_fadein':
                loop_count += effect.loop
        chapter_frame_count += loop_count

        video_silence = 0
        try:
            video_silence = db_video['silence']
        except:
            pass
        chapter_frame_count += video_silence

        audio_duration = 0
        audio_duration +=  db_audio['avsync']
        audio_silence_padding = 0
        for segment in db_audio['segments']:
            if 'duration' in segment.keys():
                audio_duration += segment['duration']
            if 'silence' in segment.keys():
                audio_duration += segment['silence']
                audio_silence_padding += segment['silence']

        # if 'silence' in db_audio.keys():
        #     audio_duration += db_audio['silence']

        # total frames count
        tmp_str = f"{chapter_frame_count}"
        print(f"{tmp_str.rjust(10)}", end='')

        # total audio count
        tmp_str = f"{db_audio['count']}"
        print(f"{tmp_str.rjust(10)}", end='')

        # avsync audio
        tmp_str = f"{ms_to_frame(db_audio['avsync'], fps)}/{db_video['avsync']}"
        print(f"{tmp_str.rjust(8)}", end='')

        # audio silence
        if show_silence:
            tmp_str = "%.02f" % (db_audio['silence']/1000)
            print(f"{tmp_str.rjust(12)}", end='')

        # -> padded (A)
        extra_str = f"{ms_to_frame(db_audio['avsync'] + audio_silence_padding, fps)}"
        print(f"{extra_str.rjust(12)}", end='')

        # video: append silence
        if show_silence:
            print(f"{str(video_silence).rjust(12)}", end='')

        # start of 1st scene
        start_str = f"{first_scene['src'].first_frame_no()}"
        print(f"{start_str.rjust(12)}", end='')

        # frames count (sum of scenes only)
        tmp_str = f"{frame_count}"
        print(f"{tmp_str.rjust(12)}", end='')

        # loop
        tmp_str = f"{loop_count}"
        if 'effects' in last_scene:
            effect = last_scene['effects'].primary_effect()
            if effect.name == 'loop_and_fadeout':
                tmp_str = f"{loop_count}({effect.fade})"
        print(f"{tmp_str.rjust(12)}", end='')

        print("")

        audio_count += ms_to_frame(audio_duration, fps)
        video_count += chapter_frame_count

        # print(">>> db_audio")
        # pprint(db_audio)
        # print("-------------------")
        # print(">>> db[%s]" % (k_ep))
        # pprint(db[k_ep])

    # Append silences
    for k_chapter in ['episode', 'asuivre', 'documentaire']:
        silence_count = ms_to_frame(db[k_ep]['audio'][k_chapter]['silence'], fps)
        audio_count += silence_count
        video_count += silence_count

    print("")
    print(green(f" Audio track: {audio_count}"))
    print(green(f" Video track: {video_count}"))
    print("")

    return {
        k_ep: (video_count, audio_count)
    }



def pprint_g_debut_fin() -> dict[str, tuple[int]]:
    # Do not show silences to fit terminal width
    show_silence: bool = False

    fps = get_fps(db)

    if False:
        # print last scene of every part
        for k_chapter_g in ('g_debut', 'g_fin'):
            print(f"{k_chapter_g}")
            video_track = db[k_chapter_g]['target']['video']
            if video_track['count'] == 0:
                continue
            print("  ", video_track['scenes'][-1])

    print("\n           ", end='')
    print("Video".rjust(12), end='')
    print("Audio".rjust(12), end='')
    print("avsync(A)".rjust(12), end='')
    if show_silence:
        print("silence(A)".rjust(12), end='')
    print("->extra(A)".rjust(12), end='')
    print("1st scene".rjust(12), end='')
    print("frames".rjust(10), end='')
    print("loop".rjust(8), end='')
    print("avsync(V)".rjust(12), end='')
    print("")
    frames: dict[str, tuple[int]] = {}
    for k_chapter_g in ('g_debut', 'g_fin'):
        audio_count = 0
        video_count = 0
        video_track = db[k_chapter_g]['video']
        audio_track = db[k_chapter_g]['audio']
        frame_count = 0

        if video_track['count'] == 0:
            print(f"{k_chapter_g.ljust(16)}", end='')
            print("\t(0)")
            continue

        first_scene: Scene = video_track['scenes'][0]
        for scene in video_track['scenes']:
            frame_count += scene['dst']['count']
        last_scene: Scene = video_track['scenes'][-1]

        loop_count: int = 0
        if 'effects' in last_scene:
            print(last_scene['effects'])
            effect = last_scene['effects'].primary_effect()
            if 'loop' in effect.name:
                loop_count = effect.loop
        chapter_frame_count = frame_count + loop_count

        chapter_frame_count += video_track['avsync']

        audio_duration = 0
        audio_duration +=  audio_track['avsync']
        for segment in audio_track['segments']:
            if 'duration' in segment.keys():
                audio_duration += segment['duration']
            if 'silence' in segment.keys():
                audio_duration += segment['silence']
        if 'silence' in audio_track.keys():
            audio_duration += audio_track['silence']

        print(f"{k_chapter_g.ljust(8)}", end='')

        # total frames count
        tmp_str = f"{video_track['count']}"
        print(f"{tmp_str.rjust(12)}", end='')

        # total audio count
        tmp_str = f"{audio_track['count']}"
        print(f"{tmp_str.rjust(12)}", end='')


        # avsync audio
        tmp_str = "%.02f" % (audio_track['avsync']/1000)
        print(f"{tmp_str.rjust(12)}", end='')

        # silence audio
        if show_silence:
            tmp_str = "%.02f" % (audio_track['silence']/1000)
            print(f"{tmp_str.rjust(12)}", end='')

        # -> padded (A)
        extra_str = f"{ms_to_frame(audio_track['avsync'] + audio_track['silence'], fps)}"
        print(f"{extra_str.rjust(12)}", end='')

        # start of 1st scene
        start_str = f"{first_scene['src'].first_frame_no()}"
        print(f"{start_str.rjust(14)}", end='')

        # frames count (sum of scenes only)
        tmp_str = f"{frame_count}"
        print(f"{tmp_str.rjust(10)}", end='')

        # loop
        tmp_str = f"{loop_count}"
        print(f"{tmp_str.rjust(8)}", end='')

        # avsync
        tmp_str = f"{video_track['avsync']}"
        print(f"{tmp_str.rjust(8)}", end='')

        audio_count += ms_to_frame(audio_duration, fps)
        video_count += video_track['count']
        print("")
        print(green(f" Audio track: {audio_count}"))
        print(green(f" Video track: {video_count}"))
        print("")

        frames[k_chapter_g] = (video_count, audio_count)

    return frames




def pprint_scene_mapping(scene: Scene) -> None:
    print(lightgreen(f"    {scene['no']}".rjust(8)), end=':')
    if 'ref' in scene:
        print(lightgreen(f"{scene['ref']['start']}".rjust(6)), end='')
        print(lightgreen(f"  ({scene['ref']['count']})".rjust(8)), end='')
    else:
        print(lightgreen(" ..."), end='')

    print(f"  <- ", end='')
    print(f"{scene['dst']['count']}".rjust(4), end='  ')

    for s in scene['src'].scenes():
        _k_ed, _k_ep, _k_ch, _no = s['k_ed_ep_ch_no']
        print(f" {_k_ed}:{_k_ep}:{_k_ch}:{_no: 3}".rjust(10), end='')
        print(f" {s['start']}".rjust(10), end='')
        print(f"{s['count']}".rjust(8), end='')
        if len(scene['src']) > 1:
            print(', ', end='')
    print()
