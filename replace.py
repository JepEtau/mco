import signal
import os
import sys

from PySide6.QtWidgets import QApplication

from gui.replace_window import ReplaceWindow
from gui.replace_controller import ReplaceController


if os.name == 'nt':
    import ctypes
    myappid = "mco.replace"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)


def main():

    application = QApplication(sys.argv)
    controller = ReplaceController()
    main_window = ReplaceWindow()

    main_window.set_controller(controller)
    controller.set_view(main_window)

    main_window.show()

    sys.exit(application.exec())


if __name__ == "__main__":

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()

