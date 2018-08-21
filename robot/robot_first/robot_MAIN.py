import serial
import time
import os, sys, setup
import threading
from queue import *
from robot_func import ControlMethods
from DB_work import DB_Master


class WriteStream(object):
    def __init__(self, queue):
        self.queue = queue

    def write(self, text):
        self.queue.put(text)

    def flush(self):
        pass


def main():
    # Create Queue and redirect sys.stdout to this queue
    my_queue = Queue()

    suka = ControlMethods(my_queue)
    print(suka.get_position(suka.ser))

    th1 = threading.Thread(target=suka.get_position(suka.ser))
    th1.daemon = True
    th1.start()


if __name__ == '__main__':
    main()