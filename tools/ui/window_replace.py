from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMenu,
    QMessageBox,
)


from .ui.ui_window_replace import Ui_ReplaceWindow



class ReplaceWindow(QMainWindow, Ui_ReplaceWindow):

    def __init__(self, ui=None, controller=None):
        super().__init__()
        self.setupUi(self)

        self.show()
