"""
This is a Python3 PyQt5 firmware upload GUI for the SparkFun RTK products - based on ESP32 esptool.exe

MIT license

Please see the LICENSE.md for more details

"""

import sys
import os
import os.path
import platform

from typing import Iterator, Tuple

from PyQt5.QtCore import QSettings, QProcess, QTimer, Qt, QIODevice, pyqtSignal, pyqtSlot, QObject
from PyQt5.QtWidgets import QWidget, QLabel, QComboBox, QGridLayout, \
    QPushButton, QApplication, QLineEdit, QFileDialog, QPlainTextEdit, \
    QAction, QActionGroup, QMenu, QMenuBar, QMainWindow, QMessageBox
from PyQt5.QtGui import QCloseEvent, QTextCursor, QIcon, QFont
from PyQt5.QtSerialPort import QSerialPortInfo

_APP_VERSION = "v1.4.3"
_APP_NAME = "RTK Firmware Uploader"

# sub folder for our resource files
_RESOURCE_DIRECTORY = "resource"

#https://stackoverflow.com/a/50914550
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, _RESOURCE_DIRECTORY, relative_path)

# determine the current GUI style
import darkdetect

# import action things - the .syntax is used since these are part of the package
from .au_action import AxJob
from .au_act_esptool import AUxEsptoolUploadFirmware
from .au_worker import AUxWorker

#----------------------------------------------------------------
# ux_is_darkmode()
#
# Helpful function used during setup to determine if the Ux is in
# dark mode
_is_darkmode = None
def ux_is_darkmode() -> bool:
    global _is_darkmode

    if _is_darkmode is not None:
        return _is_darkmode

    osName = platform.system()

    if osName == "Darwin":
        _is_darkmode = darkdetect.isDark()

    elif osName == "Windows":
        # it appears that the Qt interface on Windows doesn't apply DarkMode
        # So, just keep it light
        _is_darkmode = False
    elif osName == "Linux":
        # Need to check this on Linux at some pont
        _is_darkmod = False

    else:
        _is_darkmode = False

    return _is_darkmode

# Setting constants
SETTING_PORT_NAME = 'port_name'
SETTING_FILE_LOCATION = 'file_location'
#SETTING_PARTITION_LOCATION = 'partition_location'
SETTING_BAUD_RATE = 'baud'

def gen_serial_ports() -> Iterator[Tuple[str, str, str]]:
    """Return all available serial ports."""
    ports = QSerialPortInfo.availablePorts()
    return ((p.description(), p.portName(), p.systemLocation()) for p in ports)

# noinspection PyArgumentList

class MainWidget(QWidget):
    """Main Widget."""

    sig_message     = pyqtSignal(str)
    sig_finished    = pyqtSignal(int)

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self.flashSize = 0

        # File location line edit
        self.file_label = QLabel(self.tr('Firmware File:'))
        self.fileLocation_lineedit = QLineEdit()
        self.file_label.setBuddy(self.fileLocation_lineedit)
        self.fileLocation_lineedit.setEnabled(False)
        self.fileLocation_lineedit.returnPressed.connect(self.on_browse_btn_pressed)

        # Browse for new file button
        self.browse_btn = QPushButton(self.tr('Browse'))
        self.browse_btn.setEnabled(True)
        self.browse_btn.pressed.connect(self.on_browse_btn_pressed)

        # # Partition file location line edit
        # self.partition_label = QLabel(self.tr('Partition File:'))
        # self.partitionFileLocation_lineedit = QLineEdit()
        # self.partition_label.setBuddy(self.partitionFileLocation_lineedit)
        # self.partitionFileLocation_lineedit.setEnabled(False)
        # self.partitionFileLocation_lineedit.returnPressed.connect(self.on_partition_browse_btn_pressed)

        # # Browse for new file button
        # self.partition_browse_btn = QPushButton(self.tr('Browse'))
        # self.partition_browse_btn.setEnabled(True)
        # self.partition_browse_btn.pressed.connect(self.on_partition_browse_btn_pressed)

        # Port Combobox
        self.port_label = QLabel(self.tr('COM Port:'))
        self.port_combobox = QComboBox()
        self.port_label.setBuddy(self.port_combobox)
        self.update_com_ports()

        # Refresh Button
        self.refresh_btn = QPushButton(self.tr('Refresh'))
        self.refresh_btn.clicked.connect(self.on_refresh_btn_pressed)

        # Baudrate Combobox
        self.baud_label = QLabel(self.tr('Baud Rate:'))
        self.baud_combobox = QComboBox()
        self.baud_label.setBuddy(self.baud_combobox)
        self.update_baud_rates()

        # Upload Button
        myFont=QFont()
        myFont.setBold(True)
        self.upload_btn = QPushButton(self.tr('  Upload Firmware  '))
        self.upload_btn.setFont(myFont)
        self.upload_btn.clicked.connect(self.on_upload_btn_pressed)

        # Reset Button
        self.reset_btn = QPushButton(self.tr('Reset ESP32'))
        self.reset_btn.clicked.connect(self.on_reset_btn_pressed)

        # Messages Bar
        self.messages_label = QLabel(self.tr('Status / Warnings:'))

        # Messages Window
        self.messageBox = QPlainTextEdit()
        color =  "C0C0C0" if ux_is_darkmode() else "424242"
        self.messageBox.setStyleSheet("QPlainTextEdit { color: #" + color + ";}")
        self.messageBox.setReadOnly(True)
        self.messageBox.clear()

        # Arrange Layout
        layout = QGridLayout()
        
        layout.addWidget(self.file_label, 1, 0)
        layout.addWidget(self.fileLocation_lineedit, 1, 1)
        layout.addWidget(self.browse_btn, 1, 2)

        # layout.addWidget(self.partition_label, 2, 0)
        # layout.addWidget(self.partitionFileLocation_lineedit, 2, 1)
        # layout.addWidget(self.partition_browse_btn, 2, 2)

        layout.addWidget(self.port_label, 2, 0)
        layout.addWidget(self.port_combobox, 2, 1)
        layout.addWidget(self.refresh_btn, 2, 2)

        layout.addWidget(self.baud_label, 3, 0)
        layout.addWidget(self.baud_combobox, 3, 1)
        layout.addWidget(self.upload_btn, 3, 2)

        layout.addWidget(self.reset_btn, 4, 2)

        layout.addWidget(self.messages_label, 5, 0)
        layout.addWidget(self.messageBox, 6, 0, 6, 3)

        self.setLayout(layout)

        self.settings = QSettings()
        #self._clean_settings() # This will delete all existing settings! Use with caution!        
        self._load_settings()

        self.setWindowTitle( _APP_NAME + " - " + _APP_VERSION)

        # setup our background worker thread ...

        # connect the signals from the background processor to callback
        # methods/slots. This makes it thread safe
        self.sig_message.connect(self.appendMessage)
        self.sig_finished.connect(self.on_finished)

        # Create our background worker object, which also will do work in it's
        # own thread.
        self._worker = AUxWorker(self.on_worker_callback)

        # add the actions/commands for this app to the background processing thread.
        # These actions are passed jobs to execute.
        self._worker.add_action(AUxEsptoolUploadFirmware())

    #--------------------------------------------------------------
    # callback function for the background worker.
    #
    # It is assumed that this method is called by the background thread
    # so signals and used to relay the call to the GUI running on the
    # main thread

    def on_worker_callback(self, msg_type, arg):

        if msg_type == AUxWorker.TYPE_MESSAGE:
            self.sig_message.emit(arg)
        elif msg_type == AUxWorker.TYPE_FINISHED:
            self.sig_finished.emit(arg)

    @pyqtSlot(str)
    def appendMessage(self, msg: str) -> None:
        if msg.startswith("\r"):
            self.messageBox.moveCursor(QTextCursor.StartOfLine, QTextCursor.KeepAnchor)
            self.messageBox.cut()
            self.messageBox.insertPlainText(msg[1:])
        else:
            self.messageBox.insertPlainText(msg)
        self.messageBox.ensureCursorVisible()
        self.messageBox.repaint()

        if msg.find("Detected flash size: 4MB") >= 0:
            self.flashSize = 4
        elif msg.find("Detected flash size: 8MB") >= 0:
            self.flashSize = 8
        elif msg.find("Detected flash size: 16MB") >= 0:
            self.flashSize = 16
        elif msg.find("Detected flash size: ") >= 0:
            self.flashSize = 0

    @pyqtSlot(str)
    def writeMessage(self, msg: str) -> None:
        self.messageBox.moveCursor(QTextCursor.End)
        #self.messageBox.ensureCursorVisible()
        self.messageBox.appendPlainText(msg)
        self.messageBox.ensureCursorVisible()
        self.messageBox.repaint()
        #QApplication.processEvents()

    #--------------------------------------------------------------
    # on_finished()
    #
    #  Slot for sending the "on finished" signal from the background thread
    #
    #  Called when the backgroudn job is finished and includes a status value
    @pyqtSlot(int)
    def on_finished(self) -> None:

        # re-enable the UX
        self.disable_interface(False)

        self.running = False

    def _load_settings(self) -> None:
        """Load settings on startup."""
        port_name = self.settings.value(SETTING_PORT_NAME)
        if port_name is not None:
            index = self.port_combobox.findData(port_name)
            if index > -1:
                self.port_combobox.setCurrentIndex(index)

        lastFile = self.settings.value(SETTING_FILE_LOCATION)
        if lastFile is not None:
            self.fileLocation_lineedit.setText(lastFile)

        # lastFile = self.settings.value(SETTING_PARTITION_LOCATION)
        # if lastFile is not None:
        #     self.partitionFileLocation_lineedit.setText(lastFile)
        # else:
        #     self.partitionFileLocation_lineedit.setText(resource_path("RTK_Surveyor.ino.partitions.bin"))

        baud = self.settings.value(SETTING_BAUD_RATE)
        if baud is not None:
            index = self.baud_combobox.findData(baud)
            if index > -1:
                self.baud_combobox.setCurrentIndex(index)

    def _save_settings(self) -> None:
        """Save settings on shutdown."""
        self.settings.setValue(SETTING_PORT_NAME, self.port)
        self.settings.setValue(SETTING_FILE_LOCATION, self.theFileName)
        # self.settings.setValue(SETTING_PARTITION_LOCATION, self.thePartitionFileName)
        self.settings.setValue(SETTING_BAUD_RATE, self.baudRate)

    def _clean_settings(self) -> None:
        """Clean (remove) all existing settings."""
        self.settings.clear()

    def show_error_message(self, msg: str) -> None:
        """Show a Message Box with the error message."""
        QMessageBox.critical(self, QApplication.applicationName(), str(msg))

    def update_com_ports(self) -> None:
        """Update COM Port list in GUI."""
        previousPort = self.port # Record the previous port before we clear the combobox
        
        self.port_combobox.clear()

        index = 0
        indexOfPrevious = -1
        for desc, name, sys in gen_serial_ports():
            longname = desc + " (" + name + ")"
            self.port_combobox.addItem(longname, sys)
            if(sys == previousPort): # Previous port still exists so record it
                indexOfPrevious = index
            index = index + 1

        if indexOfPrevious > -1: # Restore the previous port if it still exists
            self.port_combobox.setCurrentIndex(indexOfPrevious)

    def update_baud_rates(self) -> None:
        """Update baud rate list in GUI."""
        # Highest speed first so code defaults to that
        # if settings.value(SETTING_BAUD_RATE) is None
        self.baud_combobox.clear()
        self.baud_combobox.addItem("921600", 921600)
        self.baud_combobox.addItem("460800", 460800)
        self.baud_combobox.addItem("115200", 115200)

    @property
    def port(self) -> str:
        """Return the current serial port."""
        return str(self.port_combobox.currentData())

    @property
    def baudRate(self) -> str:
        """Return the current baud rate."""
        return str(self.baud_combobox.currentData())

    @property
    def theFileName(self) -> str:
        """Return the file name."""
        return self.fileLocation_lineedit.text()

    # @property
    # def thePartitionFileName(self) -> str:
    #     """Return the partition file name."""
    #     return self.partitionFileLocation_lineedit.text()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle Close event of the Widget."""
        try:
            self._save_settings()
        except:
            pass

        # shutdown the background worker/stop it so the app exits correctly
        self._worker.shutdown()

        event.accept()

    def on_refresh_btn_pressed(self) -> None:
        self.update_com_ports()
        self.writeMessage("Ports Refreshed\n")

    def on_browse_btn_pressed(self) -> None:
        """Open dialog to select bin file."""
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(
            None,
            "Select Firmware to Upload",
            "",
            "Firmware Files (*.bin);;All Files (*)",
            options=options)
        if fileName:
            self.fileLocation_lineedit.setText(fileName)

    # def on_partition_browse_btn_pressed(self) -> None:
    #     """Open dialog to select partition bin file."""
    #     options = QFileDialog.Options()
    #     fileName, _ = QFileDialog.getOpenFileName(
    #         None,
    #         "Select Partition File",
    #         "",
    #         "Parition Files (*.bin);;All Files (*)",
    #         options=options)
    #     if fileName:
    #         self.partitionFileLocation_lineedit.setText(fileName)

    #--------------------------------------------------------------
    # disable_interface()
    #
    # Enable/Disable portions of the ux - often used when a job is running
    #
    def disable_interface(self, bDisable=False):

        self.upload_btn.setDisabled(bDisable)
        self.reset_btn.setDisabled(bDisable)

    def on_reset_btn_pressed(self) -> None:
        """Reset the ESP32"""
        portAvailable = False
        for desc, name, sys in gen_serial_ports():
            if (sys == self.port):
                portAvailable = True
        if (portAvailable == False):
            self.writeMessage("Port No Longer Available")
            return

        try:
            self._save_settings() # Save the settings in case the upload crashes
        except:
            pass

        self.writeMessage("Resetting ESP32\n")

        command = []
        command.extend(["--chip","esp32"])
        command.extend(["--port",self.port])
        #command.extend(["--baud",self.baudRate])
        command.extend(["--before","default_reset","run"])


        # Create a job and add it to the job queue. The worker thread will pick this up and
        # process the job. Can set job values using dictionary syntax, or attribute assignments
        #
        # Note - the job is defined with the ID of the target action
        theJob = AxJob(AUxEsptoolUploadFirmware.ACTION_ID, {"command":command})

        # Send the job to the worker to process
        self._worker.add_job(theJob)

        self.disable_interface(True)

    def on_upload_btn_pressed(self) -> None:
        """Upload the firmware"""
        portAvailable = False
        for desc, name, sys in gen_serial_ports():
            if (sys == self.port):
                portAvailable = True
        if (portAvailable == False):
            self.writeMessage("Port No Longer Available")
            return

        fileExists = False
        try:
            f = open(self.theFileName)
            fileExists = True
        except IOError:
            fileExists = False
        finally:
            if (fileExists == False):
                self.writeMessage("File Not Found")
                return
            f.close()

        # fileExists = False
        # try:
        #     f = open(self.thePartitionFileName)
        #     fileExists = True
        # except IOError:
        #     fileExists = False
        # finally:
        #     if (fileExists == False):
        #         self.writeMessage("File Not Found")
        #         return
        #     f.close()

        try:
            self._save_settings() # Save the settings in case the upload crashes
        except:
            pass

        self.flashSize = 0

        self.writeMessage("Detecting flash size\n\n")

        command = []
        command.extend(["--chip","esp32"])
        command.extend(["--port",self.port])
        command.extend(["--baud",self.baudRate])
        command.extend(["flash_id"])

        # Create a job and add it to the job queue. The worker thread will pick this up and
        # process the job. Can set job values using dictionary syntax, or attribute assignments
        #
        # Note - the job is defined with the ID of the target action
        theJob = AxJob(AUxEsptoolUploadFirmware.ACTION_ID, {"command":command})

        self.running = True

        # Send the job to the worker to process
        self._worker.add_job(theJob)

        self.disable_interface(True)

        # Wait for the job to finish
        while (self.running):
            QApplication.processEvents()

        if self.flashSize == 0:
            self.writeMessage("Flash size not detected! Defaulting to 16MB\n")
            self.flashSize = 16
        else:
            self.writeMessage("Flash size is " + str(self.flashSize) + "MB\n")

        thePartitionFileName = ''
        firmwareSizeCorrect = True
        if self.flashSize == 16:
            thePartitionFileName = resource_path("RTK_Surveyor_Partitions_16MB.bin")
            # if self.theFileName.find("16MB") < 0:
            #     firmwareSizeCorrect = False
        else:
            thePartitionFileName = resource_path("RTK_Surveyor_Partitions_4MB.bin")
            # if self.theFileName.find("4MB") < 0:
            #     firmwareSizeCorrect = False

        if firmwareSizeCorrect == False:
            reply = QMessageBox.warning(self, "Firmware size mismatch", "Do you want to continue?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return

        self.writeMessage("Uploading firmware\n")

        command = []
        #command.extend(["--trace"]) # Useful for debugging
        command.extend(["--chip","esp32"])
        command.extend(["--port",self.port])
        command.extend(["--baud",self.baudRate])
        command.extend(["--before","default_reset","--after","hard_reset","write_flash","-z","--flash_mode","dio","--flash_freq","80m","--flash_size","detect"])
        command.extend(["0x1000",resource_path("RTK_Surveyor.ino.bootloader.bin")])
        command.extend(["0x8000",thePartitionFileName])
        command.extend(["0xe000",resource_path("boot_app0.bin")])
        command.extend(["0x10000",self.theFileName])

        #print("python esptool.py %s\n\n" % " ".join(command)) # Useful for debugging - cut and paste into a command prompt

        # Create a job and add it to the job queue. The worker thread will pick this up and
        # process the job. Can set job values using dictionary syntax, or attribute assignments
        #
        # Note - the job is defined with the ID of the target action
        theJob = AxJob(AUxEsptoolUploadFirmware.ACTION_ID, {"command":command})

        # Send the job to the worker to process
        self._worker.add_job(theJob)

        self.disable_interface(True)

def startUploaderGUI():
    """Start the GUI"""
    from sys import exit as sysExit
    app = QApplication([])
    app.setOrganizationName('SparkFun Electronics')
    app.setApplicationName(_APP_NAME + ' - ' + _APP_VERSION)
    app.setWindowIcon(QIcon(resource_path("RTK.png")))
    app.setApplicationVersion(_APP_VERSION)
    w = MainWidget()
    w.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    startUploaderGUI()