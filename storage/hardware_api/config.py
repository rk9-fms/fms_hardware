import serial
import platform

if platform.system() == 'Darwin':
    # on mac: https://plugable.com/2011/07/12/installing-a-usb-serial-adapter-on-mac-os-x/
    serial_port = '/dev/cu.usbserial'
else:
    # for raspberry pi
    serial_port = 'ttyUSB0'

serial_kwargs = dict(
    port=serial_port,
    baudrate=4800,
    bytesize=serial.SEVENBITS,
    parity=serial.PARITY_EVEN,
    stopbits=serial.STOPBITS_ONE,
    timeout=0
)
