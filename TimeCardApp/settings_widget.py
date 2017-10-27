from PyQt5 import QtWidgets, QtCore, QtGui
from extra_widgets import *


app = QtCore.QCoreApplication.instance()


class SettingsWidget(QtWidgets.QFrame):

    def __init__(self):
        super().__init__()
        self.moving = False

        self.setWindowTitle("Time Card App Settings")
        self.setFixedSize(400, 150)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Tool)
        self.setStyleSheet("background: white;")
        self.setFrameStyle(QtWidgets.QFrame.Box)

        self.main_vbox = QtWidgets.QVBoxLayout()
        self.main_vbox.setSpacing(0)
        self.main_vbox.setContentsMargins(0, 0, 0, 0)

        self.init_titlebar()

        self.main_vbox.addWidget(self.titlebar)

        self.main_vbox.addWidget(get_separator(498, 1))

        self.settings_vbox = QtWidgets.QVBoxLayout()
        self.settings_vbox.setSpacing(10)
        self.settings_vbox.setContentsMargins(10, 10, 10, 10)

        version_label = QtWidgets.QLabel(f"Version: {app.version}")
        self.settings_vbox.addWidget(version_label)

        self.check_for_updates_checkbox = QtWidgets.QCheckBox("Check for updates")

        if app.settings["check_for_updates"]:
            self.check_for_updates_checkbox.setCheckState(QtCore.Qt.Checked)

        self.check_for_updates_checkbox.stateChanged.connect(self.check_for_updates_checked)

        self.settings_vbox.addWidget(self.check_for_updates_checkbox)

        self.main_vbox.addLayout(self.settings_vbox)

        self.main_vbox.addStretch()

        self.setLayout(self.main_vbox)

    def init_titlebar(self):
        self.titlebar = QtWidgets.QWidget()
        self.titlebar.setFixedHeight(34)
        self.titlebar.setStyleSheet("background-color:lightgrey;")

        titlebar_hbox = QtWidgets.QHBoxLayout()
        titlebar_hbox.setContentsMargins(0, 0, 0, 0)
        titlebar_hbox.setSpacing(0)
        titlebar_hbox.addSpacing(3)

        window_title_label = QtWidgets.QLabel("Time Card App Settings")
        font = QtGui.QFont()
        font.setPointSize(12)
        window_title_label.setFont(font)
        titlebar_hbox.addWidget(window_title_label)

        titlebar_hbox.addStretch()

        exit_button_label = ButtonLabel(app.program_data_dir + "/images/exit_before.png",
                                        app.program_data_dir + "/images/exit_after.png")
        exit_button_label.clicked.connect(self.hide)
        exit_button_label.setToolTip("Exit")
        titlebar_hbox.addWidget(exit_button_label)
        titlebar_hbox.addSpacing(5)

        self.titlebar.setLayout(titlebar_hbox)

    def mousePressEvent(self, ev):
        if self.titlebar.geometry().contains(ev.pos()):
            self.oldPos = ev.globalPos()
            self.moving = True

    def mouseReleaseEvent(self, ev):
        self.moving = False

    def mouseMoveEvent(self, ev):
        if self.moving:
            delta = QtCore.QPoint(ev.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = ev.globalPos()

    def check_for_updates_checked(self):
        if self.check_for_updates_checkbox.checkState() == QtCore.Qt.Checked:
            app.settings["check_for_updates"] = True
            app.save_settings()

        else:
            app.settings["check_for_updates"] = False
            app.save_settings()
