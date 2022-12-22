# Copyright 2018-2022 Benjamin Wiegand <benjamin.wiegand@physik.hu-berlin.de>
#
# This file is part of Linien and based on redpid.
#
# Linien is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Linien is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Linien.  If not, see <http://www.gnu.org/licenses/>.

from time import sleep
from typing import Callable

from linien_gui.threads import RemoteServerInstallationThread
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QDialog, QListWidget, QMessageBox, QVBoxLayout, QWidget
from pyqtgraph import QtCore


class SSHCommandOutputWidget(QListWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setSelectionMode(self.NoSelection)

    command_ended = pyqtSignal()

    def run(self, thread: QThread):
        thread.start()
        self.read_output_and_update_widget(thread)
        self.command_ended.emit()

    def read_output_and_update_widget(self, thread: QThread):
        if thread.isFinished() and thread.out_stream.empty:
            self.addItem("Finished. Close window to continue.")
            return
        else:
            while not thread.out_stream.empty():
                self.addItem(thread.out_stream.read().rstrip())
                self.scrollToBottom()
        # update widget every 100 ms
        QtCore.QTimer.singleShot(100, lambda: self.run(thread))


def show_installation_progress_widget(
    parent: QWidget, device: dict, callback: Callable
):

    # Define and open dialog window
    window = QDialog(parent)
    window.setWindowTitle("Deploying Linien Server")
    window.resize(800, 600)
    window_layout = QVBoxLayout(window)
    widget = SSHCommandOutputWidget(parent)
    window_layout.addWidget(widget)
    window.setLayout(window_layout)
    window.setModal(True)
    window.setWindowModality(QtCore.Qt.WindowModal)
    window.show()

    # Define what happens after the command has finished
    def after_command():
        # FIXME: This is a hack to make sure the window is shown for a little while
        sleep(3)
        window.hide()
        callback()

    widget.command_ended.connect(after_command)

    # Create and start thread
    thread = RemoteServerInstallationThread(device)
    widget.run(thread)

    return window


class LoadingDialog(QMessageBox):
    aborted = pyqtSignal()

    def __init__(self, parent: QWidget, host: str):
        super().__init__(parent)

        self.setIcon(QMessageBox.Information)
        self.setText(f"Connecting to {host}")
        self.setWindowTitle("Connecting")
        self.setModal(True)
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.setStandardButtons(QMessageBox.NoButton)
        self.show()

    def closeEvent(self, *args):
        self.aborted.emit()

    def keyPressEvent(self, event):
        key = event.key()
        if key == QtCore.Qt.Key_Escape:
            self.close()


def error_dialog(parent: QWidget, error):
    return QMessageBox.question(parent, "Error", error, QMessageBox.Ok, QMessageBox.Ok)


def question_dialog(parent, question, title):
    box = QMessageBox(parent)
    box.setText(question)
    box.setWindowTitle(title)
    reply = QMessageBox.question(
        parent, title, question, QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
    )

    return reply == QMessageBox.Yes


def ask_for_parameter_restore_dialog(parent, question, title):
    box = QMessageBox(parent)
    box.setText(question)
    box.setWindowTitle(title)
    # do_nothing_button
    _ = box.addButton("Keep remote parameters", QMessageBox.NoRole)
    upload_button = box.addButton("Upload local parameters", QMessageBox.YesRole)

    box.exec_()

    return box.clickedButton() == upload_button
