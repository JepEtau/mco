#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import signal
import sys
# import pyopencl as cl
import cv2

from PySide6.QtWidgets import QApplication


def main():
    application = QApplication(sys.argv)

    from merge_stabilize.window_main import Window_main
    from merge_stabilize.model_merge_stabilize import Model_merge_stabilize

    main_model = Model_merge_stabilize()
    main_window = Window_main(main_model)

    main_model.set_view(main_window)
    main_window.show()
    sys.exit(application.exec())


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    print(cv2.ocl.haveOpenCL() )
    cv2.ocl.setUseOpenCL(True)
    print(cv2.ocl.haveOpenCL() )

    # Get platforms, both CPU and GPU
    # plat = cl.get_platforms()
    # CPU = plat[0].get_devices()
    # try:
    #     GPU = plat[1].get_devices()
    # except IndexError:
    #     GPU = "none"
    main()