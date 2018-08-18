from time import sleep

import RPi.GPIO as GPIO


class Conveyor:
    def __init__(self, locks):
        self.locks = locks

    def lock_release_car(self, lock_id):
        self.locks[lock_id].pass_one()

    def lock_open(self, lock_id):
        self.locks[lock_id].open()

    def lock_close(self, lock_id):
        self.locks[lock_id].close()

    def locks_state(self):
        return {lock.name: {'is_busy': lock.is_busy, 'state': lock.state} for lock in self.locks}

    def lock_state(self, lock_id):
        lock = self.locks[lock_id]
        return {lock.name: {'is_busy': lock.is_busy, 'state': lock.state}}


class Lock:
    def __init__(self, name, in_port, out_port):
        """
        first_lock: in - 4, out - 18
        second_lock: in - 17, out - 23
        third_lock: in - 27, out - 24
        fourth_lock: in - 22, out - 25
        """
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        self._name = name
        self._in_port = in_port
        self._out_port = out_port
        GPIO.setup(self._in_port, GPIO.IN)
        GPIO.setup(self._out_port, GPIO.OUT)
        GPIO.output(self._out_port, GPIO.LOW)
        self._state = 'closed'

    @property
    def name(self):
        return self._name.upper()

    @property
    def in_port(self):
        return self._in_port

    @property
    def out_port(self):
        return self._out_port

    @property
    def state(self):
        return self._state.upper()

    @property
    def is_busy(self):
        if GPIO.input(self.in_port):
            return 'YES'
        else:
            return 'NO'

    def open(self):
        if self._state == 'open':
            return
        GPIO.output(self._out_port, GPIO.HIGH)
        self._state = 'open'

    def close(self):
        if self._state == 'close':
            return
        GPIO.output(self._out_port, GPIO.LOW)
        self._state = 'closed'

    def pass_one(self):
        if self._state == 'open':
            return
        GPIO.output(self._out_port, GPIO.HIGH)
        sleep(0.8)
        GPIO.output(self._out_port, GPIO.LOW)


class ConveyorError(Exception):
    def __init__(self, msg):
        GPIO.setup(7, GPIO.OUT)
        GPIO.output(7, GPIO.LOW)
        self.msg = msg

    def __str__(self):
        GPIO.output(7, GPIO.HIGH)
        return repr(self.msg)
