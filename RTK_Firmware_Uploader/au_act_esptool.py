from .au_action import AxAction, AxJob

import esptool # pip install esptool

from platform import system
import os.path

if (system() == "Darwin"): # Fix for MacOS pyinstaller windowed executable

    head_tail = os.path.split(os.path.dirname(__file__))
    if (head_tail[1] == "RTK_Firmware_Uploader"): # Check if this is the Uploader executable
        base_path = os.path.abspath(head_tail[0])
        STUBS_DIR = os.path.join(base_path, "esptool", "targets", "stub_flasher")
        # Python hackiness: change the path to stub json files in the context of the esptool
        # module, so it edits the esptool's global variables
        exec(
            "loader.STUBS_DIR = '{}'".format(STUBS_DIR),
            esptool.__dict__,
            esptool.__dict__,
        )

#--------------------------------------------------------------------------------------
# action testing
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