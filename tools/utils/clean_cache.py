#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.append('scripts')

import argparse
import gc
import signal

from pprint import pprint
from utils.pretty_print import *



def main():
    pass

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
