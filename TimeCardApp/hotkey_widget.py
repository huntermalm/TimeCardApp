from PyQt5 import QtWidgets, QtCore, QtGui
from extra_widgets import *
from system_hotkey import SystemRegisterError

app = QtCore.QCoreApplication.instance()

key_dict = {
    "(None)": None,
    'A': 'a',
    'B': 'b',
    'C': 'c',
    'D': 'd',
    'E': 'e',
    'F': 'f',
    'G': 'g',
    'H': 'h',
    'I': 'i',
    'J': 'j',
    'K': 'k',
    'L': 'l',
    'M': 'm',
    'N': 'n',
    'O': 'o',
    'P': 'p',
    'Q': 'q',
    'R': 'r',
    'S': 's',
    'T': 't',
    'U': 'u',
    'V': 'v',
    'W': 'w',
    'X': 'x',
    'Y': 'y',
    'Z': 'z',
    '0': '0',
    '1': '1',
    '2': '2',
    '3': '3',
    '4': '4',
    '5': '5',
    '6': '6',
    '7': '7',
    '8': '8',
    '9': '9',
    "↑": "up",
    "↓": "down",
    "→": "right",
    "←": "left",
    "home": "home",
    "end": "end",
    "ins": "insert",
    "return": "return",
    "tab": "tab",
    "space": "space",
    "backspace": "backspace",
    "del": "delete",
    "esc": "escape",
    "pause": "pause",
    "*": "kp_multiply",
    "+": "kp_add",
    "|": "kp_separator",
    "-": "kp_subtract",
    ".": "kp_decimal",
    "/": "kp_divide",
    "NUMPAD_0": "kp_0",
    "NUMPAD_1": "kp_1",
    "NUMPAD_2": "kp_2",
    "NUMPAD_3": "kp_3",
    "NUMPAD_4": "kp_4",
    "NUMPAD_5": "kp_5",
    "NUMPAD_6": "kp_6",
    "NUMPAD_7": "kp_7",
    "NUMPAD_8": "kp_8",
    "NUMPAD_9": "kp_9",
    "F1": "f1",
    "F2": "f2",
    "F3": "f3",
    "F4": "f4",
    "F5": "f5",
    "F6": "f6",
    "F7": "f7",
    "F8": "f8",
    "F9": "f9",
    "F10": "f10",
    "F11": "f11",
    "F12": "f12"
    }


class HotkeyWidget(QtWidgets.QFrame):

    def __init__(self, file, parent_project_widget):
        super().__init__()
        self.moving = False
        self.file = file
        self.parent_project_widget = parent_project_widget

        self.setWindowTitle("Hotkey Assignment")
        self.setFixedSize(400, 150)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Tool)
        self.setStyleSheet("background: white;")
        self.setFrameStyle(QtWidgets.QFrame.Box)

        self.main_vbox = QtWidgets.QVBoxLayout()
        self.main_vbox.setContentsMargins(0, 0, 0, 0)
        self.main_vbox.setSpacing(0)

        self.hotkey_vbox = QtWidgets.QVBoxLayout()
        self.hotkey_vbox.setContentsMargins(10, 10, 10, 10)
        self.hotkey_vbox.setSpacing(10)

        self.hotkey_options_hbox = QtWidgets.QHBoxLayout()
        self.hotkey_options_hbox.setContentsMargins(0, 0, 0, 0)
        self.hotkey_options_hbox.setSpacing(5)

        self.bottom_buttons_hbox = QtWidgets.QHBoxLayout()
        self.bottom_buttons_hbox.setContentsMargins(0, 0, 0, 0)
        self.bottom_buttons_hbox.setSpacing(5)

        self.init_titlebar()

        project_label = QtWidgets.QLabel(f"{self.file.name}")
        project_label_font = QtGui.QFont()
        project_label_font.setBold(True)
        project_label.setFont(project_label_font)

        self.checkboxes = []

        self.ctrl_checkbox = QtWidgets.QCheckBox("Ctrl +")
        self.checkboxes.append(self.ctrl_checkbox)
        self.ctrl_checkbox.stateChanged.connect(self.checkbox_changed)

        self.shift_checkbox = QtWidgets.QCheckBox("Shift +")
        self.checkboxes.append(self.shift_checkbox)
        self.shift_checkbox.stateChanged.connect(self.checkbox_changed)

        self.alt_checkbox = QtWidgets.QCheckBox("Alt +")
        self.checkboxes.append(self.alt_checkbox)
        self.alt_checkbox.stateChanged.connect(self.checkbox_changed)

        self.win_checkbox = QtWidgets.QCheckBox("Win +")
        self.checkboxes.append(self.win_checkbox)
        self.win_checkbox.stateChanged.connect(self.checkbox_changed)

        self.key_combobox = QtWidgets.QComboBox()
        self.key_combobox.setFixedWidth(95)
        self.key_combobox.currentIndexChanged.connect(self.combobox_changed)
        self.key_combobox.setStyleSheet("""QComboBox {
                                            border: 1px solid gray;
                                            padding: 1px 18px 1px 3px;
                                        }

                                        QComboBox:editable {
                                            background: white;
                                        }

                                        QComboBox::drop-down {
                                            subcontrol-origin: padding;
                                            subcontrol-position: top right;
                                            width: 15px;

                                            border-left-width: 0px;
                                            border-left-color: darkgray;
                                            border-left-style: solid; /* just a single line */
                                            border-top-right-radius: 3px; /* same radius as the QComboBox */
                                            border-bottom-right-radius: 3px;
                                        }

                                        QComboBox::down-arrow {
                                            image: url(./data/images/arrow_down_02.png);
                                        }

                                        QComboBox QAbstractItemView {
                                            selection-background-color: lightgray;
                                        }
                                        """)
        for key in key_dict:
            self.key_combobox.addItem(key)

        self.clear_button = ButtonLabel(app.program_data_dir + "/images/clear_before.png",
                                        app.program_data_dir + "/images/clear_after.png")
        self.clear_button.clicked.connect(self.clear_pressed)

        self.assign_button = ButtonLabel(app.program_data_dir + "/images/assign_before.png",
                                         app.program_data_dir + "/images/assign_after.png")
        self.assign_button.clicked.connect(self.assign_pressed)

        self.cancel_button = ButtonLabel(app.program_data_dir + "/images/cancel_before_02.png",
                                         app.program_data_dir + "/images/cancel_after_02.png")
        self.cancel_button.clicked.connect(self.cancel_pressed)

        self.setup_widget()

        self.main_vbox.addWidget(self.titlebar)
        self.main_vbox.addWidget(get_separator(2, 1))

        self.hotkey_vbox.addWidget(project_label)

        self.hotkey_options_hbox.addStretch()
        self.hotkey_options_hbox.addWidget(self.ctrl_checkbox)
        self.hotkey_options_hbox.addWidget(self.shift_checkbox)
        self.hotkey_options_hbox.addWidget(self.alt_checkbox)
        self.hotkey_options_hbox.addWidget(self.win_checkbox)
        self.hotkey_options_hbox.addWidget(self.key_combobox)
        self.hotkey_options_hbox.addStretch()

        self.hotkey_vbox.addLayout(self.hotkey_options_hbox)
        self.hotkey_vbox.addSpacing(15)

        self.bottom_buttons_hbox.addWidget(self.clear_button)
        self.bottom_buttons_hbox.addStretch()
        self.bottom_buttons_hbox.addWidget(self.assign_button)
        self.bottom_buttons_hbox.addWidget(self.cancel_button)

        self.hotkey_vbox.addLayout(self.bottom_buttons_hbox)

        self.main_vbox.addLayout(self.hotkey_vbox)
        self.main_vbox.addStretch()

        self.setLayout(self.main_vbox)

    def setup_widget(self):
        if self.file.hotkey:
            if "control" in self.file.hotkey:
                self.ctrl_checkbox.setCheckState(QtCore.Qt.Checked)

            if "shift" in self.file.hotkey:
                self.shift_checkbox.setCheckState(QtCore.Qt.Checked)

            if "alt" in self.file.hotkey:
                self.alt_checkbox.setCheckState(QtCore.Qt.Checked)

            if "super" in self.file.hotkey:
                self.win_checkbox.setCheckState(QtCore.Qt.Checked)

            for count, key_pair in enumerate(key_dict.items()):
                if key_pair[1] in self.file.hotkey:
                    self.key_combobox.setCurrentIndex(count)

        else:
            self.clear_pressed()

    def combobox_changed(self):
        if self.key_combobox.currentIndex() > 0:
            self.assign_button.set_disabled(False)

            self.check_hotkey_availability(self.get_hotkey_tuple())

        else:
            for checkbox in self.checkboxes:
                if checkbox.checkState() == QtCore.Qt.Checked:
                    self.assign_button.set_disabled()

    def get_amount_checked(self):
        amount_checked = 0

        for checkbox in self.checkboxes:
            if checkbox.checkState() == QtCore.Qt.Checked:
                amount_checked += 1

        return amount_checked

    def checkbox_changed(self):
        amount_checked = self.get_amount_checked()

        if amount_checked == 3:
            for checkbox in self.checkboxes:
                if checkbox.checkState() != QtCore.Qt.Checked:
                    checkbox.setDisabled(True)

        elif amount_checked == 2:
            for checkbox in self.checkboxes:
                checkbox.setDisabled(False)

        if self.key_combobox.currentIndex() > 0:
            self.check_hotkey_availability(self.get_hotkey_tuple())

        else:
            if amount_checked == 0:
                self.assign_button.set_disabled(False)

            else:
                self.assign_button.set_disabled()

    def clear_pressed(self):
        for checkbox in self.checkboxes:
            checkbox.setCheckState(QtCore.Qt.Unchecked)

        self.key_combobox.setCurrentIndex(0)

        self.assign_button.set_disabled(False)

    def get_hotkey_string(self):
        hotkey_string = ""

        if self.ctrl_checkbox.checkState() == QtCore.Qt.Checked:
            hotkey_string += "Ctrl+"

        if self.shift_checkbox.checkState() == QtCore.Qt.Checked:
            hotkey_string += "Shift+"

        if self.alt_checkbox.checkState() == QtCore.Qt.Checked:
            hotkey_string += "Alt+"

        if self.win_checkbox.checkState() == QtCore.Qt.Checked:
            hotkey_string += "Win+"

        hotkey_string += self.key_combobox.currentText()

        return hotkey_string

    def check_hotkey_availability(self, hotkey_tuple):
        hotkey_available = True

        for file_widget in app.all_file_widgets:
            if file_widget.file.type() == "project":
                if file_widget.file.hotkey == hotkey_tuple:
                    self.assign_button.set_disabled(True)
                    return

    def get_hotkey_tuple(self):
        hotkey_list = []

        if self.ctrl_checkbox.checkState() == QtCore.Qt.Checked:
            hotkey_list.append("control")

        if self.shift_checkbox.checkState() == QtCore.Qt.Checked:
            hotkey_list.append("shift")

        if self.alt_checkbox.checkState() == QtCore.Qt.Checked:
            hotkey_list.append("alt")

        if self.win_checkbox.checkState() == QtCore.Qt.Checked:
            hotkey_list.append("super")

        hotkey_list.append(key_dict[self.key_combobox.currentText()])

        return tuple(hotkey_list)

    def assign_pressed(self):
        amount_checked = self.get_amount_checked()

        if amount_checked == 0 and self.key_combobox.currentIndex() == 0:
            if self.file.hotkey:
                self.parent_project_widget.hotkey_label.setText("Unassigned")
                self.parent_project_widget.unregister_hotkey()
                self.file.hotkey = None

        else:
            self.parent_project_widget.register_hotkey(self.get_hotkey_tuple())

            self.parent_project_widget.hotkey_label.setText(self.get_hotkey_string())

            self.file.hotkey = self.get_hotkey_tuple()

        self.hide()
        app.save_project_data()

    def cancel_pressed(self):
        self.setup_widget()
        self.hide()

    def init_titlebar(self):
        self.titlebar = QtWidgets.QWidget()
        self.titlebar.setFixedHeight(34)
        self.titlebar.setStyleSheet("background-color:lightgrey;")

        titlebar_hbox = QtWidgets.QHBoxLayout()
        titlebar_hbox.setContentsMargins(0, 0, 0, 0)
        titlebar_hbox.setSpacing(0)
        titlebar_hbox.addSpacing(3)

        window_title_label = QtWidgets.QLabel("Hotkey Assignment")
        font = QtGui.QFont()
        font.setPointSize(12)
        window_title_label.setFont(font)
        titlebar_hbox.addWidget(window_title_label)

        titlebar_hbox.addStretch()

        exit_button_label = ButtonLabel(app.program_data_dir + "/images/exit_before.png",
                                        app.program_data_dir + "/images/exit_after.png")
        exit_button_label.clicked.connect(self.cancel_pressed)
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
