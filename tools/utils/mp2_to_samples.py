#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
sys.path.append('../../scripts')

from utils.time_conversions import HMS_MS
from utils.time_conversions import MS_MS
from utils.time_conversions import MS_MS
from utils.time_conversions import MS
from utils.time_conversions import HMS_MS

from utils.common import FPS

# This utility is used to round timestamp (HH:MM:SS.MS) to a multiple
# of a video frame (25fps)
SAMPLES_PER_FRAME = 1152
FREQUENCY = 48000


if __name__ == "__main__":
    while True:
        print("> ", end='')
        inputString = input()

        if inputString == 'q':
            break

        isFound = False

        if not isFound:
            _match = re.match(re.compile(HMS_MS), inputString)
            if _match:
                timestamp = int(_match[1]) * 60
                timestamp = (timestamp + int(_match[2])) * 60
                timestamp = (timestamp + int(_match[3])) * 1000
                timestamp += int(_match[4])
                isFound = True

        if not isFound:
            _match = re.match(re.compile(MS_MS), inputString)
            if _match:
                timestamp = 0
                timestamp = (timestamp + int(_match[1])) * 60
                timestamp = (timestamp + int(_match[2])) * 1000
                timestamp += int(_match[3])
                isFound = True

        if not isFound:
            _match = re.match(re.compile(MS), inputString)
            if _match:
                timestamp = 0
                timestamp = (timestamp + int(_match[1])) * 60
                timestamp = (timestamp + int(_match[2])) * 1000
                timestamp += 0
                isFound = True

        timestamp = timestamp / 1000

        # nb of MP2 frames
        nbOfMp2Frames = float(FREQUENCY * timestamp) / float(SAMPLES_PER_FRAME)

        # print("timestamp in s: %.05f" % (timestamp))
        # print("timestamp in samples: %.05f" % (timestamp * FREQUENCY))
        # print("nb of frames: %.05f" % (nbOfMp2Frames))

# 03:05.850

        if int(nbOfMp2Frames) == nbOfMp2Frames:
            timestamp = (nbOfMp2Frames*SAMPLES_PER_FRAME) / FREQUENCY
            print("multiple: %.03f" % (timestamp))
        else:
            print("not multiple")
            previous = int(nbOfMp2Frames)*SAMPLES_PER_FRAME
            next = (int(nbOfMp2Frames+.5))*SAMPLES_PER_FRAME

            timestamp =  previous / FREQUENCY
            ms = int((timestamp - int(timestamp)+0.0005) * 1000)
            timestamp_in_s = int(timestamp)
            timestamp_in_h = int(timestamp_in_s / 3600)
            hours = timestamp_in_h
            remaining_s = timestamp_in_s - (hours * 3600)
            minutes = int(remaining_s / 60)
            remaining_s = remaining_s - (minutes * 60)
            frames_count = timestamp*FPS
            print("%d\t\t%.03f\t\t%02d:%02d:%02d.%03d\t%.2f" % (
                previous,
                timestamp,
                hours,
                minutes,
                remaining_s,
                ms,
                frames_count))


            timestamp =  next / FREQUENCY
            ms = int((timestamp - int(timestamp)+0.0005) * 1000)
            timestamp_in_s = int(timestamp)
            timestamp_in_h = int(timestamp_in_s / 3600)
            hours = timestamp_in_h
            remaining_s = timestamp_in_s - (hours * 3600)
            minutes = int(remaining_s / 60)
            remaining_s = remaining_s - (minutes * 60)
            frames_count = timestamp*FPS
            print("%d\t\t%.03f\t\t%02d:%02d:%02d.%03d\t%.2f" % (next,
                timestamp, hours, minutes, remaining_s, ms,
                frames_count))
