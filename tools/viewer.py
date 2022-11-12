#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import signal
import sys

from PySide6.QtWidgets import QApplication

def main():
    application = QApplication(sys.argv)

    from viewer.window_main import Window_main
    from viewer.model_viewer import Model_viewer

    main_model = Model_viewer()
    main_window = Window_main(main_model)

    main_model.set_view(main_window)
    main_window.show()
    sys.exit(application.exec())


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()