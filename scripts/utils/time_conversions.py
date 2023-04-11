# -*- coding: utf-8 -*-
import re
from datetime import datetime
from datetime import timedelta
import time
from utils.common import FPS

# Used to round timestamp (HH:MM:SS.MS) to a multiple of a video frame duration (at 25fps)

HMS_MS = "^([0-9]{1,2}):([0-9]{1,2}):([0-9]{1,2}).([0-9]{3})$"
MS_MS = "^([0-9]{1,2}):([0-9]{1,2}).([0-9]{3})$"
MS = "^([0-9]{1,2}):([0-9]{1,2})$"
TIMESTAMP_S = "^(\d*).(\d*)$"


def convert_s_to_m_s_ms(elapsed_time_s):
    minutes = int(elapsed_time_s/60)
    seconds = int(elapsed_time_s - (minutes * 60))
    milliseconds = 1000 * (elapsed_time_s - (60 * minutes + seconds))
    return minutes, seconds, milliseconds

def frames_to_ms(count:int) -> int:
    return int((float(count) * 1000) / FPS)


def ms_to_frames(ms:int) -> int:
    return int((float(ms) * FPS) / 1000)


def print_current_datetime():
    datetime_now = datetime.now()
    msg = "(%s)" % (datetime_now.strftime("%Y-%m-%d %H:%M:%S"))
    print(msg, end="", flush=True)
    startTime = time()
    return startTime


def current_datetime_str() -> str:
    datetime_now = datetime.now()
    msg = "(%s)" % (datetime_now.strftime("%Y-%m-%d %H:%M:%S"))
    return msg


def frame2sexagesimal(frameNo):
    # Time stamp
    _timestampFloat = float(frameNo)/FPS
    _timestampInt = int(_timestampFloat)
    _timestamp_ms = (100 * frameNo)/FPS - (100 * _timestampInt)
    if _timestamp_ms < 10:
        timestampStr = "%s.0%d" % (str(timedelta(seconds=_timestampInt)), _timestamp_ms)
    else:
        timestampStr = "%s.%d" % (str(timedelta(seconds=_timestampInt)), _timestamp_ms)
    return timestampStr


def timestamp2sexagesimal(timestamp):
    frameNo = int(timestamp * FPS)
    return frame2sexagesimal(frameNo)



def frame_no_to_timestamp(frame_no:int, fps=25.0):
    # Returns th frame no. converted to a timestamp (e.g. 1452.12s)
    timestamp_float = float(frame_no)/fps
    timestamp_int = int(timestamp_float)
    timestamp_ms = (100 * frame_no)/fps - (100 * timestamp_int)
    if timestamp_ms < 10:
        timestampStr = "%s.0%d" % (str(timedelta(seconds=timestamp_int)), timestamp_ms)
    else:
        timestampStr = "%s.%d" % (str(timedelta(seconds=timestamp_int)), timestamp_ms)
    return timestampStr



def frame_no_to_sexagesimal(frame_no:int, fps=25.0):
    timestamp_float = float(frame_no) / fps
    return timestamp_to_sexagesimal(timestamp_float)



def timestamp_to_sexagesimal(timestamp:float):
    # Timestamp (e.g. 1452.12s) to sexagesimal (HH:MM:SS.MS)
    ms = int((timestamp - int(timestamp)+0.0005) * 1000)
    timestamp_in_s = int(timestamp)
    timestamp_in_h = int(timestamp_in_s / 3600)
    hours = timestamp_in_h
    remaining_s = timestamp_in_s - (hours * 3600)
    minutes = int(remaining_s / 60)
    remaining_s = remaining_s - (minutes * 60)
    return "%02d:%02d:%02d.%03d" % (hours, minutes, remaining_s, ms)





if __name__ == "__main__":
    while True:
        print("> ", end='')
        inputString = input()

        if inputString == 'q':
            break

        isFound = False
        if not isFound:
            _match = re.match(re.compile(TIMESTAMP_S), inputString)
            dec = int(_match.group(2))
            if dec < 10: dec *= 100
            elif dec < 100: dec *= 10
            timestamp_ms = 1000 * int(_match.group(1)) + dec
            isFound = True
        else:
            continue

        timestamp_ms_int = float(int(float(timestamp_ms) * FPS / 1000))
        # print(timestamp_ms_int)
        # print(timestamp_ms * FPS/1000)

        if timestamp_ms * FPS/1000 == timestamp_ms_int:
            print("multiple")
        else:
            timestamp_ms_previous = timestamp_ms_int / ( FPS)
            timestamp_ms_next = (timestamp_ms_int + 1) / ( FPS)
            print("%s\n\t%.2f\t%s\n\t%.2f\t%s" % (
                inputString,
                timestamp_ms_previous, timestamp2sexagesimal(timestamp_ms_previous),
                timestamp_ms_next, timestamp2sexagesimal(timestamp_ms_next)))

