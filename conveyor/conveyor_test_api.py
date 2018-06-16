from unittest.mock import patch, MagicMock
from unittest import TestCase
from time import sleep


class GPIOMock:
    BOARD = 1
    OUT = 1
    IN = 1
    BCM = 1
    HIGH = 1
    LOW = 1

    @staticmethod
    def setmode(a):
        print(a)

    @staticmethod
    def setup(a, b):
        print(a)

    @staticmethod
    def output(a, b):
        print(a)

    @staticmethod
    def input(a):
        print(a)

    @staticmethod
    def cleanup():
        print("a")

    @staticmethod
    def setmode(a):
        print(a)

    @staticmethod
    def setwarnings(flag):
        print("False")


MockRPi = MagicMock()
MockRPi.GPIO = GPIOMock
modules = {
    "RPi": MockRPi,
    "RPi.GPIO": MockRPi.GPIO,
}

with patch.dict("sys.modules", modules):
    import RPi.GPIO as GPIO

    from conveyor.conveyor_hardware_api import Lock, Conveyor

    class TestLock(TestCase):

        def setUp(self):
            self.lock = Lock('ZYL.1', 4, 18)

        def test_lock_name(self):
            self.assertEqual(self.lock.name, "ZYL.1".lower(), "Lock name is incorrect")

        def test_lock_in_port(self):
            self.assertEqual(self.lock.in_port, 4, "Lock in_port is incorrect")

        def test_lock_out_port(self):
            self.assertEqual(self.lock.out_port, 18, "Lock out_port is incorrect")

        def test_lock_state(self):
            self.assertEqual(self.lock.state, "CLOSED", "Lock state is incorrect")

        def test_lock_is_busy(self):
            self.assertEqual(self.lock.is_busy, False, "Lock is_busy value is incorrect")

        def test_open_lock(self):
            self.lock.open()
            self.assertEqual(self.lock.state, "OPEN", "Lock state is incorrect")

        def test_close_lock(self):
            self.lock.open()
            self.assertEqual(self.lock.state, "OPEN", "Lock state is incorrect")
            self.lock.close()
            self.assertEqual(self.lock.state, "CLOSED", "Lock state is incorrect")

        def test_pass_one_lock(self):
            self.lock.pass_one()
            self.assertEqual(self.lock.state, "CLOSED", "Lock state is incorrect")


    class TestConveyor(TestCase):

        def setUp(self):
            self.cv = Conveyor(
                [Lock("ZYL.1", 4, 18), Lock("ZYL.2", 17, 23), Lock("ZYL.3", 27, 24), Lock("ZYL.4", 22, 25)]
            )

        def test_conveyor_state(self):
            self.assertEqual(self.cv.conveyor_state, "ENABLED", "Conveyor state is incorrect")

        def test_conveyor_e_stop(self):
            self.cv.conveyor_e_stop()
            self.assertEqual(self.cv.conveyor_state, "E_STOP", "Conveyor state is incorrect")

        def test_conveyor_lock_state(self):
            expected_lock_state = {
                "lock_id": 1,
                "lock_name": "zyl.1",
                "is_busy": False,
                "state": "CLOSED",
            }
            self.assertEqual(self.cv.lock_state(lock_id=1), expected_lock_state, "Lock state is incorrect")
            self.assertEqual(self.cv.lock_state(lock_name="zyl.1"), expected_lock_state, "Lock state is incorrect")

        def test_conveyor_lock_release_car(self):
            self.cv.lock_release_car(lock_id=1)
            expected_lock_state = {
                "lock_id": 1,
                "lock_name": "zyl.1",
                "is_busy": False,
                "state": "CLOSED",
            }
            self.assertEqual(self.cv.lock_state(lock_id=1), expected_lock_state, "Conveyor lock state is incorrect")
            self.cv.lock_release_car(lock_name="zyl.1")
            self.assertEqual(self.cv.lock_state(lock_name="zyl.1"), expected_lock_state,
                             "Conveyor lock state is incorrect")

        def test_conveyor_lock_open(self):
            self.cv.lock_open(lock_id=1)
            expected_lock_state = {
                "lock_id": 1,
                "lock_name": "zyl.1",
                "is_busy": False,
                "state": "OPEN",
            }
            self.assertEqual(self.cv.lock_state(lock_id=1), expected_lock_state, "Conveyor lock state is incorrect")
            self.cv.lock_close(lock_id=1)
            expected_lock_state["state"] = "CLOSED"
            self.assertEqual(self.cv.lock_state(lock_id=1), expected_lock_state, "Conveyor lock state is incorrect")
            self.cv.lock_open(lock_name="zyl.1")
            expected_lock_state["state"] = "OPEN"
            self.assertEqual(self.cv.lock_state(lock_name="zyl.1"), expected_lock_state,
                             "Conveyor lock state is incorrect")

        def test_conveyor_lock_close(self):
            expected_lock_state = {
                "lock_id": 1,
                "lock_name": "zyl.1",
                "is_busy": False,
                "state": "OPEN",
            }
            self.cv.lock_open(lock_id=1)
            self.assertEqual(self.cv.lock_state(lock_id=1), expected_lock_state, "Conveyor lock state is incorrect")
            self.cv.lock_close(lock_id=1)
            expected_lock_state["state"] = "CLOSED"
            self.assertEqual(self.cv.lock_state(lock_id=1), expected_lock_state, "Conveyor lock state is incorrect")
            self.cv.lock_open(lock_id=1)
            expected_lock_state["state"] = "OPEN"
            self.assertEqual(self.cv.lock_state(lock_id=1), expected_lock_state, "Conveyor lock state is incorrect")
            self.cv.lock_close(lock_name="zyl.1")
            expected_lock_state["state"] = "CLOSED"
            self.assertEqual(self.cv.lock_state(lock_name="zyl.1"), expected_lock_state,
                             "Conveyor lock state is incorrect")

        def test_conveyor_locks_state(self):
            expected_locks_state = [
                {
                    "lock_id": 1,
                    "lock_name": "zyl.1",
                    "is_busy": False,
                    "state": "CLOSED",
                },
                {
                    "lock_id": 2,
                    "lock_name": "zyl.2",
                    "is_busy": False,
                    "state": "CLOSED",
                },
                {
                    "lock_id": 3,
                    "lock_name": "zyl.3",
                    "is_busy": False,
                    "state": "CLOSED",
                },
                {
                    "lock_id": 4,
                    "lock_name": "zyl.4",
                    "is_busy": False,
                    "state": "CLOSED",
                },
            ]
            self.assertEqual(self.cv.locks_state(), expected_locks_state, "Locks states are incorrect")
