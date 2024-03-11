from .au_action import AxAction, AxJob

import esptool # pip install esptool

# # When I couldn't get the windowed executable to work on MacOS, I suspected that esptool still could not
# # find the stub_flasher json files. Turns out it was actually the baud rate that was the issue...
# # 921600 fails on my Mac Mini, but 460800 works fine...
# # I'm leaving the following commented code for future reference. I really like the exec trick!
# 
# from platform import system
# import os.path
# import sys
# if (system() == "Darwin") and hasattr(sys, '_MEIPASS'): # Fix for MacOS pyinstaller windowed executable
#     head_tail = os.path.split(os.path.dirname(__file__))
#     base_path = os.path.abspath(head_tail[0])
#     STUBS_DIR = os.path.join(base_path, "esptool", "targets", "stub_flasher")
#     # Python hackiness: change the path to stub json files in the context of the esptool
#     # module, so it edits the esptool's global variables
#     exec(
#         "loader.STUBS_DIR = '{}'".format(STUBS_DIR),
#         esptool.__dict__,
#         esptool.__dict__,
#         )

#--------------------------------------------------------------------------------------
# action testing
class AUxEsptoolReadMAC(AxAction):

    ACTION_ID = "esptool-read-mac"
    NAME = "ESP32 Read MAC"

    def __init__(self) -> None:
        super().__init__(self.ACTION_ID, self.NAME)

    def run_job(self, job:AxJob):

        try:
            esptool.main(job.command)

        except Exception:
            return 1

        return 0

class AUxEsptoolEraseFlash(AxAction):

    ACTION_ID = "esptool-erase-flash"
    NAME = "ESP32 Flash Erase"

    def __init__(self) -> None:
        super().__init__(self.ACTION_ID, self.NAME)

    def run_job(self, job:AxJob):

        try:
            esptool.main(job.command)

        except Exception:
            return 1

        return 0

class AUxEsptoolDetectFlash(AxAction):

    ACTION_ID = "esptool-detect-flash"
    NAME = "ESP32 Flash Size Detection"

    def __init__(self) -> None:
        super().__init__(self.ACTION_ID, self.NAME)

    def run_job(self, job:AxJob):

        try:
            esptool.main(job.command)

        except Exception:
            return 1

        return 0

class AUxEsptoolUploadFirmware(AxAction):

    ACTION_ID = "esptool-upload-firmware"
    NAME = "ESP32 Firmware Upload"

    def __init__(self) -> None:
        super().__init__(self.ACTION_ID, self.NAME)

    def run_job(self, job:AxJob):

        try:
            esptool.main(job.command)

        except Exception:
            return 1

        return 0

class AUxEsptoolResetESP32(AxAction):

    ACTION_ID = "esptool-reset-esp32"
    NAME = "ESP32 Reset"

    def __init__(self) -> None:
        super().__init__(self.ACTION_ID, self.NAME)

    def run_job(self, job:AxJob):

        try:
            esptool.main(job.command)

        except Exception:
            return 1

        return 0