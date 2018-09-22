from time import sleep
from enum import Enum
from collections import namedtuple

import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)


class LockState(Enum):
    CLOSED = 0
    OPEN = 1


class ConveyorState(Enum):
    E_STOP = 0
    ENABLED = 1


class Conveyor:
    def __init__(self, locks):
        self.locks = locks
        for lock_id, lock in enumerate(self.locks, 1):
            lock.id = lock_id
        self.state = ConveyorState.ENABLED
        GPIO.setup(7, GPIO.OUT)
        GPIO.output(7, GPIO.LOW)
        self._lock_with_state = namedtuple('lock_with_state', ('lock', 'state'))

    def conveyor_e_stop(self):
        GPIO.output(7, GPIO.HIGH)
        self.state = ConveyorState.E_STOP

    def _find_lock_by_id(self, lock_id):
        for lock in self.locks:
            if lock.id == lock_id:
                return lock

    def _find_lock_by_name(self, lock_name):
        for lock in self.locks:
            if lock.name == lock_name.lower():
                return lock

    def _get_lock_by_id_or_name(self, searching_parameter):
        if isinstance(searching_parameter, int):
            return self._find_lock_by_id(searching_parameter)
        elif isinstance(searching_parameter, str):
            return self._find_lock_by_name(searching_parameter)

    def lock_pass_one(self, lock_identifier):
        self._get_lock_by_id_or_name(lock_identifier).pass_one()

    def lock_open(self, lock_identifier):
        self._get_lock_by_id_or_name(lock_identifier).open()

    def lock_close(self, lock_identifier):
        self._get_lock_by_id_or_name(lock_identifier).close()

    def locks_state(self):
        return [
            self._lock_with_state(lock, lock.state)
            for lock in self.locks
        ]

    def lock_state(self, lock_identifier):
        lock = self._get_lock_by_id_or_name(lock_identifier)
        return self._lock_with_state(lock, lock.state)


class Lock:
    PASS_ONE_AWAIT_TIME = 0.8

    def __init__(self, name, in_port, out_port):
        self.name = name.lower()
        self.in_port = in_port
        self.out_port = out_port
        GPIO.setup(self.in_port, GPIO.IN)
        GPIO.setup(self.out_port, GPIO.OUT)
        GPIO.output(self.out_port, GPIO.LOW)
        self.state = LockState.CLOSED

    @property
    def is_busy(self):
        if GPIO.input(self.in_port):
            return True
        else:
            return False

    def open(self):
        if self.state == LockState.OPEN:
            return
        GPIO.output(self.out_port, GPIO.HIGH)
        self.state = LockState.OPEN

    def close(self):
        if self.state == LockState.CLOSED:
            return
        GPIO.output(self.out_port, GPIO.LOW)
        self.state = LockState.CLOSED

    def pass_one(self):
        if self.state == LockState.OPEN:
            return
        GPIO.output(self.out_port, GPIO.HIGH)
        self.state = LockState.OPEN
        sleep(self.PASS_ONE_AWAIT_TIME)
        GPIO.output(self.out_port, GPIO.LOW)
        self.state = LockState.CLOSED


if __name__ == "__main__":
    cv = Conveyor([Lock("ZYL.1", 4, 18), Lock("ZYL.2", 17, 23), Lock("ZYL.3", 27, 24), Lock("ZYL.4", 22, 25)])
