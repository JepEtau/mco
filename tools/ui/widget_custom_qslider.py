from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QSlider
from .stylesheet import set_stylesheet, set_widget_stylesheet


class CustomQSliderWidget(QSlider):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setSingleStep(1)

    def update_stylesheet(self):
        set_widget_stylesheet(self)


    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        if e.button() == Qt.LeftButton:
            e.accept()
            x = e.pos().x()
            value = int((self.maximum() - self.minimum()) * x / self.width() + self.minimum())
            self.setValue(value)
            print(f"pressed: {value}")


    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        if e.button() == Qt.LeftButton:
            e.accept()
            x = e.pos().x()
            value = int((self.maximum() - self.minimum()) * x / self.width() + self.minimum())
            self.setValue(value)
            print(f"released: {value}")
