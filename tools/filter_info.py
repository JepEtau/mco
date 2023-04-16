#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import signal
import sys

from PySide6.QtWidgets import QApplication

import os
if os.name == 'nt':
    import ctypes
    myappid = 'mycompany.myproduct.subproduct.version' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

def main(arguments):
    application = QApplication(sys.argv)

    from filter_info.window_main import Window_main
    from filter_info.controller_filter_info import Controller_filter_info

    controller = Controller_filter_info()
    main_window = Window_main(controller)

    controller.set_view(main_window)
    main_window.show()
    controller.load_file(arguments.input)
    sys.exit(application.exec())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Filter info")
    parser.add_argument("input", nargs='?', default=None)
    arguments = parser.parse_args()

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main(arguments)