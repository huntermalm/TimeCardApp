from urllib.request import urlopen as uReq
from bs4 import BeautifulSoup as soup
from PyQt5 import QtCore, QtGui, QtWidgets
import requests


app = QtCore.QCoreApplication.instance()


def get_latest_version(project_url):
    if project_url[-1] == "/":
        project_url = project_url[0:-1]

    latest_release_url = f"{project_url}/releases/latest"

    uClient = uReq(latest_release_url)
    page_html = uClient.read()
    uClient.close()

    page_soup = soup(page_html, "html.parser")

    header = page_soup.findAll("div", {"class": "release-header"})[0]

    return header.h1.a.contents[0]


class UpdateDownloadWidget(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Downloading Update...")
        self.setFixedSize(300, 100)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)

        self.init_download_url_and_filename(app.project_url)

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

        with open(app.user_data_dir + self.file_name, "wb") as f:
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

        current_version_label = QtWidgets.QLabel(f"Current Version: {app.version}")
        update_message_vbox.addWidget(current_version_label)

        latest_version_label = QtWidgets.QLabel(f"Latest Version: {app.latest_version}")
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
        app.main_window.show()
        self.hide()
        ev.ignore()

    def no_clicked(self):
        app.main_window.show()
        self.hide()
        self.deleteLater()

    def yes_clicked(self):
        self.hide()
        app.update_download_widget.show()
        app.processEvents()
        app.update_download_widget.download_update()
        app.main_window.trayIcon.hide()
        app.quit()

        from subprocess import Popen
        Popen([app.user_data_dir + app.update_download_widget.file_name])
