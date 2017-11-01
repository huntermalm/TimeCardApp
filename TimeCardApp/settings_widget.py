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
        self.setObjectName("hotkeyWidget")
        self.setStyleSheet(f"QWidget#hotkeyWidget {{ background: {app.active_theme['primary_color']}; }}")
        self.setFrameStyle(QtWidgets.QFrame.Box)

        self.main_vbox = QtWidgets.QVBoxLayout()
        self.main_vbox.setSpacing(0)
        self.main_vbox.setContentsMargins(0, 0, 0, 0)

        self.init_titlebar()

        self.main_vbox.addWidget(self.titlebar)

        self.main_vbox.addWidget(get_separator(2, 1))

        self.settings_vbox = QtWidgets.QVBoxLayout()
        self.settings_vbox.setSpacing(10)
        self.settings_vbox.setContentsMargins(10, 10, 10, 10)

        self.version_label = QtWidgets.QLabel(f"Version: {app.version}")
        self.version_label.setStyleSheet(f"color: {app.active_theme['font_color']}")
        self.settings_vbox.addWidget(self.version_label)

        self.check_for_updates_checkbox = QtWidgets.QCheckBox("Check for updates")
        self.check_for_updates_checkbox.setStyleSheet(f"color: {app.active_theme['font_color']};")

        self.theme_hbox = QtWidgets.QHBoxLayout()
        self.theme_hbox.setSpacing(3)

        if app.settings["check_for_updates"]:
            self.check_for_updates_checkbox.setCheckState(QtCore.Qt.Checked)

        self.check_for_updates_checkbox.stateChanged.connect(self.check_for_updates_checked)

        self.settings_vbox.addWidget(self.check_for_updates_checkbox)

        self.theme_label = QtWidgets.QLabel("Theme:")
        self.theme_label.setStyleSheet(f"color: {app.active_theme['font_color']}")
        self.theme_hbox.addWidget(self.theme_label)

        self.theme_combobox = ComboBox()
        self.theme_combobox.setFixedSize(50, 20)
        self.theme_combobox.activated.connect(self.combobox_changed)
        for theme in app.themes:
            self.theme_combobox.addItem(theme)

        self.theme_combobox.setCurrentIndex(self.theme_combobox.findText(app.settings["theme"]))

        self.theme_hbox.addWidget(self.theme_combobox)

        self.theme_hbox.addStretch()

        self.settings_vbox.addLayout(self.theme_hbox)

        self.main_vbox.addLayout(self.settings_vbox)

        self.main_vbox.addStretch()

        self.setLayout(self.main_vbox)

    def reset_stylesheet(self):
        self.version_label.setStyleSheet(f"color: {app.active_theme['font_color']}")
        self.check_for_updates_checkbox.setStyleSheet(f"color: {app.active_theme['font_color']}")
        self.theme_label.setStyleSheet(f"color: {app.active_theme['font_color']}")
        self.theme_combobox.reset_stylesheet()
        self.titlebar.setStyleSheet(f"background:{app.active_theme['secondary_color']};")
        self.setStyleSheet(f"QWidget#hotkeyWidget {{ background: {app.active_theme['primary_color']}; }}")
        self.window_title_label.setStyleSheet(f"color: {app.active_theme['font_color']};")

    def combobox_changed(self):
        app.active_theme = app.themes[self.theme_combobox.currentText()]
        app.settings["theme"] = self.theme_combobox.currentText()
        app.save_settings()

        self.reset_stylesheet()

        app.main_window.central_widget.setStyleSheet(f"background:{app.active_theme['primary_color']};")
        app.main_window.titlebar.setStyleSheet(f"background:{app.active_theme['secondary_color']};")
        app.main_window.window_title_label.setStyleSheet(f"color: {app.active_theme['font_color']};")
        app.main_window.add_project_button.setStyleSheet(f"background:{app.active_theme['primary_color']};")
        app.main_window.add_project_button.add_project_label.setStyleSheet(f"color: {app.active_theme['font_color']}")
        app.main_window.add_folder_button.setStyleSheet(f"background:{app.active_theme['primary_color']};")
        app.main_window.add_folder_button.add_folder_label.setStyleSheet(f"color: {app.active_theme['font_color']}")
        app.main_window.project_entry_widget.reset_stylesheet()
        app.main_window.folder_entry_widget.reset_stylesheet()
        app.main_window.scrollbar.reset_stylesheet()

        for file_widget in app.all_file_widgets:
            file_widget.reset_stylesheet()

    def init_titlebar(self):
        self.titlebar = QtWidgets.QWidget()
        self.titlebar.setFixedHeight(34)
        self.titlebar.setStyleSheet(f"background:{app.active_theme['secondary_color']};")

        titlebar_hbox = QtWidgets.QHBoxLayout()
        titlebar_hbox.setContentsMargins(0, 0, 0, 0)
        titlebar_hbox.setSpacing(0)
        titlebar_hbox.addSpacing(10)

        self.window_title_label = QtWidgets.QLabel("Time Card App Settings")
        self.window_title_label.setStyleSheet(f"color: {app.active_theme['font_color']};")
        font = QtGui.QFont()
        font.setPointSize(12)
        self.window_title_label.setFont(font)
        titlebar_hbox.addWidget(self.window_title_label)

        titlebar_hbox.addStretch()

        exit_button_label = ButtonLabel(app.program_data_dir + "/images/exit_before.png",
                                        app.program_data_dir + "/images/exit_after.png")
        exit_button_label.clicked.connect(self.hide)
        exit_button_label.setToolTip("Exit")
        titlebar_hbox.addWidget(exit_button_label)
        titlebar_hbox.addSpacing(10)

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
