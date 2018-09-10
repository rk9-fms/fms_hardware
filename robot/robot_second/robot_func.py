import serial
import time
from threading import Thread
import setup
from queue import Queue
import enum
from peewee import *
import time
import os.path as path


db  = SqliteDatabase('petyx.db')

class RobotState(enum.Enum):
    BUSY = 1
    FREE = 2
    STOP = 3
    ERROR = 4


class OpList(Model):
    seq_name = CharField()
    sequence = BlobField()

    class Meta:
        database = db


class DBMaster:
    def __init__(self):
        db.connect()
        db.create_tables([OpList])

    # start to fill table with operation lists
    def add_list(self, filename):
        fname = path.basename(filename[:-4])
        try:
            OpList.select().where(OpList.seq_name == fname).get()
            return
        except Exception:
            pass

        with open(filename, 'r') as some_list:
            seq = some_list.read()
        obj = OpList.create(seq_name=fname, sequence=seq)
        obj.save()

    # return list of operations to complete
    def get_operation(self, seq_name):
        try:
            query = OpList.select().where(OpList.seq_name == seq_name)
            for i in query:
                return i.sequence
                #return bytes(i.sequence, encoding='utf-8')
        except Exception:
            print("No such operation")
            pass


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

    # get actual position
    def get_position(self):
        while True:
            try:
                self.ser.write(b'1;1;PPOSF\r')
                position = ''
                while i != '\r':
                    i = self.ser.read(1).decode('utf-8')
                    position = position + i
                return position
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
        seq = table.get_operation(seq_name)
        for i in seq:
            command = i.split('\n')
            if command[0].isdigit():
                command.pop(0)
            print(i)
            self.ser.write(bytes(' '.join(command)))

    def wait_to_start(self, home_position):
        start_wait = time.time()
        if time.time() - start_wait > self.wait_timeout and self.get_position() == home_position:
            raise RuntimeError(f"Some problems.")
        else:
            pass

    # waiting till current position will be equal to home position
    def wait_for_complete(self, home_position):
        time.sleep(0.5)
        start_wait = time.time()
        while time.time() - start_wait < self.wait_timeout:
            if self.get_position() == home_position:
                self.status = RobotState.FREE
                return
            elif self.get_position() != home_position:
                self.status = RobotState.BUSY
                time.sleep(0.5)
            else:
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