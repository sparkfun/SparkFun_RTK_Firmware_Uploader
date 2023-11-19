from .au_action import AxAction, AxJob

import esptool # pip install esptool

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