from PyQt5 import QtCore, QtGui, QtWidgets


def get_separator(width, height, fully_fixed=False):
    separator = QtWidgets.QWidget()

    if fully_fixed:
        separator.setFixedSize(width, height)

    else:
        if width == 1:
            separator.setFixedWidth(1)
            separator.setMinimumHeight(height)

        else:
            separator.setFixedHeight(1)
            separator.setMinimumWidth(width)

    separator.setStyleSheet("background-color:black;")
    return separator


class ScrollBar(QtWidgets.QScrollBar):
    def __init__(self):
        super().__init__()

        self.setStyleSheet("""
        /* VERTICAL */
        QScrollBar:vertical {
            border: none;
            background: none;
            width: 10px;
            margin: 0px 0 0px 0;
        }

        QScrollBar::handle:vertical {
            background: darkgrey;
            min-height: 26px;
        }

        QScrollBar::add-line:vertical {
            border: none;
            background: none;
        }

        QScrollBar::sub-line:vertical {
            height: 0px;
            width: 0px;
            border: none;
            background: none;
        }

        QScrollBar:up-arrow:vertical, QScrollBar::down-arrow:vertical {
            border: none;
            background: none;
            color: none;
        }

        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: none;
        }

        """)


class ButtonLabel(QtWidgets.QLabel):

    clicked = QtCore.pyqtSignal()

    def __init__(self, image_before_path, image_after_path):
        super().__init__()
        self.disabled = False
        self.is_enabled = False  # Only for buttons that stay pressed!

        self.enabled_pixmap = None
        self.before_pixmap = QtGui.QPixmap(image_before_path)
        self.after_pixmap = QtGui.QPixmap(image_after_path)
        self.setPixmap(self.before_pixmap)

    def set_disabled(self, condition=True):
        if condition:
            self.disabled = True
            opacity_25 = QtWidgets.QGraphicsOpacityEffect(self)
            opacity_25.setOpacity(0.5)
            self.setGraphicsEffect(opacity_25)

        else:
            self.disabled = False
            opacity_100 = QtWidgets.QGraphicsOpacityEffect(self)
            opacity_100.setOpacity(1.0)
            self.setGraphicsEffect(opacity_100)

    def mousePressEvent(self, ev):
        if not self.disabled:
            if QtCore.QCoreApplication.instance().mouseButtons() & QtCore.Qt.LeftButton:
                self.clicked.emit()

    def enterEvent(self, ev):
        if not self.disabled:
            self.setPixmap(self.after_pixmap)

    def leaveEvent(self, ev):
        if not self.disabled:
            if self.is_enabled:
                self.setPixmap(self.enabled_pixmap)

            else:
                self.setPixmap(self.before_pixmap)
