import signal
import os
import sys

sys.path.append(
    os.path.abspath(os.path.join(os.getcwd(), os.pardir))
)

from PySide6.QtWidgets import QApplication

if os.name == 'nt':
    import ctypes
    myappid = "mco.deshake"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)


def main():

    application = QApplication(sys.argv)
    from logger import log

    from tools.backend.deshake_controller import DeshakeController
    controller = DeshakeController()

    from ui.window_replace import DeshakeWindow
    main_window = DeshakeWindow(controller=controller)

    # main_window.set_controller(controller)
    controller.set_view(main_window)

    main_window.show()

    sys.exit(application.exec())


if __name__ == "__main__":

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()

