# -*- coding: utf-8 -*-
from pprint import pprint
from typing_extensions import Literal
from utils.common import K_PARTS_ORDERED
from utils.time_conversions import ms_to_frames

def p_red(*values: object) -> str:
    return "\033[31m{}\033[00m" .format(values[0])


def print_red(*values: object,
            sep: str | None = " ",
            end: str | None = "\n",
            flush: Literal[False] = False):
    print("\033[31m{}\033[00m" .format(values[0]), sep=sep, end=end, flush=flush)


def print_green(*values: object,
            sep: str | None = " ",
            end: str | None = "\n",
            flush: Literal[False] = False):
    print("\033[32m{}\033[00m" .format(values[0]), sep=sep, end=end, flush=flush)


def p_orange(*values: object) -> str:
    return "\033[33m{}\033[00m".format(values[0])


def print_orange(*values: object,
            sep: str | None = " ",
            end: str | None = "\n",
            flush: Literal[False] = False):
    print("\033[33m{}\033[00m" .format(values[0]), sep=sep, end=end, flush=flush)


def print_blue(*values: object,
            sep: str | None = " ",
            end: str | None = "\n",
            flush: Literal[False] = False):
    print("\033[34m{}\033[00m" .format(values[0]), sep=sep, end=end, flush=flush)


def print_purple(*values: object,
            sep: str | None = " ",
            end: str | None = "\n",
            flush: Literal[False] = False):
    print("\033[35m{}\033[00m" .format(values[0]), sep=sep, end=end, flush=flush)


def print_cyan(*values: object,
            sep: str | None = " ",
            end: str | None = "\n",
            flush: Literal[False] = False):
    print("\033[36m{}\033[00m" .format(values[0]), sep=sep, end=end, flush=flush)


def lightgrey(*values: object) -> str:
    return "\033[37m{}\033[00m" .format(values[0])
def print_lightgrey(*values: object,
            sep: str | None = " ",
            end: str | None = "\n",
            flush: Literal[False] = False):
    print("\033[37m{}\033[00m" .format(values[0]), sep=sep, end=end, flush=flush)


def print_darkgrey(*values: object,
            sep: str | None = " ",
            end: str | None = "\n",
            flush: Literal[False] = False):
    print("\033[90m{}\033[00m" .format(values[0]), sep=sep, end=end, flush=flush)


def print_lightred(*values: object,
            sep: str | None = " ",
            end: str | None = "\n",
            flush: Literal[False] = False):
    print("\033[91m{}\033[00m" .format(values[0]), sep=sep, end=end, flush=flush)


def p_lightgreen(*values: object) -> str:
    return "\033[92m{}\033[00m" .format(values[0])
def print_lightgreen(*values: object,
            sep: str | None = " ",
            end: str | None = "\n",
            flush: Literal[False] = False):
    print("\033[92m{}\033[00m" .format(values[0]), sep=sep, end=end, flush=flush)


def p_yellow(*values: object) -> str:
    return "\033[93m{}\033[00m" .format(values[0])
def print_yellow(*values: object,
            sep: str | None = " ",
            end: str | None = "\n",
            flush: Literal[False] = False):
    print("\033[93m{}\033[00m" .format(values[0]), sep=sep, end=end, flush=flush)


def print_lightblue(*values: object,
            sep: str | None = " ",
            end: str | None = "\n",
            flush: Literal[False] = False):
    print("\033[94m{}\033[00m" .format(values[0]), sep=sep, end=end, flush=flush)


def print_pink(*values: object,
            sep: str | None = " ",
            end: str | None = "\n",
            flush: Literal[False] = False):
    print("\033[95m{}\033[00m" .format(values[0]), sep=sep, end=end, flush=flush)



def p_lightcyan(*values: object) -> str:
    return "\033[96m{}\033[00m" .format(values[0])
def print_lightcyan(*values: object,
            sep: str | None = " ",
            end: str | None = "\n",
            flush: Literal[False] = False):
    print("\033[96m{}\033[00m" .format(values[0]), sep=sep, end=end, flush=flush)



























def pprint_episode(db, k_ep):

    if False:
        # print last shot of every part
        for k_p in K_PARTS_ORDERED:
            print(f"{k_p}")
            db_video = db[k_ep]['target']['video'][k_p]
            if db_video['count'] == 0:
                continue
            print("  ", db_video['shots'][-1])

    print_lightcyan("\n              ", end='')
    print_lightcyan("total(V)".rjust(12), end='')
    print_lightcyan("total(A)".rjust(12), end='')
    print_lightcyan("avsync(A)".rjust(12), end='')
    print_lightcyan("silence(A)".rjust(12), end='')
    print_lightcyan("+adjust(A)".rjust(12), end='')
    print_lightcyan("1st shot".rjust(12), end='')
    print_lightcyan("frames".rjust(10), end='')
    print_lightcyan("loop".rjust(8), end='')
    print_lightcyan("avsync(V)".rjust(12), end='')
    print_lightcyan("")
    episode_audio_count = 0
    episode_video_count = 0
    for k_p in K_PARTS_ORDERED:
        db_video = db[k_ep]['video']['target'][k_p]
        db_audio = db[k_ep]['audio'][k_p]
        frame_count = 0
        print_lightcyan("  %s" % (k_p.ljust(12)), end='')

        if db_video['count'] == 0:
            print("%s%s" % ("0".rjust(12), "0".rjust(8)))
            continue

        part_frame_count = db_video['avsync']

        first_shot = db_video['shots'][0]

        for shot in db_video['shots']:
            frame_count += shot['count']
        last_shot = db_video['shots'][-1]

        loop_count = 0
        if 'effects' in last_shot:
            if 'loop' in last_shot['effects'][0]:
                loop_count = last_shot['effects'][2]
            try:
                if 'fadein' in db_video['shots'][0]['effects'][0]:
                    print("todo: add fadein")
            except:
                pass
        part_frame_count += frame_count + loop_count

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
        tmp_str = f"{part_frame_count}"
        print(f"{tmp_str.rjust(12)}", end='')

        # total audio count
        tmp_str = f"{db_audio['count']}"
        print(f"{tmp_str.rjust(12)}", end='')

        # avsync audio
        tmp_str = f"{ms_to_frames(db_audio['avsync'])}"
        print(f"{tmp_str.rjust(8)}", end='')

        # silence audio
        tmp_str = "%.02f" % (db_audio['silence']/1000)
        print(f"{tmp_str.rjust(12)}", end='')

        # -> padded (A)
        extra_str = f"{ms_to_frames(db_audio['avsync'] + audio_silence_padding)}"
        print(f"{extra_str.rjust(12)}", end='')


        # start of 1st shot
        start_str = f"{first_shot['start']}"
        print(f"{start_str.rjust(12)}", end='')

        # frames count (sum of shots only)
        tmp_str = f"{frame_count}"
        print(f"{tmp_str.rjust(12)}", end='')

        # loop
        tmp_str = f"{loop_count}"
        print(f"{tmp_str.rjust(12)}", end='')

        # avsync
        tmp_str = f"{db_video['avsync']}"
        print(f"{tmp_str.rjust(12)}", end='')


        print("")

        episode_audio_count += ms_to_frames(audio_duration)
        episode_video_count += part_frame_count

        # print(">>> db_audio")
        # pprint(db_audio)
        # print("-------------------")
        # print(">>> db[%s]" % (k_ep))
        # pprint(db[k_ep])

    # Append silences
    for k_p in ['episode', 'asuivre', 'documentaire']:
        silence_count = ms_to_frames(db[k_ep]['audio'][k_p]['silence'])
        episode_audio_count += silence_count
        episode_video_count += silence_count

    print("")
    print_green("audio (total count): ", end=' ')
    print("%d" % (episode_audio_count))
    print_green("video (total count): ", end=' ')
    print("%d" % (episode_video_count))
    print_green("")


def pprint_g_debut_fin(db):

    if False:
        # print last shot of every part
        for k_part_g in ['g_debut', 'g_fin']:
            print(f"{k_part_g}")
            db_video = db[k_part_g]['target']['video']
            if db_video['count'] == 0:
                continue
            print("  ", db_video['shots'][-1])

    print("\n           ", end='')
    print("total(V)".rjust(12), end='')
    print("total(A)".rjust(12), end='')
    print("avsync(A)".rjust(12), end='')
    print("silence(A)".rjust(12), end='')
    print("->extra(A)".rjust(12), end='')
    print("1st shot".rjust(12), end='')
    print("frames".rjust(10), end='')
    print("loop".rjust(8), end='')
    print("avsync(V)".rjust(12), end='')
    print("")
    for k_part_g in ['g_debut', 'g_fin']:
        episode_audio_count = 0
        episode_video_count = 0
        db_video = db[k_part_g]['video']
        db_audio = db[k_part_g]['audio']
        frame_count = 0

        if db_video['count'] == 0:
            print(f"{k_part_g.ljust(16)}", end='')
            print("\t(0)")
            continue

        first_shot = db_video['shots'][0]

        for shot in db_video['shots']:
            frame_count += shot['count']
        last_shot = db_video['shots'][-1]

        loop_count = 0
        if 'effects' in last_shot:
            if 'loop' in last_shot['effects'][0]:
                loop_count = last_shot['effects'][2]
        part_frame_count = frame_count + loop_count

        part_frame_count += db_video['avsync']

        audio_duration = 0
        audio_duration +=  db_audio['avsync']
        for segment in db_audio['segments']:
            if 'duration' in segment.keys():
                audio_duration += segment['duration']
            if 'silence' in segment.keys():
                audio_duration += segment['silence']
        if 'silence' in db_audio.keys():
            audio_duration += db_audio['silence']

        print(f"{k_part_g.ljust(8)}", end='')

        # total frames count
        tmp_str = "%d" % db_video['count']
        print(f"{tmp_str.rjust(12)}", end='')

        # total audio count
        tmp_str = "%d" % db_audio['count']
        print(f"{tmp_str.rjust(12)}", end='')


        # avsync audio
        tmp_str = "%.02f" % (db_audio['avsync']/1000)
        print(f"{tmp_str.rjust(12)}", end='')

        # silence audio
        tmp_str = "%.02f" % (db_audio['silence']/1000)
        print(f"{tmp_str.rjust(12)}", end='')

        # -> padded (A)
        extra_str = "%d" % ms_to_frames(db_audio['avsync'] + db_audio['silence'])
        print(f"{extra_str.rjust(12)}", end='')

        # start of 1st shot
        start_str = "%d" % first_shot['start']
        print(f"{start_str.rjust(14)}", end='')

        # frames count (sum of shots only)
        tmp_str = "%d" % frame_count
        print(f"{tmp_str.rjust(10)}", end='')

        # loop
        tmp_str = "%d" % loop_count
        print(f"{tmp_str.rjust(8)}", end='')

        # avsync
        tmp_str = "%d" % db_video['avsync']
        print(f"{tmp_str.rjust(8)}", end='')

        print("")

        if True:
            episode_audio_count += ms_to_frames(audio_duration)
            episode_video_count += db_video['count']
            print("  audio (count): %d" % (episode_audio_count))
            print("  video (count): %d" % (episode_video_count))
            print("")

