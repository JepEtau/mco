from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSlider



class CustomQSliderWidget(QSlider):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setSingleStep(1)


    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        if e.button() == Qt.LeftButton:
            e.accept()
            x = e.pos().x()
            value = (self.maximum() - self.minimum()) * x / self.width() + self.minimum()
            self.setValue(value)
