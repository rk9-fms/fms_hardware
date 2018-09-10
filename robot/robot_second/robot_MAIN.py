import serial
import time
import os, sys, setup
import threading
from queue import *
from robot_func import Robot
from robot_func import DBMaster


class WriteStream(object):
    def __init__(self, queue):
        self.queue = queue

    def write(self, text):
        self.queue.put(text)

    def flush(self):
        pass

def main():
    r1_table = DBMaster()
    r1_table.add_list('stuff.txt')

    robot_1 = Robot(r1_table)
    robot_1.go_perform('stuff')


if __name__ == '__main__':
    main()

