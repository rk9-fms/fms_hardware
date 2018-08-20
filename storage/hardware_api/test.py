import time
import types
import random
from io import BytesIO

from mock import patch

from storage.hardware_api.storage_api import Storage, StorageHWAPIBySerial, StorageHWStatus

print('Lets test some basics')
print('We will mock serial connection by io.BytesIO, run simple method Storage.move_to_idle_position,')
print('and then we will check commands that all this complicated things sends to ASRS')

time.sleep(0.5)  # little beautifying for logs output
with patch('serial.Serial') as patched_serial:
    patched_serial.return_value = BytesIO()
    st_hw_api = StorageHWAPIBySerial()

    def get_status(self):
        status = random.choice([StorageHWStatus.IDLE, StorageHWStatus.BUSY])
        self.logger.debug(f'Current status: {status!r}')
        return status

    # patching the bound method
    st_hw_api.get_status = types.MethodType(get_status, st_hw_api)

    st = Storage(st_hw_api)

st.move_to_idle_position()
st.move_to_idle_position()

print(st.status.value)
st.return_to_home()
st.pick_from_asrs(1, 2, 3)
st.return_to_home()

st.stop()

time.sleep(0.5)  # little beautifying for logs output
print('Output commands are:')
for command in st_hw_api.ser.getvalue().split(b'\n\r'):
    if command:
        print(command + b'\n\r')
