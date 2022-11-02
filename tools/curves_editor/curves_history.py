#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# from PySide6 import QtCore
from genericpath import exists
from PySide6.QtCore import Signal
from PySide6.QtCore import QObject

from copy import deepcopy
import os
import os.path
import pprint
import configparser
from pathlib import Path
from pathlib import PosixPath
import sys

import re

from logger import log


import collections
from collections import OrderedDict


class Curves_history(object):
    def __init__(self, maxCount=5):
        super(Curves_history, self).__init__()
        self.history = []
        self.index = 0
        self.maxCount = maxCount


    def appendCurves(self, k_curve, curves):
        # print(k_curve)
        # print(curves)
        # limit the history to maxCount elements
        if self.index >= self.maxCount:
            self.history = self.history[1:]
            self.index = self.maxCount - 1

        # Remove following elements
        if self.index < len(self.history):
            self.history = self.history[0:self.index]

        # Append the element
        self.history.insert(self.index ,{
            'k_curves': k_curve,
            'curves': deepcopy(curves)})
        self.index += 1

    def getCurrentCurves(self):
        return self.history[self.index]

    def getPreviousCurves(self):
        if self.index > 0:
            return self.history[self.index - 1]
        else:
            return self.history[0]

    def getNextCurves(self):
        if self.index < len(self.history) - 1:
            return self.history[self.index + 1]
        else:
            return self.history[self.index]

    def print(self):
        print("----------------\nhistory (%d), index = %d" % (len(self.history), self.index))
        for i in range(len(self.history)):
            print("\t[%d]" % (i))
            print("\t\tk_curves: %s" % (self.history[i]['k_curves']))
            # pprint.pprint(self.history[i]['curves'])
            if self.history[i]['curves'] is not None:
                for c in ['m', 'r', 'g', 'b']:
                    valueStr = "%s=" % (c)
                    for p in self.history[i]['curves'][c].points():
                        valueStr += "(%.06f:%.06f);" % (p.x(), p.y())
                    valueStr = valueStr[:-1]
                    print("\t\t%s" % (valueStr))
        print("----------------")

