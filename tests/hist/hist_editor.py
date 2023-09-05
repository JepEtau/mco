#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import signal
import sys
from PySide6.QtWidgets import QApplication


def main():
    application = QApplication(sys.argv)

    from window_main import Window_main
    from hist import Hist

    backend = Hist()
    frontend = Window_main(backend)

    backend.set_view(frontend)
    frontend.show()
    sys.exit(application.exec())


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()