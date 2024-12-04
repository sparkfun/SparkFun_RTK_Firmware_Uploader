"""
This is a Python3 PyQt5 firmware upload GUI for the SparkFun RTK products - based on ESP32 esptool.exe

MIT license

Please see the LICENSE.md for more details

"""

# import action things - the .syntax is used since these are part of the package
from .au_worker import AUxWorker
from .au_action import AxJob
from .au_act_esptool import AUxEsptoolDetectFlash, AUxEsptoolUploadFirmware, AUxEsptoolResetESP32, \
    AUxEsptoolEraseFlash, AUxEsptoolReadMAC

import darkdetect
import sys
import os
import os.path
import platform

import serial

from time import sleep

from typing import Iterator, Tuple

from PyQt5.QtCore import QSettings, QProcess, QTimer, Qt, QIODevice, pyqtSignal, pyqtSlot, QObject
from PyQt5.QtWidgets import QWidget, QLabel, QComboBox, QGridLayout, \
    QPushButton, QApplication, QLineEdit, QFileDialog, QPlainTextEdit, \
    QAction, QActionGroup, QMenu, QMenuBar, QMainWindow, QMessageBox
from PyQt5.QtGui import QCloseEvent, QTextCursor, QIcon, QFont
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo

_APP_NAME = "RTK Firmware Uploader"

# sub folder for our resource files
_RESOURCE_DIRECTORY = "resource"

#https://stackoverflow.com/a/50914550
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, _RESOURCE_DIRECTORY, relative_path)

def get_version(rel_path: str) -> str:
    try: 
        with open(resource_path(rel_path), encoding='utf-8') as fp:
            for line in fp.read().splitlines():
                if line.startswith("__version__"):
                    delim = '"' if '"' in line else "'"
                    return line.split(delim)[1]
            raise RuntimeError("Unable to find version string.")
    except:
        raise RuntimeError("Unable to find _version.py.")

_APP_VERSION = get_version("_version.py")

# ----------------------------------------------------------------
# hack to know when a combobox menu is being shown. Helpful if contents
# of list are dynamic -- like serial ports.

class AUxComboBox(QComboBox):

    popupAboutToBeShown = pyqtSignal()

    def showPopup(self):
        self.popupAboutToBeShown.emit()
        super().showPopup()

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

    sig_message = pyqtSignal(str)
    sig_finished = pyqtSignal(int, str, int)

    def _createMenuBar(self):
        self.menuBar = QMenuBar(self)

        self.extrasReadMACAction = QAction("Read WiFi MAC", self)
        self.extrasResetAction = QAction("Reset ESP32", self)
        self.extrasEraseAction = QAction("Erase Flash", self)

        extrasMenu = self.menuBar.addMenu("Extras")
        extrasMenu.addAction(self.extrasReadMACAction)
        extrasMenu.addAction(self.extrasResetAction)
        extrasMenu.addAction(self.extrasEraseAction)

        self.extrasReadMACAction.triggered.connect(self.readMAC)
        self.extrasResetAction.triggered.connect(self.tera_term_reset)
        self.extrasEraseAction.triggered.connect(self.eraseChip)

        self.extrasReadMACAction.setDisabled(False)
        self.extrasResetAction.setDisabled(False)
        self.extrasEraseAction.setDisabled(False)

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self.flashSize = 0
        self.macAddress = "UNKNOWN"

        self._createMenuBar()

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
        self.port_combobox = AUxComboBox()
        self.port_label.setBuddy(self.port_combobox)
        self.update_com_ports()
        self.port_combobox.popupAboutToBeShown.connect(self.on_port_combobox)

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

        layout.addWidget(self.menuBar, 1, 0)

        layout.addWidget(self.file_label, 2, 0)
        layout.addWidget(self.fileLocation_lineedit, 2, 1)
        layout.addWidget(self.browse_btn, 2, 2)

        # layout.addWidget(self.partition_label, 3, 0)
        # layout.addWidget(self.partitionFileLocation_lineedit, 3, 1)
        # layout.addWidget(self.partition_browse_btn, 3, 2)

        layout.addWidget(self.port_label, 3, 0)
        layout.addWidget(self.port_combobox, 3, 1)

        layout.addWidget(self.baud_label, 4, 0)
        layout.addWidget(self.baud_combobox, 4, 1)
        layout.addWidget(self.upload_btn, 4, 2)

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
        self._worker.add_action(AUxEsptoolDetectFlash(), AUxEsptoolUploadFirmware(), AUxEsptoolResetESP32(), \
                                AUxEsptoolEraseFlash(), AUxEsptoolReadMAC())

    #--------------------------------------------------------------
    # callback function for the background worker.
    #
    # It is assumed that this method is called by the background thread
    # so signals and used to relay the call to the GUI running on the
    # main thread

    def on_worker_callback(self, *args): #msg_type, arg):

        # need a min of 2 args (id, arg)
        if len(args) < 2:
            self.writeMessage("Invalid parameters from the uploader.")
            return

        msg_type = args[0]
        if msg_type == AUxWorker.TYPE_MESSAGE:
            self.sig_message.emit(args[1])
        elif msg_type == AUxWorker.TYPE_FINISHED:
            # finished takes 3 args - status, job type, and job id
            if len(args) < 4:
                self.writeMessage("Invalid parameters from the uploader.");
                return;

            self.sig_finished.emit(args[1], args[2], args[3])
            
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

        macAddrPtr = msg.find("MAC: ")
        if macAddrPtr >= 0:
            self.macAddress = msg[macAddrPtr + len("MAC: "):]

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
    @pyqtSlot(int, str, int)
    def on_finished(self, status, action_type, job_id) -> None:

        # If the Read MAC is finished, re-enable the UX
        if action_type == AUxEsptoolReadMAC.ACTION_ID:
            self.writeMessage("Read MAC complete...")
            self.writeMessage("WiFi MAC Address is {}".format(self.macAddress))
            self.disable_interface(False)

        # If the flash erase is finished, re-enable the UX
        if action_type == AUxEsptoolEraseFlash.ACTION_ID:
            self.writeMessage("Flash erase complete...")
            self.disable_interface(False)

        # If the flash detection is finished, trigger the upload
        if action_type == AUxEsptoolDetectFlash.ACTION_ID:
            self.writeMessage("Flash detection complete. Uploading firmware...")
            self.do_upload()

        # If the upload is finished, trigger a reset
        if action_type == AUxEsptoolUploadFirmware.ACTION_ID:
            self.writeMessage("Firmware upload complete. Resetting ESP32...")
            self.esptool_reset()

        # If the reset is finished, re-enable the UX
        if action_type == AUxEsptoolResetESP32.ACTION_ID:
            self.writeMessage("Reset complete...")
            self.disable_interface(False)

    # --------------------------------------------------------------
    # on_port_combobox()
    #
    # Called when the combobox pop-up menu is about to be shown
    #
    # Use this event to dynamically update the displayed ports
    #
    @pyqtSlot()
    def on_port_combobox(self):
        self.update_com_ports()

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
        self.extrasEraseAction.setDisabled(bDisable)
        self.extrasReadMACAction.setDisabled(bDisable)
        self.extrasResetAction.setDisabled(bDisable)

    def eraseChip(self) -> None:
        """Perform erase_flash"""
        portAvailable = False
        for desc, name, sys in gen_serial_ports():
            if (sys == self.port):
                portAvailable = True
        if (portAvailable == False):
            self.writeMessage("Port No Longer Available")
            return

        try:
            self._save_settings() # Save the settings in case the command fails
        except:
            pass

        self.writeMessage("Erasing flash\n\n")

        command = []
        command.extend(["--chip","esp32"])
        command.extend(["--port",self.port])
        command.extend(["--before","default_reset"])
        command.extend(["erase_flash"])

        # Create a job and add it to the job queue. The worker thread will pick this up and
        # process the job. Can set job values using dictionary syntax, or attribute assignments
        #
        # Note - the job is defined with the ID of the target action
        theJob = AxJob(AUxEsptoolEraseFlash.ACTION_ID, {"command":command})

        # Send the job to the worker to process
        self._worker.add_job(theJob)

        self.disable_interface(True)

    def readMAC(self) -> None:
        """Perform read_mac"""
        portAvailable = False
        for desc, name, sys in gen_serial_ports():
            if (sys == self.port):
                portAvailable = True
        if (portAvailable == False):
            self.writeMessage("Port No Longer Available")
            return

        try:
            self._save_settings() # Save the settings in case the command fails
        except:
            pass

        self.writeMessage("Reading WiFi MAC address\n\n")

        command = []
        command.extend(["--chip","esp32"])
        command.extend(["--port",self.port])
        command.extend(["--before","default_reset"])
        command.extend(["read_mac"])

        # Create a job and add it to the job queue. The worker thread will pick this up and
        # process the job. Can set job values using dictionary syntax, or attribute assignments
        #
        # Note - the job is defined with the ID of the target action
        theJob = AxJob(AUxEsptoolReadMAC.ACTION_ID, {"command":command})

        # Send the job to the worker to process
        self._worker.add_job(theJob)

        self.disable_interface(True)

    def on_upload_btn_pressed(self) -> None:
        """Get ready to upload the firmware. First, detect the flash size"""
        portAvailable = False
        for desc, name, sys in gen_serial_ports():
            if (sys == self.port):
                portAvailable = True
        if (portAvailable == False):
            self.writeMessage("Port No Longer Available")
            return

        try:
            self._save_settings() # Save the settings in case the command fails
        except:
            pass

        self.flashSize = 0

        self.writeMessage("Detecting flash size\n\n")

        command = []
        command.extend(["--chip","esp32"])
        command.extend(["--port",self.port])
        command.extend(["--before","default_reset","--after","no_reset"])
        command.extend(["flash_id"])

        # Create a job and add it to the job queue. The worker thread will pick this up and
        # process the job. Can set job values using dictionary syntax, or attribute assignments
        #
        # Note - the job is defined with the ID of the target action
        theJob = AxJob(AUxEsptoolDetectFlash.ACTION_ID, {"command":command})

        # Send the job to the worker to process
        self._worker.add_job(theJob)

        self.disable_interface(True)

    def do_upload(self) -> None:
        """Upload the firmware"""
        portAvailable = False
        for desc, name, sys in gen_serial_ports():
            if (sys == self.port):
                portAvailable = True
        if (portAvailable == False):
            self.writeMessage("Port No Longer Available")
            self.disable_interface(False)
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
                self.disable_interface(False)
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
            self._save_settings() # Save the settings in case the command fails
        except:
            pass

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
        elif self.flashSize == 8:
            thePartitionFileName = resource_path("RTK_Everywhere_Partitions_8MB.bin")
            # if self.theFileName.find("8MB") < 0:
            #     firmwareSizeCorrect = False
        else:
            thePartitionFileName = resource_path("RTK_Surveyor_Partitions_4MB.bin")
            # if self.theFileName.find("4MB") < 0:
            #     firmwareSizeCorrect = False

        if firmwareSizeCorrect == False:
            reply = QMessageBox.warning(self, "Firmware size mismatch", "Do you want to continue?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                self.disable_interface(False)
                return

        sleep(1.0);
        self.writeMessage("Uploading firmware\n")

        baud = self.baudRate
        if baud == "921600":
            if (platform.system() == "Darwin"): # 921600 fails on MacOS
                self.writeMessage("MacOS detected. Limiting baud to 460800\n")
                baud = "460800"
            if ((str(self.port_combobox.currentText()).find("CH342") >= 0) and (self.flashSize == 16)): # 921600 fails on CH342 + 16MB ESP32 (ie, RTK Torch)
                self.writeMessage("RTK Torch detected. Limiting baud to 460800\n")
                baud = "460800"

        command = []
        #command.extend(["--trace"]) # Useful for debugging
        command.extend(["--chip","esp32"])
        command.extend(["--port",self.port])
        command.extend(["--baud",baud])
        command.extend(["--before","default_reset","--after","no_reset","write_flash","-z","--flash_mode","dio","--flash_freq","80m","--flash_size","detect"])
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

        self.disable_interface(True) # Redundant... Interface is still disabled from flash detect

    def esptool_reset(self) -> None:
        """Tell the ESP32 to reset/restart"""
        portAvailable = False
        for desc, name, sys in gen_serial_ports():
            if (sys == self.port):
                portAvailable = True
        if (portAvailable == False):
            self.writeMessage("Port No Longer Available")
            self.disable_interface(False)
            return

        try:
            self._save_settings() # Save the settings in case the command fails
        except:
            pass

        sleep(1.0);
        self.writeMessage("Resetting ESP32\n")

        # ---- The esptool method -----

        command = []
        command.extend(["--chip","esp32"])
        command.extend(["--port",self.port])
        command.extend(["--before","default_reset","run"])

        # Create a job and add it to the job queue. The worker thread will pick this up and
        # process the job. Can set job values using dictionary syntax, or attribute assignments
        #
        # Note - the job is defined with the ID of the target action
        theJob = AxJob(AUxEsptoolResetESP32.ACTION_ID, {"command":command})

        # Send the job to the worker to process
        self._worker.add_job(theJob)

        self.disable_interface(True)

    def tera_term_reset(self) -> None:
        """Reset the ESP32 the TeraTerm way"""
        portAvailable = False
        for desc, name, sys in gen_serial_ports():
            if (sys == self.port):
                portAvailable = True
        if (portAvailable == False):
            self.writeMessage("Port No Longer Available")
            return

        try:
            self._save_settings() # Save the settings in case the command fails
        except:
            pass

        self.writeMessage("Resetting ESP32\n")

        # ---- The pySerial method -----

        self.disable_interface(True)

        sleep(0.1)

        try:
            ser = serial.Serial()
            ser.port = self.port
            ser.setDTR(False) # DTR High
            ser.setRTS(False) # RTS High
            with ser as s:
                s.setRTS(True) # RTS Low - before DTR
                s.setDTR(True) # DTR Low - after RTS
                sleep(1.0)
                self.writeMessage("Waiting for reset to complete")
                sleep(1.0)
                self.writeMessage("Waiting for reset to complete")
                sleep(1.0)
                self.writeMessage("Waiting for reset to complete")
                sleep(1.0)
                self.writeMessage("Waiting for reset to complete\n")
                sleep(1.0)
        except:
            self.writeMessage("Could not open serial port\n")
            self.disable_interface(False)
            return

        self.writeMessage("Reset complete...")
        self.disable_interface(False)

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