#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import signal
import sys
import cv2

from PySide6.QtWidgets import QApplication

import os
if os.name == 'nt':
    import ctypes
    myappid = 'mycompany.myproduct.subproduct.version' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

def main():
    application = QApplication(sys.argv)

    from video_editor.window_main import Window_main
    from video_editor.model_video_editor import Model_video_editor

    main_model = Model_video_editor()
    main_window = Window_main(main_model)

    main_model.set_view(main_window)
    main_window.show()
    sys.exit(application.exec())


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # print(cv2.ocl.haveOpenCL() )
    # if cv2.ocl.haveOpenCL():
    #     cv2.ocl.setUseOpenCL(True)
    # print(cv2.ocl.haveOpenCL() )

    main()