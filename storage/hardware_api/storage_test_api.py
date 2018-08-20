import time
import types
from io import BytesIO

from unittest.mock import patch, MagicMock


class GPIOMock:
    BOARD = 'BOARD'
    OUT = 'OUT'
    IN = 'IN'
    BCM = 'BCM'
    HIGH = 'HIGH'
    LOW = 'LOW'

    def setmode(self, mode):
        print(f'setmode {mode}')

    def setup(self, port, mode):
        print(f'setup {port} {mode}')

    def output(self, port, mode):
        print(f'output {port} {mode}')

    def setwarnings(self, flag):
        print(f'setwarnings {flag}')


MockRPi = MagicMock()
MockRPi.GPIO = GPIOMock()
modules = {
    "RPi": MockRPi,
    "RPi.GPIO": MockRPi.GPIO
}

with patch.dict("sys.modules", modules), patch('serial.Serial') as patched_serial:
    from storage.hardware_api.storage_api import StorageHWAPIBySerial, StorageHWStatus, Storage

    patched_serial.return_value = BytesIO()
    test_st_hw_api = StorageHWAPIBySerial()

    test_st_hw_api._status_call_count = 0

    def get_status(self):
        if self._status_call_count == 3:
            status = StorageHWStatus.IDLE
            self._status_call_count = 0
        else:
            status = StorageHWStatus.BUSY
            self._status_call_count += 1
        self.logger.debug(f'Current status: {status!r}, {self._status_call_count}')
        return status

    # patching the bound method
    test_st_hw_api.get_status = types.MethodType(get_status, test_st_hw_api)
    test_st = Storage(test_st_hw_api)
