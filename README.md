SparkFun RTK Firmware Uploader
========================================

![RTK Uploader](images/RTK_Uploader_Windows_1.png)

The RTK Firmware Uploader is a simple, easy to use method for updating the firmware on SparkFun RTK products. Available on all major platforms, as well as a Python package, the Uploader simplifies working with SparkFun RTK products. 

If you need to install the application, see the [Installation Section](#installation) of this page.

## Notes:

From v1.6.0, this GUI does not contain a copy of ```esptool.py```. Instead the latest ```esptool.py``` is installed and used by the build workflow. If you want to run ```RTK_Firmware_Uploader.py``` locally, you will need to ```pip install esptool``` first.

# Using the RTK Firmware Uploader
  
## Upload Firmware
  
* Attach the RTK product over USB
* Click the ```COM Port``` combo box and select the correct COM port from the dropdown menu

![Select COM Port](images/RTK_Uploader_Windows_2.png)

* Adjust the Baud Rate if desired
* Click ```Browse``` and select the firmware file you'd like to upload (the filename should end in *.bin*)
  * You can find the firmware in the [SparkFun_RTK_Firmware_Binaries repo on GitHub](https://github.com/sparkfun/SparkFun_RTK_Firmware_Binaries)
  * The older versions of the firmware are in a [separate folder](https://github.com/sparkfun/SparkFun_RTK_Firmware_Binaries/tree/main/PreviousVersions)
  * If you have one of the earliest RTK Surveyors with 4MB flash, please select **v1_12**

![Select Firmware](images/RTK_Uploader_Windows_4.png)

* Click the  ```Upload Firmware``` button to update the firmware

The selected firmware is then uploaded to the connected SparkFun RTK product. Upload information and progress are displayed in the output portion of the interface. 

![Firmware Upload](images/RTK_Uploader_Windows.gif)

## Reset ESP32

Clicking the ```Reset ESP32``` button will reset the ESP32 processor. This is helpful when the firmware update succeeds but does not reset the RTK correctly.
If your RTK 'freezes' after the update, pressing ```Reset ESP32``` will get it going again.

![Reset ESP32](images/RTK_Uploader_Windows_3.png)


## Installation

Installation binaries are available for all major platforms (macOS, Window, and Linux) on the release page of the RTK Uploader GitHub repository:

[**RTK Uploader Release Page**](https://github.com/sparkfun/SparkFun_RTK_Firmware_Uploader/releases)

Click the arrow next to **Assets** if required to see the installers:

![Releases Assets](images/RTK_Uploader_Assets.png)


### Windows
* Download the [github release](https://github.com/sparkfun/SparkFun_RTK_Firmware_Uploader/releases) zip file - *RTKUploader.win.zip*
* Unzip the release file - *RTKUploader.zip*
* This results in the application executable, *RTKUploader.exe*
* Double-click *RTKUploader.exe* to start the application

### macOS
* Download the [github release](https://github.com/sparkfun/SparkFun_RTK_Firmware_Uploader/releases) file - *RTKUploader.dmg*
* Double click the *RTKUploader.dmg* file to mount the disk image. 
* A Finder window, with the contents of the file will open
* Install the *RTKUploader.app* by dragging it on the *Applications* in the RTKUploader Finder Window, or copying the file to a desired location.
* Once complete, unmount the RTKUploader disk image by right-clicking on the mounted disk in Finder and ejecting it.
* You may need to install drivers for the CH340 USB interface chip. Full instructions can be found in our [CH340 Tutorial](https://learn.sparkfun.com/tutorials/how-to-install-ch340-drivers/all#mac-osx)

To launch the RTK Uploader application:
* Double-click RTKUploader.app to launch the application
* The RTKUploader.app isn't signed, so macOS won't run the application, and will display a warning dialog. Dismiss this dialog.
* To approve app execution bring up the macOS *System Preferences* and navigate to: *Security & Privacy > General*. 
* On this page, select the *Open Anyway* button to launch the RTKUploader application.
* Once selected, macOS will present one last dialog. Select *Open* to run the application. The RTKUploader will now start.

### Linux
* Download the [github release](https://github.com/sparkfun/SparkFun_RTK_Firmware_Uploader/releases) file - *RTKUploader.linux.gz*
* Un-gzip the file, either by double-clicking in on the desktop, or using the `gunzip` command in a terminal window. This results in the file *RTKUploader* 
* To run the application, the file must have *execute* permission. This is performed by selecting *Properties* from the file right-click menu, and then selecting permissions. You can also change permissions using the `chmod` command in a terminal window.
* Once the application has execute permission, you can start the application a terminal window. Change directory's to the application location and issue `./RTKUploader`
* You may need to install drivers for the CH340 USB interface chip. Full instructions can be found in our [CH340 Tutorial](https://learn.sparkfun.com/tutorials/how-to-install-ch340-drivers/all#linux)


### Python Package
The RTK Firmware Uploader is also provided as an installable Python package. This is advantageous for platforms that lack a pre-compiled application. 

To install the Python package:
* Download the package file - *python-install-package.zip*
* Unzip the github release file. This results in the installable Python package file - *RTK_Firmware_Uploader-1.4.0.tar.gz* (note - the version number might vary)

At a command line - issue the package install command:

* `pip install RTK_Firmware_Uploader-1.4.0.tar.gz`
* Once installed, you can start the RTK Uploader App by issuing the command `./RTK_Formware_Upload` at the command line. (To see the command, you might need to start a new terminal, or issue a command like `rehash` depending on your platform/shell)

Notes:
* A path might be needed to specify the install file location.
* Depending on your platform, this command might need to be run as admin/root.
* Depending on your system, you might need to use the command `pip3`

### Raspberry Pi
We've tested the Uploader on both 32-bit and 64-bit Raspberry Pi Debian. You will need to use the **Python Package** to install it.

Notes:
* On 32-bit Raspberry Pi, with both Python 2 and Python 3 installed, use `sudo pip3 install RTK_Firmware_Uploader-1.4.0.tar.gz`
  * By default, the executable will be placed in `/usr/local/bin`
* On 64-bit Raspberry Pi, use `sudo pip install RTK_Firmware_Uploader-1.4.0.tar.gz`
* The `sudo` is required to let `setup.py` install `python3-pyqt5` and `python3-pyqt5.qtserialport` using `sudo apt-get install`

![Raspberry Pi 64-bit : Install](images/RPi_install.png)

![Raspberry Pi 64-bit : Install](images/RPi_Uploader.png)

