import os
import sys
import pickle
import requests
import win32api
from project import Project
from datetime import datetime
from bs4 import BeautifulSoup as soup
from PyQt5 import QtCore, QtGui, QtWidgets
from urllib.request import urlopen as uReq
from urllib import error
from GithubUpdater import get_latest_version


version = "1.2.2"
project_url = "https://github.com/huntermalm/TimeCardApp/"

app_data_dir = os.getenv("LOCALAPPDATA")
user_data_dir = f"{app_data_dir}\\Time Card App\\"
program_data_dir = os.getcwd() + "\\data"

monitor_handle = win32api.EnumDisplayMonitors()[0][0]
monitor_info = win32api.GetMonitorInfo(monitor_handle)
working_width = monitor_info["Work"][2]
working_height = monitor_info["Work"][3]

app = QtWidgets.QApplication(sys.argv)

# Load Settings
try:
    with open(user_data_dir + "settings", "rb") as f:
        settings = pickle.load(f)

except FileNotFoundError:
    settings = {
        "version": "1.2.2",
        "check_for_updates": True
    }

# Load Project Data
try:
    with open(user_data_dir + "project_data", "rb") as f:
        project_data = pickle.load(f)

except FileNotFoundError:
    project_data = []


def save_settings():
    with open(user_data_dir + "settings", "wb") as f:
        pickle.dump(settings, f, protocol=3)


def save_project_data():
    with open(user_data_dir + "project_data", "wb") as f:
        pickle.dump(project_data, f, protocol=3)


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
            if app.mouseButtons() & QtCore.Qt.LeftButton:
                self.clicked.emit()

    def enterEvent(self, ev):
        if not self.disabled and not self.is_enabled:
            self.setPixmap(self.after_pixmap)

    def leaveEvent(self, ev):
        if not self.disabled and not self.is_enabled:
            self.setPixmap(self.before_pixmap)


class ProjectOptionsWidget(QtWidgets.QWidget):

    def __init__(self, parent_project_widget):
        super().__init__()
        self.parent_project_widget = parent_project_widget
        self.setContentsMargins(0, 0, 0, 0)
        self.setAttribute(QtCore.Qt.WA_StyledBackground)
        self.setStyleSheet("background-color:lightgrey;")
        self.setFixedHeight(50)

        self.project_options_hbox = QtWidgets.QHBoxLayout()
        self.project_options_hbox.setContentsMargins(0, 0, 0, 0)
        self.project_options_hbox.setSpacing(0)
        self.project_options_hbox.addStretch()

        delete_button_label = ButtonLabel(program_data_dir + "/images/delete_before.png", program_data_dir + "/images/delete_after.png")
        delete_button_label.clicked.connect(self.delete_pressed)
        self.project_options_hbox.addWidget(delete_button_label)
        self.project_options_hbox.addSpacing(35)

        self.setLayout(self.project_options_hbox)

        self.shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(50)
        self.shadow.setXOffset(0)
        self.shadow_widget = QtWidgets.QWidget(self)
        self.shadow_widget.setFixedHeight(45)
        self.shadow_widget.setMinimumWidth(working_width)
        # self.shadow_widget.setStyleSheet("background-color:black;")
        self.shadow_widget.setGraphicsEffect(self.shadow)
        self.shadow_widget.move(0, -45)

    def delete_pressed(self):
        main_window = self.parent().parent().parent().parent().parent()

        restore_buttons = False

        for count, project_widget in enumerate(main_window.project_widgets):
            if project_widget is self.parent_project_widget:
                project_widget.hide()
                project_widget.deleteLater()

                project_widget.separator.hide()
                project_widget.separator.deleteLater()

                self.hide()
                self.deleteLater()

                project_widget.project_options_separator.hide()
                project_widget.project_options_separator.deleteLater()

                for project_count, user_project in enumerate(project_data):
                    if project_widget.project is user_project:
                        del project_data[project_count]
                        break

                save_project_data()

                restore_buttons = project_widget.active

                del main_window.project_widgets[count]
                break

        if restore_buttons:
            for project_widget in main_window.project_widgets:
                project_widget.start_button_label.set_disabled(False)


class ProjectWidget(QtWidgets.QWidget):

    def __init__(self, user_project):
        super().__init__()
        self.active = False
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.tick)
        self.setContentsMargins(0, 0, 0, 0)
        self.project = user_project
        self.setFixedHeight(45)

        self.separator = get_separator(500, 1)

        self.project_options_widget = ProjectOptionsWidget(self)
        self.project_options_widget.hide()
        self.project_options_separator = get_separator(500, 1)
        self.project_options_separator.hide()
        self.is_showing_options = False

        project_widget_hbox = QtWidgets.QHBoxLayout()
        project_widget_hbox.setSpacing(0)
        project_widget_hbox.setContentsMargins(0, 0, 0, 0)
        project_widget_hbox.addSpacing(5)

        project_name_label = QtWidgets.QLabel(self.project.name)
        project_name_label_font = QtGui.QFont()
        project_name_label_font.setPointSize(16)
        project_name_label.setFont(project_name_label_font)
        project_widget_hbox.addWidget(project_name_label)

        project_widget_hbox.addStretch()

        project_widget_hbox.addSpacing(20)

        self.project_time_label = QtWidgets.QLabel()

        self.total_time = 0

        if self.project.times:
            for time in self.project.times:
                self.total_time += (time[1] - time[0]).total_seconds()

            self.update_project_time_label()

        else:
            self.project_time_label.setText("— —")

        project_widget_hbox.addWidget(self.project_time_label)

        project_widget_hbox.addSpacing(20)

        self.start_button_label = ButtonLabel(program_data_dir + "/images/start_before.png", program_data_dir + "/images/start_after.png")
        self.start_button_label.clicked.connect(self.start_pressed)
        project_widget_hbox.addWidget(self.start_button_label)

        project_widget_hbox.addWidget(get_separator(1, 18, fully_fixed=True))

        self.end_button_label = ButtonLabel(program_data_dir + "/images/end_before.png", program_data_dir + "/images/end_after.png")
        self.end_button_label.clicked.connect(self.end_pressed)
        self.end_button_label.set_disabled()
        project_widget_hbox.addWidget(self.end_button_label)

        project_widget_hbox.addSpacing(10)

        edit_button_label = ButtonLabel(program_data_dir + "/images/edit_before.png", program_data_dir + "/images/edit_after.png")
        edit_button_label.clicked.connect(self.edit_pressed)
        project_widget_hbox.addWidget(edit_button_label)

        project_widget_hbox.addSpacing(25)

        self.setLayout(project_widget_hbox)

    def edit_pressed(self):
        main_window = self.parent().parent().parent().parent().parent()

        if self.is_showing_options:
            self.is_showing_options = False
            self.project_options_widget.hide()
            self.project_options_separator.hide()

        else:
            for project_widget in main_window.project_widgets:
                if project_widget is not self and project_widget.is_showing_options:
                    project_widget.is_showing_options = False
                    project_widget.project_options_widget.hide()
                    project_widget.project_options_separator.hide()

            self.is_showing_options = True
            self.project_options_widget.show()
            self.project_options_separator.show()

    def start_pressed(self):
        self.start_time = datetime.now()
        self.timer.start(1000)

        main_window = self.parent().parent().parent().parent().parent()

        self.active = True

        self.start_button_label.set_disabled()
        self.end_button_label.set_disabled(False)

        for project_widget in main_window.project_widgets:
            if project_widget is not self:
                project_widget.start_button_label.set_disabled()

    def end_pressed(self):
        end_time = datetime.now()
        self.timer.stop()
        time_tuple = (self.start_time, end_time)
        self.project.times.append(time_tuple)

        main_window = self.parent().parent().parent().parent().parent()
        save_project_data()

        self.total_time = 0

        for time in self.project.times:
            self.total_time += (time[1] - time[0]).total_seconds()

        self.update_project_time_label()

        main_window = self.parent().parent().parent().parent().parent()

        self.active = False

        self.end_button_label.set_disabled()
        self.start_button_label.set_disabled(False)

        for project_widget in main_window.project_widgets:
            if project_widget is not self:
                project_widget.start_button_label.set_disabled(False)

    def tick(self):
        self.total_time = 0

        for time in self.project.times:
            self.total_time += (time[1] - time[0]).total_seconds()

        self.total_time += (datetime.now() - self.start_time).total_seconds()

        self.update_project_time_label()

    def update_project_time_label(self):
        d = divmod(self.total_time, 86400)
        h = divmod(d[1], 3600)
        m = divmod(h[1], 60)
        s = m[1]

        h_string = str(int(h[0]))
        m_string = str(int(m[0]))
        s_string = str(round(s))

        if len(h_string) == 1:
            h_string = f"0{h_string}"
        if len(m_string) == 1:
            m_string = f"0{m_string}"
        if len(s_string) == 1:
            s_string = f"0{s_string}"

        self.project_time_label.setText(f"{h_string}:{m_string}:{s_string}")


class ProjectEntryWidget(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)
        self.setAttribute(QtCore.Qt.WA_StyledBackground)
        self.setStyleSheet("background-color:white;")
        self.setFixedHeight(45)

        project_entry_hbox = QtWidgets.QHBoxLayout()
        project_entry_hbox.setContentsMargins(0, 0, 0, 0)
        project_entry_hbox.setSpacing(0)
        project_entry_hbox.addSpacing(5)

        project_name_label = QtWidgets.QLabel("Project Name:")
        project_name_label_font = QtGui.QFont()
        project_name_label_font.setPointSize(16)
        project_name_label.setFont(project_name_label_font)
        project_entry_hbox.addWidget(project_name_label)

        project_entry_hbox.addSpacing(5)

        self.line_edit = QtWidgets.QLineEdit()
        line_edit_font = QtGui.QFont()
        line_edit_font.setPointSize(16)
        self.line_edit.setFont(line_edit_font)
        self.line_edit.setFixedHeight(30)
        self.line_edit.textChanged.connect(self.enable_check_button_label)
        self.line_edit.returnPressed.connect(self.confirm)
        project_entry_hbox.addWidget(self.line_edit)
        project_entry_hbox.addSpacing(10)

        self.check_button_label = ButtonLabel(program_data_dir + "/images/check_before.png", program_data_dir + "/images/check_after.png")
        self.check_button_label.caution_pixmap = QtGui.QPixmap(program_data_dir + "/images/caution.png")
        self.check_button_label.clicked.connect(self.confirm)
        self.check_button_label.set_disabled()
        self.check_button_label.setToolTip("Confirm")
        project_entry_hbox.addWidget(self.check_button_label)
        project_entry_hbox.addSpacing(10)

        self.cancel_button_label = ButtonLabel(program_data_dir + "/images/cancel_before.png", program_data_dir + "/images/cancel_after.png")
        self.cancel_button_label.clicked.connect(self.cancel)
        self.cancel_button_label.setToolTip("Cancel")
        project_entry_hbox.addWidget(self.cancel_button_label)

        project_entry_hbox.addSpacing(25)

        self.setLayout(project_entry_hbox)

    def cancel(self):
        main_window = self.parent().parent().parent().parent().parent()
        main_window.add_project_button.show()
        main_window.add_project_button.enterEvent(None)
        self.hide()

    def confirm(self):
        if not self.check_button_label.disabled:
            new_project = Project(self.line_edit.text())
            self.line_edit.clear()

            main_window = self.parent().parent().parent().parent().parent()
            scroll_widget_vbox = main_window.scroll_widget_vbox

            project_data.append(new_project)

            new_project_widget = ProjectWidget(new_project)
            scroll_widget_vbox.insertWidget(scroll_widget_vbox.count() - 4, new_project_widget)
            main_window.project_widgets.append(new_project_widget)

            for project_widget in main_window.project_widgets:
                if project_widget.active:
                    new_project_widget.start_button_label.set_disabled()

            scroll_widget_vbox.insertWidget(scroll_widget_vbox.count() - 4, new_project_widget.separator)
            scroll_widget_vbox.insertWidget(scroll_widget_vbox.count() - 4, new_project_widget.project_options_widget)
            scroll_widget_vbox.insertWidget(scroll_widget_vbox.count() - 4, new_project_widget.project_options_separator)

            save_project_data()
            main_window.add_project_button.show()
            self.hide()

            scrollbar = main_window.scroll_area.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def enable_check_button_label(self):
        disable = False
        same_name = False

        new_project_name = self.line_edit.text().strip()

        if new_project_name:
            main_window = self.parent().parent().parent().parent().parent()

            same_name = False

            for user_project in project_data:
                if user_project.name == new_project_name:
                    same_name = True
                    disable = True

            else:
                self.check_button_label.setPixmap(self.check_button_label.before_pixmap)
                self.check_button_label.set_disabled(False)
                self.check_button_label.setToolTip("Confirm")

        else:
            disable = True

        if disable:
            if same_name:
                self.check_button_label.set_disabled()
                self.check_button_label.setPixmap(self.check_button_label.caution_pixmap)
                self.check_button_label.setToolTip("A project with this name already exists.")

            else:
                self.check_button_label.set_disabled()
                self.check_button_label.setToolTip("Confirm")


class AddProjectButton(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        # self.shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        # self.shadow.setBlurRadius(10)
        # self.shadow.setXOffset(0)
        # self.setGraphicsEffect(self.shadow)
        self.setContentsMargins(0, 0, 0, 0)
        self.setAttribute(QtCore.Qt.WA_StyledBackground)
        self.setStyleSheet("background-color:white;")
        self.setFixedHeight(45)

        add_project_button_hbox = QtWidgets.QHBoxLayout()
        add_project_button_hbox.setSpacing(0)
        add_project_button_hbox.setContentsMargins(0, 0, 0, 0)
        add_project_button_hbox.addSpacing(10)

        self.plus_before_pixmap = QtGui.QPixmap(program_data_dir + "/images/plus_before.png")
        self.plus_after_pixmap = QtGui.QPixmap(program_data_dir + "/images/plus_after.png")
        self.plus_label = QtWidgets.QLabel()
        self.plus_label.setPixmap(self.plus_before_pixmap)
        add_project_button_hbox.addWidget(self.plus_label)
        add_project_button_hbox.addSpacing(10)

        add_project_label = QtWidgets.QLabel("Add Project")
        add_project_label_font = QtGui.QFont()
        add_project_label_font.setPointSize(16)
        add_project_label.setFont(add_project_label_font)
        add_project_button_hbox.addWidget(add_project_label)

        add_project_button_hbox.addStretch()

        self.setLayout(add_project_button_hbox)

    def mousePressEvent(self, ev):
        main_window = self.parent().parent().parent().parent().parent()

        main_window.add_project_button.hide()
        main_window.project_entry_widget.show()
        main_window.project_entry_widget.line_edit.setFocus(True)

    def enterEvent(self, ev):
        self.setStyleSheet("background-color:lightgrey;")
        self.plus_label.setPixmap(self.plus_after_pixmap)

    def leaveEvent(self, ev):
        self.setStyleSheet("background-color:white;")
        self.plus_label.setPixmap(self.plus_before_pixmap)


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

        version_label = QtWidgets.QLabel(f"Version: {version}")
        self.settings_vbox.addWidget(version_label)

        self.check_for_updates_checkbox = QtWidgets.QCheckBox("Check for updates")

        if settings["check_for_updates"]:
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

        exit_button_label = ButtonLabel(program_data_dir + "/images/exit_before.png", program_data_dir + "/images/exit_after.png")
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
            settings["check_for_updates"] = True
            save_settings()

        else:
            settings["check_for_updates"] = False
            save_settings()


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()
        self.pinned = False
        self.moving = False
        # self.project_data = load_project_data()
        self.settings_widget = SettingsWidget()
        self.setWindowTitle("Time Card App")
        self.width = 500
        self.height = 500
        # self.setFixedSize(self.width, self.height)
        self.setMinimumWidth(500)
        self.setMinimumHeight(500)
        self.setWindowFlags(QtCore.Qt.CustomizeWindowHint | QtCore.Qt.Tool)
        # self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Tool)
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.installEventFilter(self)
        self.setContentsMargins(0, 0, 0, 0)
        self.set_main_position()

        self.init_central_widget()

        self.setCentralWidget(self.central_widget)

        self.createActions()
        self.createTrayIcon()
        self.setIcon()
        self.trayIcon.show()

    def eventFilter(self, object, event):
        if not self.settings_widget.isVisible():
            if event.type() == QtCore.QEvent.WindowDeactivate:
                if(not self.trayIcon.geometry().contains(QtGui.QCursor().pos()) and
                   not object.geometry().contains(QtGui.QCursor().pos()) and
                   not self.pinned):
                    self.minimize()

        return 0

    def set_main_position(self):
        self.move(working_width - self.width - 7, working_height - self.height - 6)

    def init_titlebar(self):
        self.titlebar = QtWidgets.QWidget()
        self.titlebar.setFixedHeight(34)
        self.titlebar.setContentsMargins(0, 0, 0, 0)
        self.titlebar.setStyleSheet("background-color:lightgrey;")

        titlebar_hbox = QtWidgets.QHBoxLayout()
        titlebar_hbox.setContentsMargins(0, 0, 0, 0)
        titlebar_hbox.setSpacing(0)
        titlebar_hbox.addSpacing(3)

        window_title_label = QtWidgets.QLabel("Time Card App")
        font = QtGui.QFont()
        font.setPointSize(14)
        window_title_label.setFont(font)
        titlebar_hbox.addWidget(window_title_label)

        titlebar_hbox.addStretch()

        self.pin_button_label = ButtonLabel(program_data_dir + "/images/pin_before.png", program_data_dir + "/images/pin_after.png")
        self.pin_button_label.clicked.connect(self.pin)
        self.pin_button_label.setToolTip("Pin the window")
        titlebar_hbox.addWidget(self.pin_button_label)
        titlebar_hbox.addSpacing(5)

        settings_button_label = ButtonLabel(program_data_dir + "/images/gear_before.png", program_data_dir + "/images/gear_after.png")
        settings_button_label.clicked.connect(self.settings_widget.show)
        settings_button_label.setToolTip("Settings")
        titlebar_hbox.addWidget(settings_button_label)
        titlebar_hbox.addSpacing(5)

        minimize_button_label = ButtonLabel(program_data_dir + "/images/minimize_black.png", program_data_dir + "/images/minimize_green.png")
        minimize_button_label.clicked.connect(self.minimize)
        minimize_button_label.setToolTip("Minimize to system tray")
        titlebar_hbox.addWidget(minimize_button_label)
        titlebar_hbox.addSpacing(5)

        exit_button_label = ButtonLabel(program_data_dir + "/images/exit_before.png", program_data_dir + "/images/exit_after.png")
        exit_button_label.clicked.connect(self.exit)
        exit_button_label.setToolTip("Exit")
        titlebar_hbox.addWidget(exit_button_label)
        titlebar_hbox.addSpacing(5)

        self.titlebar.setLayout(titlebar_hbox)

    def init_central_widget(self):
        self.central_widget = QtWidgets.QWidget()
        self.central_widget.setContentsMargins(0, 0, 0, 0)
        self.central_widget.setStyleSheet("background-color:white;")

        main_hbox = QtWidgets.QHBoxLayout()
        main_hbox.setSpacing(0)
        main_hbox.setContentsMargins(0, 0, 0, 0)

        self.main_vbox = QtWidgets.QVBoxLayout()
        self.main_vbox.setSpacing(0)
        self.main_vbox.setContentsMargins(0, 0, 0, 0)

        self.main_vbox.addWidget(get_separator(500, 1))

        self.init_titlebar()

        self.main_vbox.addWidget(self.titlebar)

        self.main_vbox.addWidget(get_separator(500, 1))

        self.init_scroll_widget()
        self.main_vbox.addWidget(self.scroll_area)

        # self.main_vbox.addStretch()

        main_hbox.addLayout(self.main_vbox)

        self.central_widget.setLayout(main_hbox)

    def init_scroll_widget(self):
        self.scroll_widget = QtWidgets.QWidget()
        self.scroll_widget.setContentsMargins(0, 0, 0, 0)

        self.scroll_widget_vbox = QtWidgets.QVBoxLayout()
        self.scroll_widget_vbox.setSpacing(0)
        self.scroll_widget_vbox.setContentsMargins(0, 0, 0, 0)

        self.project_widgets = []

        for user_project in project_data:
            project_widget = ProjectWidget(user_project)
            self.project_widgets.append(project_widget)
            self.scroll_widget_vbox.addWidget(project_widget)
            self.scroll_widget_vbox.addWidget(project_widget.separator)

            self.scroll_widget_vbox.addWidget(project_widget.project_options_widget)
            self.scroll_widget_vbox.addWidget(project_widget.project_options_separator)

        self.add_project_button = AddProjectButton()
        # self.add_project_button.clicked.connect(self.create_project)
        self.scroll_widget_vbox.addWidget(self.add_project_button)

        self.project_entry_widget = ProjectEntryWidget()
        self.project_entry_widget.hide()
        self.scroll_widget_vbox.addWidget(self.project_entry_widget)

        self.scroll_widget_vbox.addWidget(get_separator(500, 1))

        self.scroll_widget_vbox.addStretch()

        self.scroll_widget.setLayout(self.scroll_widget_vbox)

        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setVerticalScrollBar(ScrollBar())
        self.scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        # self.scroll_area.setFixedSize(500, 464)
        self.scroll_area.setMinimumWidth(500)
        # self.scroll_area.setMinimumHeight(464)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll_area.setWidget(self.scroll_widget)

    def createActions(self):
        self.minimizeAction = QtWidgets.QAction("Mi&nimize", self,
                                                triggered=self.minimize)

        self.restoreAction = QtWidgets.QAction("&Restore", self,
                                               triggered=self.restore)

        self.quitAction = QtWidgets.QAction("&Quit", self,
                                            triggered=self.exit)

    def resizeEvent(self, ev):
        self.current_size = self.size()

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

    def pin(self):
        if self.pin_button_label.is_enabled:
            self.pin_button_label.is_enabled = False
            self.pin_button_label.setPixmap(self.pin_button_label.after_pixmap)

            self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowStaysOnTopHint)
            self.pinned = False
            self.restore()

        else:
            self.pin_button_label.is_enabled = True
            pin_pressed_pixmap = QtGui.QPixmap(program_data_dir + "/images/pin_pressed.png")
            self.pin_button_label.setPixmap(pin_pressed_pixmap)

            self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
            self.pinned = True
            self.restore()

    def minimize(self):
        self.hide()

    def restore(self):
        self.resize(self.current_size)
        self.showNormal()
        self.activateWindow()

    def exit(self):
        for project_widget in self.project_widgets:
            if project_widget.active:
                project_widget.end_pressed()
                break

        save_settings()

        self.trayIcon.hide()
        app.quit()

    def setIcon(self):
        icon = QtGui.QIcon(program_data_dir + "/images/icon.png")
        self.trayIcon.setIcon(icon)
        self.setWindowIcon(icon)

        self.trayIcon.setToolTip("Time Card App")

    def createTrayIcon(self):
        self.trayIconMenu = QtWidgets.QMenu(self)
        self.trayIconMenu.addAction(self.minimizeAction)
        self.trayIconMenu.addAction(self.restoreAction)
        self.trayIconMenu.addSeparator()
        self.trayIconMenu.addAction(self.quitAction)

        self.trayIcon = QtWidgets.QSystemTrayIcon(self)
        self.trayIcon.setContextMenu(self.trayIconMenu)
        self.trayIcon.activated.connect(self.iconActivated)

    def iconActivated(self, reason):
        if reason in (QtWidgets.QSystemTrayIcon.Trigger, QtWidgets.QSystemTrayIcon.DoubleClick):
            self.restore()


class UpdateDownloadWidget(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Downloading Update...")
        self.setFixedSize(300, 100)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)

        self.init_download_url_and_filename(project_url)

        self.hbox = QtWidgets.QHBoxLayout()

        self.vbox = QtWidgets.QVBoxLayout()
        self.vbox.addStretch()

        file_name_label = QtWidgets.QLabel(self.file_name)
        self.vbox.addWidget(file_name_label)

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.sizeHint()
        self.vbox.addWidget(self.progress_bar)

        self.vbox.addStretch()

        self.hbox.addLayout(self.vbox)

        self.setLayout(self.hbox)

    def init_download_url_and_filename(self, project_url):
        if project_url[-1] == "/":
            project_url = project_url[0:-1]

        latest_release_url = f"{project_url}/releases/latest"
        uClient = uReq(latest_release_url)
        page_html = uClient.read()
        uClient.close()
        page_soup = soup(page_html, "html.parser")
        download = page_soup.findAll("ul", {"class": "release-downloads"})[0]

        self.download_url = "https://github.com" + download.li.a["href"]
        self.file_name = self.download_url.split('/')[-1]

    def download_update(self):
        dl = 0

        with open(user_data_dir + self.file_name, "wb") as f:
            response = requests.get(self.download_url, stream=True)
            total_length = response.headers.get('content-length')

            if total_length is None:
                f.write(response.content)

            else:
                for data in response.iter_content(1024):
                    dl += len(data)
                    f.write(data)
                    amount_done = int(100 * dl / int(total_length))
                    self.progress_bar.setValue(amount_done)

                    if amount_done == 100:
                        self.hide()


class UpdateMessageWidget(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Update Available")
        self.setFixedSize(300, 125)

        update_message_hbox = QtWidgets.QHBoxLayout()
        update_message_hbox.addStretch()

        update_message_vbox = QtWidgets.QVBoxLayout()

        update_label = QtWidgets.QLabel("There is an update available.  Would you like to update?")
        update_message_vbox.addWidget(update_label)

        current_version_label = QtWidgets.QLabel(f"Current Version: {version}")
        update_message_vbox.addWidget(current_version_label)

        latest_version_label = QtWidgets.QLabel(f"Latest Version: {latest_version}")
        update_message_vbox.addWidget(latest_version_label)

        update_message_vbox.addStretch()

        button_hbox = QtWidgets.QHBoxLayout()

        yes_button = QtWidgets.QPushButton("Yes")
        yes_button.clicked.connect(self.yes_clicked)
        button_hbox.addWidget(yes_button)

        no_button = QtWidgets.QPushButton("No")
        no_button.clicked.connect(self.no_clicked)
        button_hbox.addWidget(no_button)

        update_message_vbox.addLayout(button_hbox)

        update_message_hbox.addLayout(update_message_vbox)

        update_message_hbox.addStretch()

        self.setLayout(update_message_hbox)

    def closeEvent(self, ev):
        main_window.show()
        self.hide()
        ev.ignore()

    def no_clicked(self):
        main_window.show()
        self.hide()
        self.deleteLater()

    def yes_clicked(self):
        self.hide()
        update_download_widget.show()
        app.processEvents()
        update_download_widget.download_update()
        main_window.trayIcon.hide()
        app.quit()

        from subprocess import Popen
        Popen([user_data_dir + update_download_widget.file_name])


if __name__ == "__main__":
    # This will be to update user files after software update
    if settings["version"] != version:

        if settings["version"] in "1.1.0 1.0.2 1.0.1 1.0.0".split():
            settings["check_for_updates"] = True
            settings["version"] = "1.2.0"

        if settings["version"] in "1.2.1 1.2.0".split():
            if os.path.isfile(user_data_dir + "projects"):
                with open(user_data_dir + "projects", "rb") as f:
                    old_project_data = pickle.load(f)

                project_data.extend(old_project_data)
                save_project_data()
                os.remove(user_data_dir + "projects")

                settings["version"] = "1.2.2"

        settings["version"] = version
        save_settings()

    main_window = MainWindow()

    if settings["check_for_updates"]:
        try:
            latest_version = get_latest_version(project_url)

            if version != latest_version:
                update_message_widget = UpdateMessageWidget()
                update_message_widget.show()

                update_download_widget = UpdateDownloadWidget()

            else:
                main_window.show()
                app.setActiveWindow(main_window)

        except error.URLError:
            main_window.show()
            app.setActiveWindow(main_window)

    else:
        main_window.show()
        app.setActiveWindow(main_window)

    sys.exit(app.exec_())
