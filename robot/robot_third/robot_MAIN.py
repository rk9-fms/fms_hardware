from robot.robot_third.robot_DB import *
from robot.robot_third.robot_func import Robot


class WriteStream(object):
    def __init__(self, queue):
        self.queue = queue

    def write(self, text):
        self.queue.put(text)

    def flush(self):
        pass


def main():
    r1_table = DBMaster("petyx.db")
    r1_table.add_list('stuff.txt')

    robot_1 = Robot(r1_table)
    robot_1.go_perform('stuff')


if __name__ == '__main__':
    main()
    import time
    time.sleep(1000)

