from argparse import ArgumentParser
import os
import signal
import sys

from PySide6.QtWidgets import QApplication

sys.path.append(
    os.path.abspath(os.path.join(os.getcwd(), os.pardir))
)
from parsers import TASK_NAMES


if os.name == 'nt':
    import ctypes
    myappid = "mco.replace"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)


def main():
    parser: ArgumentParser = ArgumentParser()
    parser.add_argument(
        "--task_name",
        "-t",
        required=False,
        choices=TASK_NAMES,
        default='cg',
    )

    arguments = parser.parse_args()

    application = QApplication(sys.argv)
    application.setStyle("Fusion")
    from logger import log
    from tools.backend.geometry_controller import GeometryController
    controller = GeometryController(task_name=arguments.task_name)

    from ui.window_geometry import GeometryWindow
    main_window = GeometryWindow(controller=controller)

    # main_window.set_controller(controller)
    controller.set_view(main_window)

    main_window.show()

    sys.exit(application.exec())


if __name__ == "__main__":

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()

