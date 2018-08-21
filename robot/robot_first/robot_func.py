import serial
import time
import os, sys, setup


class ControlMethods:

    def __init__(self, queue):
        self.ser = serial.Serial(setup.port, baudrate=9600, bytesize=serial.EIGHTBITS,
                                 parity=serial.PARITY_EVEN, stopbits=serial.STOPBITS_ONE, timeout=2)  # open serial port

        self.queue = queue
        self.ser.flushInput()
        self.ser.flushOutput()

    def get_position(self, ser):  #get actual position
        while True:
            ser.write(b'1;1;PPOSF\r')
            position = ''
            while i != '\r':
                i = ser.read(1).decode('utf-8')
                position = position + i
            return position

    def set_position(self, x, y, z, a, b): #set position with string
        self.ser.write(b'1;1;CNTLON\r')
        self.ser.write(b'1;1;SRVON\r')
        time.sleep(2)
        b_str = 'MP {},{},{},{},{}'.format(x, y, z, a, b).encode()
        self.ser.write(b_str)

    def move_x(self):
        self.ser. write(b'DS 1,0,0\r')

    def move_y(self):
        self.ser.write(b'DS 0,1,0\r')

    def move_z(self):
        self.ser.write(b'DS 0,0,1\r')

