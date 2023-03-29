#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import signal
import sys

from PySide6.QtWidgets import QApplication

import os
if os.name == 'nt':
    import ctypes
    myappid = 'mycompany.myproduct.subproduct.version' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

def main():
    application = QApplication(sys.argv)

    from filter_info.window_main import Window_main
    from filter_info.model_filter_info import Model_filter_info

    main_model = Model_filter_info()
    main_window = Window_main(main_model)

    main_model.set_view(main_window)
    main_window.show()
    sys.exit(application.exec())


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()