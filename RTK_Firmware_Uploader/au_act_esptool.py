from .au_action import AxAction, AxJob
from .esptool import main as esptool_main
from .esptool import ESPLoader
from .esptool import UnsupportedCommandError
from .esptool import NotSupportedError
from .esptool import NotImplementedInROMError
from .esptool import FatalError


#--------------------------------------------------------------------------------------
# action testing
class AUxEsptoolUploadFirmware(AxAction):

    ACTION_ID = "esptool-upload-firmware"
    NAME = "ESP32 Firmware Upload"

    def __init__(self) -> None:
        super().__init__(self.ACTION_ID, self.NAME)

    def run_job(self, job:AxJob):

        try:
            esptool_main(job.command)

        except Exception:
            return 1

        return 0