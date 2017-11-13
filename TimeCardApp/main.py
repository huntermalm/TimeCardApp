import os
import sys
import pickle
import win32api
from project import *
from urllib import error
from datetime import datetime
from PyQt5 import QtCore, QtGui, QtWidgets
from user_data_updator import update_user_data
from system_hotkey import SystemHotkey


app = QtWidgets.QApplication(sys.argv)

app.themes = {
    "Light": {
        "primary_color": "white",
        "secondary_color": "lightgray",
        "font_color": "black",
        "scrollbar_background": "#F0F0F0",
        "scrollbar_handle": "#A9A9A9"
        },

    "Dark": {
        "primary_color": "#383838",
        "secondary_color": "#2A2A2A",
        "font_color": "lightgray",
        "scrollbar_background": "#2C2C2C",
        "scrollbar_handle": "#1B1B1B"
        }
    }

from GithubUpdater import *
from extra_widgets import *
from settings_widget import SettingsWidget
from hotkey_widget import HotkeyWidget

app.version = "1.6.0"
app.project_url = "https://github.com/huntermalm/TimeCardApp/"

app.app_data_dir = os.getenv("LOCALAPPDATA")
app.user_data_dir = f"{app.app_data_dir}\\Time Card App\\"
app.program_data_dir = os.getcwd() + "\\data"

monitor_handle = win32api.EnumDisplayMonitors()[0][0]
monitor_info = win32api.GetMonitorInfo(monitor_handle)
working_width = monitor_info["Work"][2]
working_height = monitor_info["Work"][3]

app.hotkeys = SystemHotkey()

rainbow_colors = {
    0: "236, 34, 68",
    1: "236, 139, 34",
    2: "236, 234, 34",
    3: "58, 236, 34",
    4: "34, 139, 236",
    5: "34, 39, 236",
    6: "134, 34, 236"
    }

# Load Settings
try:
    with open(app.user_data_dir + "settings", "rb") as f:
        app.settings = pickle.load(f)

except FileNotFoundError:
    app.settings = {
        "version": "1.6.0",
        "check_for_updates": True,
        "theme": "Light"
    }

# Load Project Data
try:
    with open(app.user_data_dir + "project_data", "rb") as f:
        app.project_data = pickle.load(f)

except FileNotFoundError:
    app.project_data = []


def save_settings():
    if not os.path.isdir(app.user_data_dir):
        os.makedirs(app.user_data_dir)

    with open(app.user_data_dir + "settings", "wb") as f:
        pickle.dump(app.settings, f, protocol=3)


app.save_settings = save_settings


def save_project_data():
    if not os.path.isdir(app.user_data_dir):
        os.makedirs(app.user_data_dir)

    with open(app.user_data_dir + "project_data", "wb") as f:
        pickle.dump(app.project_data, f, protocol=3)


app.save_project_data = save_project_data


def center_window(top_window, bottom_window):
    top_window_new_x = bottom_window.x() + (bottom_window.width() // 2) - (top_window.width() // 2)
    top_window_new_y = bottom_window.y() + (bottom_window.height() // 2) - (top_window.height() // 2)
    top_window.move(top_window_new_x, top_window_new_y)


# app.center_window = center_window


class FolderWidget(QtWidgets.QWidget):

    def __init__(self, file, root=False, color=0):
        super().__init__()
        main_widget = QtWidgets.QWidget()
        main_widget.setFixedHeight(45)

        self.root = root
        self.file = file

        self.color = color

        if self.color == 7:
            self.color = 0

        self.folder_widgets = []
        self.is_showing_options = False
        self.collapsed = True
        self.active = False
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.tick)

        self.init_options_widget()
        self.init_contents_widget()
        self.separator = get_separator(2, 1)
        self.options_separator = get_separator(2, 1)

        self.contents_widget.hide()
        self.options_widget.hide()
        self.separator.hide()
        self.options_separator.hide()

        main_vbox = QtWidgets.QVBoxLayout()
        main_vbox.setSpacing(0)
        main_vbox.setContentsMargins(0, 0, 0, 0)

        main_hbox = QtWidgets.QHBoxLayout()
        main_hbox.setSpacing(0)
        main_hbox.setContentsMargins(0, 0, 0, 0)

        self.collapse_button = ButtonLabel(app.program_data_dir + "/images/arrow_right.png",
                                           app.program_data_dir + "/images/arrow_middle.png")
        self.collapse_button.enabled_pixmap = QtGui.QPixmap(app.program_data_dir + "/images/arrow_down.png")
        self.collapse_button.clicked.connect(self.collapse_pressed)

        if not self.file.files:
            self.collapse_button.set_disabled()

        self.name_label = QtWidgets.QLabel(self.file.name)
        self.name_label.setStyleSheet(f"color: {app.active_theme['font_color']}")
        name_label_font = QtGui.QFont()
        name_label_font.setPointSize(16)
        self.name_label.setFont(name_label_font)

        self.time_label = QtWidgets.QLabel()
        self.time_label.setStyleSheet(f"color: {app.active_theme['font_color']}")

        self.total_time = self.contents_total_time()

        if self.total_time > 0:
            self.update_time_label()

        else:
            self.time_label.setText("— —")

        self.add_project_button_label = ButtonLabel(app.program_data_dir + "/images/plus_before.png",
                                                    app.program_data_dir + "/images/plus_after.png")
        self.add_project_button_label.clicked.connect(self.add_project_pressed)

        self.add_folder_button_label = ButtonLabel(app.program_data_dir + "/images/add_folder_before.png",
                                                   app.program_data_dir + "/images/add_folder_after.png")
        self.add_folder_button_label.clicked.connect(self.add_folder_pressed)

        edit_button_label = ButtonLabel(app.program_data_dir + "/images/edit_before.png",
                                        app.program_data_dir + "/images/edit_after.png")
        edit_button_label.clicked.connect(self.edit_pressed)

        main_hbox.addSpacing(10)
        main_hbox.addWidget(self.collapse_button)
        main_hbox.addSpacing(10)
        main_hbox.addWidget(self.name_label)
        main_hbox.addStretch()
        main_hbox.addSpacing(20)
        main_hbox.addWidget(self.time_label)
        main_hbox.addSpacing(20)
        main_hbox.addWidget(self.add_project_button_label)
        main_hbox.addSpacing(12)
        main_hbox.addWidget(self.add_folder_button_label)
        main_hbox.addSpacing(12)
        main_hbox.addWidget(edit_button_label)
        main_hbox.addSpacing(15)

        main_widget.setLayout(main_hbox)

        main_vbox.addWidget(self.separator)
        main_vbox.addWidget(main_widget)
        main_vbox.addWidget(self.options_separator)
        main_vbox.addWidget(self.options_widget)
        main_vbox.addWidget(self.contents_widget)

        self.setLayout(main_vbox)

    def contents_total_time(self):
        total_time = 0

        if self.folder_widgets:
            for folder_widget in self.folder_widgets:
                if folder_widget.file.type() == "project":
                    total_time += folder_widget.total_time

                else:
                    total_time += folder_widget.contents_total_time()

        return total_time

    def init_contents_widget(self):
        self.contents_widget = QtWidgets.QWidget()
        # self.contents_widget.setFixedHeight(46)

        base_vbox = QtWidgets.QVBoxLayout()
        base_vbox.setContentsMargins(0, 0, 0, 0)
        base_vbox.setSpacing(0)

        base_hbox = QtWidgets.QHBoxLayout()
        base_hbox.setContentsMargins(0, 0, 0, 0)
        base_hbox.setSpacing(0)

        self.content_vbox = QtWidgets.QVBoxLayout()
        self.content_vbox.setContentsMargins(0, 0, 0, 0)
        self.content_vbox.setSpacing(0)

        color_tab = QtWidgets.QWidget()
        color_tab.setAttribute(QtCore.Qt.WA_StyledBackground)
        color_tab.setStyleSheet(f"background: rgb({self.get_color()});")
        color_tab.setFixedWidth(7)

        self.entry_separator = get_separator(2, 1)
        self.entry_separator.hide()

        self.project_entry_widget = ProjectEntryWidget()
        self.project_entry_widget.hide()

        self.folder_entry_widget = FolderEntryWidget()
        self.folder_entry_widget.hide()

        base_vbox.addWidget(get_separator(2, 1))

        base_hbox.addWidget(color_tab)
        base_hbox.addWidget(get_separator(1, 2))

        if self.file.files:
            for count, file in enumerate(self.file.files):
                if file.type() == "project":
                    file_widget = ProjectWidget(file)

                else:
                    file_widget = FolderWidget(file, color=self.color + 1)

                app.all_file_widgets.append(file_widget)
                self.folder_widgets.append(file_widget)
                self.content_vbox.addWidget(file_widget)

                if len(self.file.files) > 1 and count != 0:
                    file_widget.separator.show()

        self.content_vbox.addWidget(self.entry_separator)
        self.content_vbox.addWidget(self.project_entry_widget)
        self.content_vbox.addWidget(self.folder_entry_widget)

        base_hbox.addLayout(self.content_vbox)

        base_vbox.addLayout(base_hbox)

        self.contents_widget.setLayout(base_vbox)

    def get_color(self):
        if self.color in rainbow_colors:
            return rainbow_colors[self.color]

        else:
            from random import randint
            return f"{randint(0, 255)}, {randint(0, 255)}, {randint(0, 255)}"

    def init_options_widget(self):
        self.options_widget = QtWidgets.QWidget()
        self.options_widget.setAttribute(QtCore.Qt.WA_StyledBackground)
        self.options_widget.setStyleSheet(f"background:{app.active_theme['secondary_color']};")
        self.options_widget.setFixedHeight(50)

        options_hbox = QtWidgets.QHBoxLayout()
        options_hbox.setContentsMargins(0, 0, 0, 0)
        options_hbox.setSpacing(0)
        options_hbox.addStretch()

        delete_button_label = ButtonLabel(app.program_data_dir + "/images/delete_before.png",
                                          app.program_data_dir + "/images/delete_after.png")
        delete_button_label.clicked.connect(self.delete_pressed)
        options_hbox.addWidget(delete_button_label)
        options_hbox.addSpacing(35)

        self.options_widget.setLayout(options_hbox)

        self.shadow = QtWidgets.QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(50)
        self.shadow.setXOffset(0)
        self.shadow_widget = QtWidgets.QWidget(self.options_widget)
        self.shadow_widget.setFixedHeight(45)
        self.shadow_widget.setMinimumWidth(working_width)
        # self.shadow_widget.setStyleSheet("background:black;")
        self.shadow_widget.setGraphicsEffect(self.shadow)
        self.shadow_widget.move(0, -45)

    def reset_stylesheet(self):
        self.name_label.setStyleSheet(f"color: {app.active_theme['font_color']}")
        self.time_label.setStyleSheet(f"color: {app.active_theme['font_color']}")
        self.options_widget.setStyleSheet(f"background:{app.active_theme['secondary_color']};")
        self.project_entry_widget.reset_stylesheet()
        self.folder_entry_widget.reset_stylesheet()

        for folder_widget in self.folder_widgets:
            folder_widget.reset_stylesheet()

    def collapse_pressed(self):
        if self.collapsed:
            self.contents_widget.show()
            self.collapsed = False
            self.collapse_button.setPixmap(self.collapse_button.enabled_pixmap)
            self.collapse_button.is_enabled = True

        else:
            self.contents_widget.hide()
            self.collapsed = True
            self.collapse_button.setPixmap(self.collapse_button.before_pixmap)
            self.collapse_button.is_enabled = False

    def add_project_pressed(self):
        self.contents_widget.show()
        self.collapsed = False
        self.collapse_button.setPixmap(self.collapse_button.enabled_pixmap)
        self.collapse_button.is_enabled = True
        self.collapse_button.set_disabled(False)
        self.folder_entry_widget.hide()
        self.project_entry_widget.show()
        self.project_entry_widget.line_edit.setFocus(True)

        if len(self.file.files) > 0:
            self.entry_separator.show()

    def add_folder_pressed(self):
        self.contents_widget.show()
        self.collapsed = False
        self.collapse_button.setPixmap(self.collapse_button.enabled_pixmap)
        self.collapse_button.is_enabled = True
        self.collapse_button.set_disabled(False)
        self.project_entry_widget.hide()
        self.folder_entry_widget.show()
        self.folder_entry_widget.line_edit.setFocus(True)

        if len(self.file.files) > 0:
            self.entry_separator.show()

    def delete_pressed(self):
        self.hide()
        self.deleteLater()

        if self.root:
            files = app.project_data

            for count, file_widget in enumerate(app.root_widgets):
                if self is file_widget:
                    if count == 0:
                        if len(app.root_widgets) > 1:
                            app.root_widgets[count + 1].separator.hide()

                    del app.root_widgets[count]
                    break

            if not app.root_widgets:
                app.main_window.buttons_separator.hide()

        else:
            parent_folder_widget = self.parent().parent()
            files = parent_folder_widget.file.files

            for count, file_widget in enumerate(parent_folder_widget.folder_widgets):
                if self is file_widget:
                    if count == 0:
                        if len(parent_folder_widget.folder_widgets) > 1:
                            parent_folder_widget.folder_widgets[count + 1].separator.hide()

                    del parent_folder_widget.folder_widgets[count]
                    break

            if not parent_folder_widget.folder_widgets:
                parent_folder_widget.contents_widget.hide()
                parent_folder_widget.collapsed = True
                parent_folder_widget.collapse_button.setPixmap(parent_folder_widget.collapse_button.before_pixmap)
                parent_folder_widget.collapse_button.is_enabled = False
                parent_folder_widget.collapse_button.set_disabled(True)

            parent_folder_widget.tick()

        self.erase_widgets()

        for count, file_widget in enumerate(app.all_file_widgets):
            if self is file_widget:
                del app.all_file_widgets[count]
                break

        for count, file in enumerate(files):
            if self.file is file:
                del files[count]
                break

        save_project_data()

    def erase_widgets(self):
        for folder_widget in self.folder_widgets:
            if folder_widget.file.type() == "folder":
                folder_widget.erase_widgets()

            else:
                folder_widget.unregister_hotkey()

            for count, file_widget in enumerate(app.all_file_widgets):
                if folder_widget is file_widget:
                    del app.all_file_widgets[count]

    def edit_pressed(self):
        if self.is_showing_options:
            self.is_showing_options = False
            self.options_widget.hide()
            self.options_separator.hide()

        else:
            for file_widget in app.all_file_widgets:
                if file_widget is not self and file_widget.is_showing_options:
                    file_widget.is_showing_options = False
                    file_widget.options_widget.hide()
                    file_widget.options_separator.hide()

            self.is_showing_options = True
            self.options_widget.show()
            self.options_separator.show()

    def tick(self):
        self.total_time = self.contents_total_time()
        self.update_time_label()

        if not self.root:
            parent_folder_widget = self.parent().parent()
            parent_folder_widget.tick()

    def update_time_label(self):
        d = divmod(self.total_time, 86400)
        h = divmod(d[1], 3600)
        m = divmod(h[1], 60)
        s = m[1]

        h_including_days = h[0] + (d[0] * 24)

        h_string = str(int(h_including_days))
        m_string = str(int(m[0]))
        s_string = str(round(s))

        if len(h_string) == 1:
            h_string = f"0{h_string}"
        if len(m_string) == 1:
            m_string = f"0{m_string}"
        if len(s_string) == 1:
            s_string = f"0{s_string}"

        time_string = f"{h_string}:{m_string}:{s_string}"

        if time_string == "00:00:00":
            time_string = "— —"

        self.time_label.setText(time_string)


class ProjectWidget(QtWidgets.QWidget):

    def __init__(self, file, root=False):
        super().__init__()
        main_widget = QtWidgets.QWidget()
        main_widget.setFixedHeight(45)

        self.root = root
        self.active = False
        self.file = file
        self.is_showing_options = False
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)

        if self.file.hotkey:
            self.register_hotkey(self.file.hotkey)

        self.hotkey_assignment_widget = HotkeyWidget(file, self)

        self.separator = get_separator(2, 1)
        self.init_options_widget()
        self.options_separator = get_separator(2, 1)

        self.separator.hide()
        self.options_widget.hide()
        self.options_separator.hide()

        main_hbox = QtWidgets.QHBoxLayout()
        main_hbox.setContentsMargins(0, 0, 0, 0)
        main_hbox.setSpacing(0)

        main_vbox = QtWidgets.QVBoxLayout()
        main_vbox.setContentsMargins(0, 0, 0, 0)
        main_vbox.setSpacing(0)

        self.project_name_label = QtWidgets.QLabel(f"{self.file.name}")
        self.project_name_label.setStyleSheet(f"color: {app.active_theme['font_color']}")
        project_name_label_font = QtGui.QFont()
        project_name_label_font.setPointSize(16)
        self.project_name_label.setFont(project_name_label_font)

        self.project_time_label = QtWidgets.QLabel()
        self.project_time_label.setStyleSheet(f"color: {app.active_theme['font_color']}")
        self.total_time = 0

        if self.file.times:
            for time in self.file.times:
                self.total_time += (time[1] - time[0]).total_seconds()

            self.update_project_time_label()

        else:
            self.project_time_label.setText(f"— —")

        self.start_button_label = ButtonLabel(app.program_data_dir + "/images/start_before.png",
                                              app.program_data_dir + "/images/start_after.png")
        self.start_button_label.clicked.connect(self.start_pressed)

        self.end_button_label = ButtonLabel(app.program_data_dir + "/images/end_before.png",
                                            app.program_data_dir + "/images/end_after.png")
        self.end_button_label.clicked.connect(self.end_pressed)
        self.end_button_label.set_disabled()

        edit_button_label = ButtonLabel(app.program_data_dir + "/images/edit_before.png",
                                        app.program_data_dir + "/images/edit_after.png")
        edit_button_label.clicked.connect(self.edit_pressed)

        main_hbox.addSpacing(15)
        main_hbox.addWidget(self.project_name_label)
        main_hbox.addStretch()
        main_hbox.addSpacing(20)
        main_hbox.addWidget(self.project_time_label)
        main_hbox.addSpacing(20)
        main_hbox.addWidget(self.start_button_label)
        main_hbox.addWidget(get_separator(1, 18, fully_fixed=True))
        main_hbox.addWidget(self.end_button_label)
        main_hbox.addSpacing(10)
        main_hbox.addWidget(edit_button_label)
        main_hbox.addSpacing(15)

        main_widget.setLayout(main_hbox)

        main_vbox.addWidget(self.separator)
        main_vbox.addWidget(main_widget)
        main_vbox.addWidget(self.options_separator)
        main_vbox.addWidget(self.options_widget)

        self.setLayout(main_vbox)

    def init_options_widget(self):
        self.options_widget = QtWidgets.QWidget()
        self.options_widget.setAttribute(QtCore.Qt.WA_StyledBackground)
        self.options_widget.setStyleSheet(f"background:{app.active_theme['secondary_color']};")
        self.options_widget.setFixedHeight(65)

        options_hbox = QtWidgets.QHBoxLayout()
        options_hbox.setContentsMargins(0, 0, 0, 0)
        options_hbox.setSpacing(0)

        hotkey_vbox = QtWidgets.QVBoxLayout()
        hotkey_vbox.setContentsMargins(0, 0, 0, 0)
        hotkey_vbox.setSpacing(0)

        hotkey_hbox = QtWidgets.QHBoxLayout()
        hotkey_hbox.setContentsMargins(0, 0, 0, 0)
        hotkey_hbox.setSpacing(0)

        delete_button = ButtonLabel(app.program_data_dir + "/images/delete_before.png",
                                    app.program_data_dir + "/images/delete_after.png")
        delete_button.clicked.connect(self.delete_pressed)

        self.hotkey_bold_label = QtWidgets.QLabel("Hotkey:")
        self.hotkey_bold_label.setStyleSheet(f"color: {app.active_theme['font_color']}")
        hotkey_bold_label_font = QtGui.QFont()
        hotkey_bold_label_font.setBold(True)
        self.hotkey_bold_label.setFont(hotkey_bold_label_font)

        self.hotkey_label = QtWidgets.QLabel()
        self.hotkey_label.setStyleSheet(f"color: {app.active_theme['font_color']}")

        if self.file.hotkey:
            self.hotkey_label.setText(self.hotkey_assignment_widget.get_hotkey_string())

        else:
            self.hotkey_label.setText("Unassigned")

        assign_hotkey_button = ButtonLabel(app.program_data_dir + "/images/assign_hotkey_before.png",
                                           app.program_data_dir + "/images/assign_hotkey_after.png")
        assign_hotkey_button.clicked.connect(self.assign_hotkey_pressed)

        hotkey_hbox.addWidget(self.hotkey_bold_label)
        hotkey_hbox.addSpacing(3)
        hotkey_hbox.addWidget(self.hotkey_label)

        hotkey_vbox.addSpacing(10)
        hotkey_vbox.addLayout(hotkey_hbox)
        hotkey_vbox.addSpacing(3)
        hotkey_vbox.addWidget(assign_hotkey_button)
        hotkey_vbox.addSpacing(10)

        options_hbox.addSpacing(15)
        options_hbox.addLayout(hotkey_vbox)
        options_hbox.addStretch()
        options_hbox.addWidget(delete_button)
        options_hbox.addSpacing(35)

        self.options_widget.setLayout(options_hbox)

        self.shadow = QtWidgets.QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(50)
        self.shadow.setXOffset(0)
        self.shadow_widget = QtWidgets.QWidget(self.options_widget)
        self.shadow_widget.setFixedHeight(45)
        self.shadow_widget.setMinimumWidth(working_width)
        # self.shadow_widget.setStyleSheet("background:black;")
        self.shadow_widget.setGraphicsEffect(self.shadow)
        self.shadow_widget.move(0, -45)

    def reset_stylesheet(self):
        self.project_name_label.setStyleSheet(f"color: {app.active_theme['font_color']}")
        self.project_time_label.setStyleSheet(f"color: {app.active_theme['font_color']}")
        self.options_widget.setStyleSheet(f"background:{app.active_theme['secondary_color']};")
        self.hotkey_bold_label.setStyleSheet(f"color: {app.active_theme['font_color']}")
        self.hotkey_label.setStyleSheet(f"color: {app.active_theme['font_color']}")

        self.hotkey_assignment_widget.reset_stylesheet()

    def assign_hotkey_pressed(self):
        for file_widget in app.all_file_widgets:
            if file_widget.file.type() == "project":
                if file_widget.hotkey_assignment_widget.isVisible():
                    file_widget.hotkey_assignment_widget.hide()

        center_window(self.hotkey_assignment_widget, app.main_window)
        self.hotkey_assignment_widget.show()

    def register_hotkey(self, hotkey_tuple):
        app.hotkeys.register(hotkey_tuple, callback=self.hotkey_triggered)

    def unregister_hotkey(self):
        if self.file.hotkey:
            app.hotkeys.unregister(self.file.hotkey)

    def hotkey_triggered(self, event):
        for file_widget in app.all_file_widgets:
            if file_widget.file.type() == "project" and file_widget is not self:
                if file_widget.active:
                    return

        if self.active:
            self.end_pressed()

        else:
            self.start_pressed()

    def delete_pressed(self):
        self.hide()
        self.deleteLater()

        if self.root:
            files = app.project_data

            for count, file_widget in enumerate(app.root_widgets):
                if self is file_widget:
                    if count == 0:
                        if len(app.root_widgets) > 1:
                            app.root_widgets[count + 1].separator.hide()

                    del app.root_widgets[count]
                    break

            if not app.root_widgets:
                app.main_window.buttons_separator.hide()

        else:
            parent_folder_widget = self.parent().parent()
            files = parent_folder_widget.file.files

            for count, file_widget in enumerate(parent_folder_widget.folder_widgets):
                if self is file_widget:
                    if count == 0:
                        if len(parent_folder_widget.folder_widgets) > 1:
                            parent_folder_widget.folder_widgets[count + 1].separator.hide()

                    del parent_folder_widget.folder_widgets[count]
                    break

            if not parent_folder_widget.folder_widgets:
                parent_folder_widget.contents_widget.hide()
                parent_folder_widget.collapsed = True
                parent_folder_widget.collapse_button.setPixmap(parent_folder_widget.collapse_button.before_pixmap)
                parent_folder_widget.collapse_button.is_enabled = False
                parent_folder_widget.collapse_button.set_disabled(True)

            parent_folder_widget.tick()

        self.unregister_hotkey()

        for count, file_widget in enumerate(app.all_file_widgets):
            if self is file_widget:
                del app.all_file_widgets[count]
                break

        for count, file in enumerate(files):
            if self.file is file:
                del files[count]
                break

        save_project_data()

        if self.active:
            for file_widget in app.all_file_widgets:
                if file_widget.file.type() == "project":
                    file_widget.start_button_label.set_disabled(False)

    def edit_pressed(self):
        if self.is_showing_options:
            self.is_showing_options = False
            self.options_widget.hide()
            self.options_separator.hide()

        else:
            for file_widget in app.all_file_widgets:
                if file_widget is not self and file_widget.is_showing_options:
                    file_widget.is_showing_options = False
                    file_widget.options_widget.hide()
                    file_widget.options_separator.hide()

            self.is_showing_options = True
            self.options_widget.show()
            self.options_separator.show()

    def start_pressed(self):
        self.start_time = datetime.now()
        # self.timer.start(1000)
        self.active = True

        self.start_button_label.set_disabled()
        self.end_button_label.set_disabled(False)

        for file_widget in app.all_file_widgets:
            if file_widget.file.type() == "project":
                if file_widget is not self:
                    file_widget.start_button_label.set_disabled()

    def end_pressed(self):
        end_time = datetime.now()
        # self.timer.stop()
        time_tuple = (self.start_time, end_time)
        self.file.times.append(time_tuple)

        save_project_data()

        self.total_time = 0

        for time in self.file.times:
            self.total_time += (time[1] - time[0]).total_seconds()

        self.update_project_time_label()

        self.active = False

        self.end_button_label.set_disabled()
        self.start_button_label.set_disabled(False)

        for file_widget in app.all_file_widgets:
            if file_widget.file.type() == "project":
                if file_widget is not self:
                    file_widget.start_button_label.set_disabled(False)

    def tick(self):
        if self.active:
            self.total_time = 0

            for time in self.file.times:
                self.total_time += (time[1] - time[0]).total_seconds()

            self.total_time += (datetime.now() - self.start_time).total_seconds()

            self.update_project_time_label()

            if not self.root:
                parent_folder_widget = self.parent().parent()
                parent_folder_widget.tick()

    def update_project_time_label(self):
        d = divmod(self.total_time, 86400)
        h = divmod(d[1], 3600)
        m = divmod(h[1], 60)
        s = m[1]

        h_including_days = h[0] + (d[0] * 24)

        h_string = str(int(h_including_days))
        m_string = str(int(m[0]))
        s_string = str(round(s))

        if len(h_string) == 1:
            h_string = f"0{h_string}"
        if len(m_string) == 1:
            m_string = f"0{m_string}"
        if len(s_string) == 1:
            s_string = f"0{s_string}"

        time_string = f"{h_string}:{m_string}:{s_string}"

        if time_string == "00:00:00":
            time_string = "— —"

        self.project_time_label.setText(time_string)


class ProjectEntryWidget(QtWidgets.QWidget):

    def __init__(self, root=False):
        super().__init__()
        self.setAttribute(QtCore.Qt.WA_StyledBackground)
        self.setStyleSheet(f"background:{app.active_theme['primary_color']};")
        self.setFixedHeight(45)

        self.root = root

        main_hbox = QtWidgets.QHBoxLayout()
        main_hbox.setContentsMargins(0, 0, 0, 0)
        main_hbox.setSpacing(0)
        main_hbox.addSpacing(10)

        self.name_label = QtWidgets.QLabel("Project Name:")
        self.name_label.setStyleSheet(f"color: {app.active_theme['font_color']}")
        name_label_font = QtGui.QFont()
        name_label_font.setPointSize(16)
        self.name_label.setFont(name_label_font)
        main_hbox.addWidget(self.name_label)

        main_hbox.addSpacing(10)

        self.line_edit = QtWidgets.QLineEdit()
        self.line_edit.setStyleSheet(f"color: {app.active_theme['font_color']};")
        line_edit_font = QtGui.QFont()
        line_edit_font.setPointSize(16)
        self.line_edit.setFont(line_edit_font)
        self.line_edit.setFixedHeight(30)
        self.line_edit.textChanged.connect(self.enable_check_button)
        self.line_edit.returnPressed.connect(self.confirm)
        main_hbox.addWidget(self.line_edit)
        main_hbox.addSpacing(10)

        self.check_button = ButtonLabel(app.program_data_dir + "/images/check_before.png",
                                        app.program_data_dir + "/images/check_after.png")
        self.check_button.caution_pixmap = QtGui.QPixmap(app.program_data_dir + "/images/caution.png")
        self.check_button.clicked.connect(self.confirm)
        self.check_button.set_disabled()
        self.check_button.setToolTip("Confirm")
        main_hbox.addWidget(self.check_button)
        main_hbox.addSpacing(10)

        self.cancel_button = ButtonLabel(app.program_data_dir + "/images/cancel_before.png",
                                         app.program_data_dir + "/images/cancel_after.png")
        self.cancel_button.clicked.connect(self.cancel)
        self.cancel_button.setToolTip("Cancel")
        main_hbox.addWidget(self.cancel_button)

        main_hbox.addSpacing(14)

        self.setLayout(main_hbox)

    def reset_stylesheet(self):
        self.setStyleSheet(f"background:{app.active_theme['primary_color']};")
        self.name_label.setStyleSheet(f"color: {app.active_theme['font_color']}")
        self.line_edit.setStyleSheet(f"color: {app.active_theme['font_color']}")

    def cancel(self):
        if self.root:
            app.main_window.add_buttons_widget.show()
            app.main_window.add_buttons_widget.enterEvent(None)

        else:
            parent_folder_widget = self.parent().parent()

            if len(parent_folder_widget.file.files) == 0:
                parent_folder_widget.contents_widget.hide()
                parent_folder_widget.collapsed = True
                parent_folder_widget.collapse_button.setPixmap(parent_folder_widget.collapse_button.before_pixmap)
                parent_folder_widget.collapse_button.is_enabled = False
                parent_folder_widget.collapse_button.set_disabled(True)

            else:
                parent_folder_widget.entry_separator.hide()

        self.hide()

    def confirm(self):
        if not self.check_button.disabled:
            new_project = Project(self.line_edit.text())
            self.line_edit.clear()

            content_vbox = self.parent().layout()

            if self.root:
                app.project_data.append(new_project)

            else:
                parent_folder_widget = self.parent().parent()
                parent_folder_widget.file.files.append(new_project)

            if self.root:
                new_project_widget = ProjectWidget(new_project, root=True)
                content_vbox.insertWidget(content_vbox.count() - 6, new_project_widget)
                app.root_widgets.append(new_project_widget)

                if len(app.project_data) > 1:
                    new_project_widget.separator.show()

                if len(app.project_data) == 1:
                    app.main_window.buttons_separator.show()

                app.main_window.add_buttons_widget.show()

            else:
                new_project_widget = ProjectWidget(new_project)
                parent_folder_widget.content_vbox.insertWidget(parent_folder_widget.content_vbox.count() - 3, new_project_widget)
                parent_folder_widget.folder_widgets.append(new_project_widget)

                if len(parent_folder_widget.file.files) > 1:
                    new_project_widget.separator.show()

            app.all_file_widgets.append(new_project_widget)

            for file_widget in app.all_file_widgets:
                if file_widget.file.type() == "project":
                    if file_widget.active:
                        new_project_widget.start_button_label.set_disabled()

            save_project_data()

            if not self.root:
                parent_folder_widget.entry_separator.hide()

            self.hide()

    def enable_check_button(self):
        disable = False
        same_name = False

        new_folder_name = self.line_edit.text().strip()

        if new_folder_name:
            if self.root:
                files = app.project_data

            else:
                parent_folder_widget = self.parent().parent()
                files = parent_folder_widget.file.files

            for file in files:
                if file.name == new_folder_name:
                    same_name = True
                    disable = True

            else:
                self.check_button.setPixmap(self.check_button.before_pixmap)
                self.check_button.set_disabled(False)
                self.check_button.setToolTip("Confirm")

        else:
            disable = True

        if disable:
            if same_name:
                self.check_button.set_disabled()
                self.check_button.setPixmap(self.check_button.caution_pixmap)
                self.check_button.setToolTip("A file with this name already exists at this level.")

            else:
                self.check_button.set_disabled()
                self.check_button.setToolTip("Confirm")


class FolderEntryWidget(QtWidgets.QWidget):

    def __init__(self, root=False):
        super().__init__()
        self.setAttribute(QtCore.Qt.WA_StyledBackground)
        self.setStyleSheet(f"background:{app.active_theme['primary_color']};")
        self.setFixedHeight(45)

        self.root = root

        main_hbox = QtWidgets.QHBoxLayout()
        main_hbox.setContentsMargins(0, 0, 0, 0)
        main_hbox.setSpacing(0)
        main_hbox.addSpacing(10)

        self.name_label = QtWidgets.QLabel("Folder Name:")
        self.name_label.setStyleSheet(f"color: {app.active_theme['font_color']}")
        name_label_font = QtGui.QFont()
        name_label_font.setPointSize(16)
        self.name_label.setFont(name_label_font)
        main_hbox.addWidget(self.name_label)

        main_hbox.addSpacing(10)

        self.line_edit = QtWidgets.QLineEdit()
        self.line_edit.setStyleSheet(f"color: {app.active_theme['font_color']};")
        line_edit_font = QtGui.QFont()
        line_edit_font.setPointSize(16)
        self.line_edit.setFont(line_edit_font)
        self.line_edit.setFixedHeight(30)
        self.line_edit.textChanged.connect(self.enable_check_button)
        self.line_edit.returnPressed.connect(self.confirm)
        main_hbox.addWidget(self.line_edit)
        main_hbox.addSpacing(10)

        self.check_button = ButtonLabel(app.program_data_dir + "/images/check_before.png",
                                        app.program_data_dir + "/images/check_after.png")
        self.check_button.caution_pixmap = QtGui.QPixmap(app.program_data_dir + "/images/caution.png")
        self.check_button.clicked.connect(self.confirm)
        self.check_button.set_disabled()
        self.check_button.setToolTip("Confirm")
        main_hbox.addWidget(self.check_button)
        main_hbox.addSpacing(10)

        self.cancel_button = ButtonLabel(app.program_data_dir + "/images/cancel_before.png",
                                         app.program_data_dir + "/images/cancel_after.png")
        self.cancel_button.clicked.connect(self.cancel)
        self.cancel_button.setToolTip("Cancel")
        main_hbox.addWidget(self.cancel_button)

        main_hbox.addSpacing(14)

        self.setLayout(main_hbox)

    def reset_stylesheet(self):
        self.setStyleSheet(f"background:{app.active_theme['primary_color']};")
        self.name_label.setStyleSheet(f"color: {app.active_theme['font_color']}")
        self.line_edit.setStyleSheet(f"color: {app.active_theme['font_color']}")

    def cancel(self):
        if self.root:
            app.main_window.add_buttons_widget.show()
            app.main_window.add_buttons_widget.enterEvent(None)

        else:
            parent_folder_widget = self.parent().parent()

            if len(parent_folder_widget.file.files) == 0:
                parent_folder_widget.contents_widget.hide()
                parent_folder_widget.collapsed = True
                parent_folder_widget.collapse_button.setPixmap(parent_folder_widget.collapse_button.before_pixmap)
                parent_folder_widget.collapse_button.is_enabled = False
                parent_folder_widget.collapse_button.set_disabled(True)

            else:
                parent_folder_widget.entry_separator.hide()

        self.hide()

    def confirm(self):
        if not self.check_button.disabled:
            new_folder = Folder(self.line_edit.text())
            self.line_edit.clear()

            content_vbox = self.parent().layout()

            if self.root:
                app.project_data.append(new_folder)

            else:
                parent_folder_widget = self.parent().parent()
                parent_folder_widget.file.files.append(new_folder)

            if self.root:
                new_folder_widget = FolderWidget(new_folder, root=True)

                content_vbox.insertWidget(content_vbox.count() - 6, new_folder_widget)
                app.root_widgets.append(new_folder_widget)

                if len(app.project_data) > 1:
                    new_folder_widget.separator.show()

                if len(app.project_data) == 1:
                    app.main_window.buttons_separator.show()

                app.main_window.add_buttons_widget.show()

            else:
                new_folder_widget = FolderWidget(new_folder, color=parent_folder_widget.color + 1)

                parent_folder_widget.content_vbox.insertWidget(parent_folder_widget.content_vbox.count() - 3, new_folder_widget)
                parent_folder_widget.folder_widgets.append(new_folder_widget)

                if len(parent_folder_widget.file.files) > 1:
                    new_folder_widget.separator.show()

            app.all_file_widgets.append(new_folder_widget)

            save_project_data()

            if not self.root:
                parent_folder_widget.entry_separator.hide()

            self.hide()

    def enable_check_button(self):
        disable = False
        same_name = False

        new_folder_name = self.line_edit.text().strip()

        if new_folder_name:
            if self.root:
                files = app.project_data

            else:
                parent_folder_widget = self.parent().parent()
                files = parent_folder_widget.file.files

            for file in files:
                if file.name == new_folder_name:
                    same_name = True
                    disable = True

            else:
                self.check_button.setPixmap(self.check_button.before_pixmap)
                self.check_button.set_disabled(False)
                self.check_button.setToolTip("Confirm")

        else:
            disable = True

        if disable:
            if same_name:
                self.check_button.set_disabled()
                self.check_button.setPixmap(self.check_button.caution_pixmap)
                self.check_button.setToolTip("A file with this name already exists at this level.")

            else:
                self.check_button.set_disabled()
                self.check_button.setToolTip("Confirm")


class AddProjectButton(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        self.setAttribute(QtCore.Qt.WA_StyledBackground)
        self.setStyleSheet(f"background:{app.active_theme['primary_color']};")

        add_project_button_hbox = QtWidgets.QHBoxLayout()
        add_project_button_hbox.setSpacing(10)
        add_project_button_hbox.setContentsMargins(0, 0, 0, 0)
        add_project_button_hbox.addStretch()

        self.plus_before_pixmap = QtGui.QPixmap(app.program_data_dir + "/images/plus_before.png")
        self.plus_after_pixmap = QtGui.QPixmap(app.program_data_dir + "/images/plus_after.png")
        self.plus_label = QtWidgets.QLabel()
        self.plus_label.setPixmap(self.plus_before_pixmap)
        add_project_button_hbox.addWidget(self.plus_label)

        self.add_project_label = QtWidgets.QLabel("Add Project")
        self.add_project_label.setStyleSheet(f"color: {app.active_theme['font_color']}")
        add_project_label_font = QtGui.QFont()
        add_project_label_font.setPointSize(16)
        self.add_project_label.setFont(add_project_label_font)
        add_project_button_hbox.addWidget(self.add_project_label)

        add_project_button_hbox.addStretch()

        self.setLayout(add_project_button_hbox)

    def mousePressEvent(self, ev):
        app.main_window.add_buttons_widget.hide()
        app.main_window.project_entry_widget.show()
        app.main_window.project_entry_widget.line_edit.setFocus(True)

    def enterEvent(self, ev):
        self.setStyleSheet(f"background:{app.active_theme['secondary_color']};")
        self.plus_label.setPixmap(self.plus_after_pixmap)

    def leaveEvent(self, ev):
        self.setStyleSheet(f"background:{app.active_theme['primary_color']};")
        self.plus_label.setPixmap(self.plus_before_pixmap)


class AddFolderButton(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        self.setAttribute(QtCore.Qt.WA_StyledBackground)
        self.setStyleSheet(f"background:{app.active_theme['primary_color']};")

        add_folder_button_hbox = QtWidgets.QHBoxLayout()
        add_folder_button_hbox.setSpacing(10)
        add_folder_button_hbox.setContentsMargins(0, 0, 0, 0)
        add_folder_button_hbox.addStretch()

        self.add_folder_before_pixmap = QtGui.QPixmap(app.program_data_dir + "/images/add_folder_before.png")
        self.add_folder_after_pixmap = QtGui.QPixmap(app.program_data_dir + "/images/add_folder_after.png")
        self.add_folder_image = QtWidgets.QLabel()
        self.add_folder_image.setPixmap(self.add_folder_before_pixmap)
        add_folder_button_hbox.addWidget(self.add_folder_image)

        self.add_folder_label = QtWidgets.QLabel("Add Folder")
        self.add_folder_label.setStyleSheet(f"color: {app.active_theme['font_color']}")
        add_folder_label_font = QtGui.QFont()
        add_folder_label_font.setPointSize(16)
        self.add_folder_label.setFont(add_folder_label_font)
        add_folder_button_hbox.addWidget(self.add_folder_label)

        add_folder_button_hbox.addStretch()

        self.setLayout(add_folder_button_hbox)

    def mousePressEvent(self, ev):
        app.main_window.add_buttons_widget.hide()
        app.main_window.folder_entry_widget.show()
        app.main_window.folder_entry_widget.line_edit.setFocus(True)

    def enterEvent(self, ev):
        self.setStyleSheet(f"background:{app.active_theme['secondary_color']};")
        self.add_folder_image.setPixmap(self.add_folder_after_pixmap)

    def leaveEvent(self, ev):
        self.setStyleSheet(f"background:{app.active_theme['primary_color']};")
        self.add_folder_image.setPixmap(self.add_folder_before_pixmap)


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()
        self.pinned = False
        self.moving = False
        # self.app.project_data = load_app.project_data()
        self.settings_widget = SettingsWidget()
        self.setWindowTitle("Time Card App")
        self.base_width = 500
        self.base_height = 500
        self.setMinimumSize(self.base_width, self.base_height)
        self.setWindowFlags(QtCore.Qt.CustomizeWindowHint | QtCore.Qt.Tool)
        # self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Tool)
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.installEventFilter(self)
        self.set_main_position()

        self.init_central_widget()

        self.setCentralWidget(self.central_widget)

        self.createActions()
        self.createTrayIcon()
        self.setIcon()
        self.trayIcon.show()

    def eventFilter(self, object, event):
        if event.type() == QtCore.QEvent.WindowDeactivate:
            stop = False

            for file_widget in app.all_file_widgets:
                if file_widget.file.type() == "project":
                    if file_widget.hotkey_assignment_widget.isVisible():
                        stop = True

            if not self.settings_widget.isVisible() and not stop:
                if(not self.trayIcon.geometry().contains(QtGui.QCursor().pos()) and
                   not object.geometry().contains(QtGui.QCursor().pos()) and
                   not self.pinned):
                    self.minimize()

        return 0

    def set_main_position(self):
        self.move(working_width - self.base_width - 7, working_height - self.base_height - 6)

    def settings_clicked(self):
        center_window(self.settings_widget, app.main_window)
        self.settings_widget.show()

    def init_titlebar(self):
        self.titlebar = QtWidgets.QWidget()
        self.titlebar.setFixedHeight(34)
        self.titlebar.setStyleSheet(f"background:{app.active_theme['secondary_color']};")

        titlebar_hbox = QtWidgets.QHBoxLayout()
        titlebar_hbox.setContentsMargins(0, 0, 0, 0)
        titlebar_hbox.setSpacing(0)
        titlebar_hbox.addSpacing(10)

        self.window_title_label = QtWidgets.QLabel("Time Card App")
        self.window_title_label.setStyleSheet(f"color: {app.active_theme['font_color']};")
        font = QtGui.QFont()
        font.setPointSize(14)
        self.window_title_label.setFont(font)
        titlebar_hbox.addWidget(self.window_title_label)

        titlebar_hbox.addStretch()

        self.pin_button_label = ButtonLabel(app.program_data_dir + "/images/pin_before.png",
                                            app.program_data_dir + "/images/pin_after.png")
        self.pin_button_label.enabled_pixmap = QtGui.QPixmap(app.program_data_dir + "/images/pin_pressed.png")
        self.pin_button_label.clicked.connect(self.pin)
        self.pin_button_label.setToolTip("Pin the window")
        titlebar_hbox.addWidget(self.pin_button_label)
        titlebar_hbox.addSpacing(5)

        settings_button_label = ButtonLabel(app.program_data_dir + "/images/gear_before.png",
                                            app.program_data_dir + "/images/gear_after.png")
        settings_button_label.clicked.connect(self.settings_clicked)
        settings_button_label.setToolTip("Settings")
        titlebar_hbox.addWidget(settings_button_label)
        titlebar_hbox.addSpacing(5)

        minimize_button_label = ButtonLabel(app.program_data_dir + "/images/minimize_black.png",
                                            app.program_data_dir + "/images/minimize_green.png")
        minimize_button_label.clicked.connect(self.minimize)
        minimize_button_label.setToolTip("Minimize to system tray")
        titlebar_hbox.addWidget(minimize_button_label)
        titlebar_hbox.addSpacing(5)

        exit_button_label = ButtonLabel(app.program_data_dir + "/images/exit_before.png",
                                        app.program_data_dir + "/images/exit_after.png")
        exit_button_label.clicked.connect(self.exit)
        exit_button_label.setToolTip("Exit")
        titlebar_hbox.addWidget(exit_button_label)
        titlebar_hbox.addSpacing(10)

        self.titlebar.setLayout(titlebar_hbox)

    def init_central_widget(self):
        self.central_widget = QtWidgets.QWidget()
        self.central_widget.setStyleSheet(f"background:{app.active_theme['primary_color']};")

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

        main_hbox.addLayout(self.main_vbox)

        self.central_widget.setLayout(main_hbox)

    def init_scroll_widget(self):
        self.scroll_widget = QtWidgets.QWidget()

        self.scroll_widget_vbox = QtWidgets.QVBoxLayout()
        self.scroll_widget_vbox.setSpacing(0)
        self.scroll_widget_vbox.setContentsMargins(0, 0, 0, 0)

        app.all_file_widgets = []
        app.root_widgets = []

        for count, file in enumerate(app.project_data):
            if file.type() == "project":
                file_widget = ProjectWidget(file, root=True)

            else:
                file_widget = FolderWidget(file, root=True)

            app.all_file_widgets.append(file_widget)
            app.root_widgets.append(file_widget)
            self.scroll_widget_vbox.addWidget(file_widget)

            if len(app.project_data) > 1 and count != 0:
                file_widget.separator.show()

        self.buttons_separator = get_separator(2, 1)
        self.scroll_widget_vbox.addWidget(self.buttons_separator)

        if not app.root_widgets:
            self.buttons_separator.hide()

        self.init_add_buttons_widget()
        self.scroll_widget_vbox.addWidget(self.add_buttons_widget)

        self.project_entry_widget = ProjectEntryWidget(root=True)
        self.project_entry_widget.hide()
        self.scroll_widget_vbox.addWidget(self.project_entry_widget)

        self.folder_entry_widget = FolderEntryWidget(root=True)
        self.folder_entry_widget.hide()
        self.scroll_widget_vbox.addWidget(self.folder_entry_widget)

        self.scroll_widget_vbox.addWidget(get_separator(2, 1))

        self.scroll_widget_vbox.addStretch()

        self.scroll_widget.setLayout(self.scroll_widget_vbox)

        self.scroll_area = QtWidgets.QScrollArea()
        self.scrollbar = ScrollBar()
        self.scroll_area.setVerticalScrollBar(self.scrollbar)
        self.scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        # self.scroll_area.setFixedSize(500, 464)
        self.scroll_area.setMinimumWidth(2)
        # self.scroll_area.setMinimumHeight(464)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll_area.setWidget(self.scroll_widget)

    def init_add_buttons_widget(self):
        self.add_buttons_widget = QtWidgets.QWidget()

        add_buttons_widget_hbox = QtWidgets.QHBoxLayout()
        add_buttons_widget_hbox.setSpacing(0)
        add_buttons_widget_hbox.setContentsMargins(0, 0, 0, 0)

        self.add_project_button = AddProjectButton()
        self.add_folder_button = AddFolderButton()

        add_buttons_widget_hbox.addWidget(self.add_project_button)
        add_buttons_widget_hbox.addWidget(get_separator(1, 45))
        add_buttons_widget_hbox.addWidget(self.add_folder_button)

        self.add_buttons_widget.setLayout(add_buttons_widget_hbox)

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
            self.pin_button_label.setPixmap(self.pin_button_label.before_pixmap)

            self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowStaysOnTopHint)
            self.pinned = False
            self.restore()

        else:
            self.pin_button_label.is_enabled = True
            self.pin_button_label.setPixmap(self.pin_button_label.enabled_pixmap)

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
        for file_widget in app.all_file_widgets:
            if file_widget.active:
                file_widget.end_pressed()
                break

        save_settings()

        self.trayIcon.hide()
        app.quit()

    def setIcon(self):
        icon = QtGui.QIcon(app.program_data_dir + "/images/icon.png")
        self.trayIcon.setIcon(icon)
        self.setWindowIcon(icon)

    def createTrayIcon(self):
        self.trayIconMenu = QtWidgets.QMenu(self)
        self.trayIconMenu.addAction(self.minimizeAction)
        self.trayIconMenu.addAction(self.restoreAction)
        self.trayIconMenu.addSeparator()
        self.trayIconMenu.addAction(self.quitAction)

        self.trayIcon = QtWidgets.QSystemTrayIcon(self)
        self.trayIcon.setContextMenu(self.trayIconMenu)
        self.trayIcon.setToolTip("Time Card App")
        self.trayIcon.activated.connect(self.iconActivated)

    def iconActivated(self, reason):
        print(reason)
        if reason in (QtWidgets.QSystemTrayIcon.Trigger, QtWidgets.QSystemTrayIcon.DoubleClick):
            self.restore()


if __name__ == "__main__":
    # This will be to update user files after software update
    if app.settings["version"] != app.version:
        update_user_data(app.settings, app.project_data, app.user_data_dir)
        app.settings["version"] = app.version
        save_settings()
        save_project_data()

    app.active_theme = app.themes[app.settings["theme"]]

    # app.active_theme = app.themes["Dark"]  # Force Theme

    app.main_window = MainWindow()

    if app.settings["check_for_updates"]:
        try:
            app.latest_version = get_latest_version(app.project_url)

            if app.version != app.latest_version:
                app.update_message_widget = UpdateMessageWidget()
                app.update_download_widget = UpdateDownloadWidget()
                app.update_message_widget.show()

            else:
                app.main_window.show()
                app.setActiveWindow(app.main_window)

        except error.URLError:
            app.main_window.show()
            app.setActiveWindow(app.main_window)

    else:
        app.main_window.show()
        app.setActiveWindow(app.main_window)

    sys.exit(app.exec_())
