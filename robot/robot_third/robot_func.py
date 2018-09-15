import serial
from threading import Thread
import setup
from queue import Queue
import enum
import time


class RobotState(enum.Enum):
    BUSY = 1
    FREE = 2
    STOP = 3
    ERROR = 4


class Robot:
    wait_timeout = 30
    def __init__(self, table):
        self.ser = serial.Serial(setup.port, baudrate=9600, bytesize=serial.EIGHTBITS,
                                 parity=serial.PARITY_EVEN, stopbits=serial.STOPBITS_ONE, timeout=2)  # open serial port
        self.status = RobotState.FREE
        self.entity_table = table
        self.ser.flushInput()
        self.ser.flushOutput()

        self.queue = Queue()
        self.Executor_thread = Thread(target=self.run)
        self.Executor_thread.daemon = True
        self.Executor_thread.start()

    # convert byte string of returned value to proper form
    #EXample "coord = b'QoKX;72.46;Y;-0.02;Z;552.14;A;2.02;B;139.54;;268435462,0;50;0.00;00000000\r'"
    #TO {'X': 72, 'Y': 0, 'Z': 552, 'A': 2, 'B': 139}
    @staticmethod
    def convert(coord):
        line = coord.decode('utf-8')
        i = 0
        coords = ['X', 'Y', 'Z', 'A', 'B']
        dick = []
        my_dick = {}
        for letter in line:
            i += 1
            if letter == 'X':
                temp = line[i - 1:].split(';')
                count = 0
                for x in temp:
                    if count % 2 == 1:
                        dick.append(x)
                    count += 1
                my_dick = dict(zip(coords, dick))

        for i in my_dick:
            my_dick[i] = int(float(my_dick[i]))
        return my_dick


    # method to compare positions. Used to comprehension of robot active status
    @staticmethod
    def compare_position(pos1, pos2):
        result = 'equal'
        for pos1_coords, pos2_coords in zip(pos1.values(), pos2.values()):
            if pos1_coords != pos2_coords:
                result = 'different'
        return result

    # get actual position
    def get_position(self):
        while True:
            try:
                self.ser.write(b'1;1;PPOSF\r')
                position = ''
                while i != '\r':
                    i = self.ser.read(1).decode('utf-8')
                    position = position + i
                return self.convert(position)
            except Exception:
                pass

    # set position with string
    def set_position(self, x, y, z, a, b):
        self.ser.write(b'1;1;CNTLON\r')
        self.ser.write(b'1;1;SRVON\r')
        time.sleep(2)
        b_str = 'MP {},{},{},{},{}'.format(x, y, z, a, b).encode()
        self.ser.write(b_str)

    #sends text of program to robot
    def send_things(self, table, seq_name):
        self.ser.write(b'1;1;CNTLON\r')
        self.ser.write(b'1;1;SRVON\r')
        time.sleep(2)
        seq = table.get_operation(seq_name)
        seq = seq.decode('utf-8').replace('\n', "\r\n")
        self.ser.write(seq)

    # Wait till robot start to move
    def wait_to_start(self, home_position):
        start_wait = time.time()
        if time.time() - start_wait > self.wait_timeout\
                and self.compare_position(self.get_position(), home_position) == 'equal':
            raise RuntimeError(f"Some problems.")
        else:
            pass

    # waiting till current position will be equal to home position
    def wait_for_complete(self, home_position):
        time.sleep(0.5)
        start_wait = time.time()
        while time.time() - start_wait < self.wait_timeout:
            if self.compare_position(self.get_position(), home_position) == 'equal':
                self.status = RobotState.FREE
                return
            elif self.compare_position(self.get_position(), home_position) == 'different':
                self.status = RobotState.BUSY
                time.sleep(0.5)
            else:
                self.status = RobotState.ERROR
                raise RuntimeError(f"Some problems.")
        raise TimeoutError("timeout has been reached")

    # function that puts names of required programs to queue
    def go_perform(self, seq_name):
        self.queue.put(seq_name)
        print("program {} started".format(seq_name))

    def run(self):
        while True:
            try:
                if self.queue.empty():
                    pass
                task = self.queue.get()
                table = self.entity_table
                home_position = self.get_position()
                time.sleep(0.5)
                self.send_things(table, task)
                self.wait_to_start(home_position)
                self.wait_for_complete(home_position)
            except Exception:
                print('error37')
                break


    """ seq = table.get_operation('jula(SW)')
    for i in seq:
        command = i.split(' ')
        if command[0].isdigit():
            command.pop(0)
        print(bytes(' '.join(command)))"""