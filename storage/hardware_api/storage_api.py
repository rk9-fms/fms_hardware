import time
import enum
import serial
import logging
import threading
from queue import Queue
from collections import namedtuple
from abc import ABC, abstractmethod

import RPi.GPIO as GPIO

from storage.hardware_api import config

# TODO: create state like LOADED_AT_PICK_SIDE LOADED_AT_PLACE_SIDE, methods and asserts of this states
# TODO: think about executor queue backup
# TODO: think about queued tasks removing, or smth like this
# TODO: think about executor timeout exception
# TODO: improve logging

# configuring GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# configuring logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

fh = logging.FileHandler('ASRS.log')
fh.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s.%(funcName)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)


class StorageLocation(enum.Enum):
    HOME = 0
    HOME_CENTER = 1
    ASRS = 2
    PRE_CONVEYOR = 3
    CONVEYOR = 4
    ASRS_PICK = 5
    ASRS_PLACE = 6


class StorageHWStatus(enum.Enum):
    BUSY = 1
    IDLE = 2
    E_STOP = 3
    ERROR = 4  # does it exists?


class StorageStatus(enum.Enum):
    NEED_TO_CALIBRATE = 0
    IDLE = 1
    ERROR = 2
    BUSY = 3


class StorageHWAPI(ABC):
    @abstractmethod
    def home_move(self):
        ...

    @abstractmethod
    def home_center_move(self):
        ...

    @abstractmethod
    def asrs_place(self, side, row, column):
        ...

    @abstractmethod
    def asrs_pick(self, side, row, column):
        ...

    @abstractmethod
    def asrs_center_move(self):
        ...

    @abstractmethod
    def pre_conv_place(self):
        ...

    @abstractmethod
    def pre_conv_pick(self):
        ...

    @abstractmethod
    def conv_place(self):
        ...

    @abstractmethod
    def conv_pick(self):
        ...

    @abstractmethod
    def get_status(self):
        ...

    @property
    def status(self):
        return self.get_status()


class StorageHWAPIBySerial(StorageHWAPI):
    """
    Class that provides hardware API to ASRS over Serial
    """
    serial_config = config.serial_kwargs
    ASRS = 'ASRS'
    ASRS_CENTER = 'ASRS_CENTER'
    HOME = 'HOME'
    HOME_CENTER = 'HOME_CENTER'
    CONVEYOR = 'CONV'
    PRE_CONVEYOR = 'PRE_CONV'
    COMMAND_ENCODING = '1251'
    COMMAND_SEPARATOR = '\n\r'
    GPIO_STATUS_PORTS = [4, 2, 0]

    def __init__(self):
        self.logger = logging.getLogger(f'{type(self).__name__}')
        self.logger.debug('Opening serial connection with ASRS')
        self.ser = serial.Serial(**self.serial_config)
        [GPIO.setup(port, GPIO.IN) for port in self.GPIO_STATUS_PORTS]

    def __repr__(self):
        return f'{type(self).__name__}()'

    def __del__(self):
        self.ser.close()

    def _prepare_command(self, command: str):
        """ Close the ASRS command with separator """
        command = f'{command}{self.COMMAND_SEPARATOR}'.encode(self.COMMAND_ENCODING)
        return command

    def _prepare_and_send_command(self, command):
        """ Send command to ASRS """
        self.logger.debug(f'Sending command to ASRS: {command!r}')
        command = self._prepare_command(command)
        self.ser.write(command)

    def home_move(self):
        command = f'PLACE {self.HOME}'
        self._prepare_and_send_command(command)

    def home_center_move(self):
        command = f'PLACE {self.HOME_CENTER}'
        self._prepare_and_send_command(command)

    def asrs_place(self, side, row, column):
        command = f'PLACE {self.ASRS} {side} {row} {column}'
        self._prepare_and_send_command(command)

    def asrs_pick(self, side, row, column):
        command = f'PICK {self.ASRS} {side} {row} {column}'
        self._prepare_and_send_command(command)

    def asrs_center_move(self):
        command = f'PLACE {self.ASRS_CENTER}'
        self._prepare_and_send_command(command)

    def pre_conv_place(self):
        command = f'PLACE {self.PRE_CONVEYOR}'
        self._prepare_and_send_command(command)

    def pre_conv_pick(self):
        command = f'PICK {self.PRE_CONVEYOR}'
        self._prepare_and_send_command(command)

    def conv_place(self):
        command = f'PLACE {self.CONVEYOR}'
        self._prepare_and_send_command(command)

    def conv_pick(self):
        command = f'PICK {self.CONVEYOR}'
        self._prepare_and_send_command(command)

    def get_status(self):
        # TODO: debug it
        gpio_status = ''.join(str(GPIO.input(port)) for port in self.GPIO_STATUS_PORTS)

        gpio_status_map = {
            '000': StorageHWStatus.IDLE,
            '001': StorageHWStatus.BUSY,
            '111': StorageHWStatus.E_STOP
        }
        status = gpio_status_map.get(gpio_status, StorageHWStatus.ERROR)

        self.logger.debug(f'Current status: {status!r}')
        return status


class StorageCommandExecutorThread:
    idle_wait_timeout = 30

    def __init__(self, storage_hw_api: StorageHWAPI):
        self.st_api = storage_hw_api

        self._init_waypoints_stuff()

        self.location = StorageLocation.HOME
        self.status = StorageStatus.IDLE
        self.queue = Queue()
        self.current_task = None

        self._executor_logger = logging.getLogger(f'{type(self).__name__}(executor_thread)')
        self._executor_logger.debug('Initializing the executor thread')

        self._executor_thread = threading.Thread(target=self._executor)
        self._executor_thread.daemon = True
        self._executor_stopped = False
        self._executor_thread.start()

    def _init_waypoints_stuff(self):
        raw_waypoint_nt = namedtuple('RawWaypoint', 'location, asrs_method_positive, asrs_method_negative')
        self.waypoint_nt = namedtuple('Waypoint', 'location, asrs_method, method_args')

        self.waypoints_list = [
            raw_waypoint_nt(StorageLocation.HOME, self.st_api.home_move, self.st_api.home_move),
            raw_waypoint_nt(StorageLocation.HOME_CENTER, self.st_api.home_center_move, self.st_api.home_center_move),
            raw_waypoint_nt(StorageLocation.ASRS, self.st_api.asrs_center_move, self.st_api.asrs_center_move),
            raw_waypoint_nt(StorageLocation.PRE_CONVEYOR, self.st_api.pre_conv_place, self.st_api.pre_conv_pick),
            raw_waypoint_nt(StorageLocation.CONVEYOR, self.st_api.conv_place, self.st_api.conv_pick)
        ]

    def _generate_way_methods_list(self, from_location: StorageLocation, to_location: StorageLocation) -> list:
        """ Generates the way methods list from one location to another """
        # think about the reasons to rewrite it with collections.OrderedDict
        self._executor_logger.debug(f'Creating waypoints list'
                                    f'from {from_location.name!r} to {to_location.name!r}')

        if from_location is to_location:
            self._executor_logger.debug('Already at needed position')
            way_methods_list = []
        elif to_location.value > from_location.value:
            self._executor_logger.debug('Will move in positive direction')
            way_methods_list = self.waypoints_list[from_location.value:to_location.value + 1]
            way_methods_list = [self.waypoint_nt(w.location, w.asrs_method_positive, ()) for w in way_methods_list]
        else:
            self._executor_logger.debug('Will move in negative direction')
            way_methods_list = reversed(self.waypoints_list[to_location.value:from_location.value + 1])
            way_methods_list = [self.waypoint_nt(w.location, w.asrs_method_negative, ()) for w in way_methods_list]

        self._executor_logger.debug(f'Waypoints list: '
                                    f'{" -> ".join(str(waypoint.location) for waypoint in way_methods_list)}')
        return way_methods_list

    def _generate_pick_place_waypoints(self, from_location: StorageLocation, to_location: StorageLocation, args):
        self._executor_logger.debug(f'Generating waypoints list for {to_location} in {args}')
        way_methods_list = self._generate_way_methods_list(from_location, StorageLocation.ASRS)

        asrs_methods_map = {StorageLocation.ASRS_PICK: self.st_api.asrs_pick,
                            StorageLocation.ASRS_PLACE: self.st_api.asrs_place}

        asrs_method = asrs_methods_map[to_location]
        pick_place_waypoint = self.waypoint_nt(to_location, asrs_method, args)
        way_methods_list.append(pick_place_waypoint)

        asrs_center_waypoint = self.waypoint_nt(StorageLocation.ASRS, self.st_api.asrs_center_move, ())
        way_methods_list.append(asrs_center_waypoint)

        self._executor_logger.debug(f'Waypoints list: '
                                    f'{" -> ".join(str(waypoint.location) for waypoint in way_methods_list)}')

        return way_methods_list

    def move_to_location(self, location: StorageLocation, *args):
        """ Move from current position to the destination """
        self._executor_logger.debug(f'Put the destination in the queue: {location} '
                                    f'with args: {args}')
        self._task_queue.put((location, *args))
        self._executor_logger.debug(f'Queue: {self._task_queue.queue}')

    def _run_asrs_method_and_wait_till_execution(self, asrs_method, *args):
        self._executor_logger.debug(f'Got some asrs_method to execute: {asrs_method.__code__.co_name} '
                                    f'with args: {args}')
        self._wait_till_idle()
        self._executor_logger.debug(f'Executing {asrs_method.__code__.co_name} with args {args}')
        asrs_method(*args)  # *method_args
        self._wait_till_idle()
        self._executor_logger.debug(f'Command {asrs_method.__code__.co_name} is executed')

    def _wait_till_idle(self):
        self._executor_logger.debug('Waiting till IDLE hw state')
        time.sleep(0.5)
        if self.st_api.status is StorageHWStatus.IDLE:
            self._executor_logger.debug('Current state is IDLE already')
            return

        waiting_start_time = time.time()
        while time.time() - waiting_start_time < self.idle_wait_timeout:
            status = self.st_api.status
            if status is StorageHWStatus.IDLE:
                self._executor_logger.debug('Current state is IDLE, stops waiting')
                return
            elif status is StorageHWStatus.BUSY:
                self._executor_logger.debug('Current state is BUSY, going to sleep')
                time.sleep(0.5)
            else:
                raise RuntimeError(f"Some problems. Error: {status}")

        raise TimeoutError("timeout has been reached")

    def _executor(self):
        self._executor_logger.debug("Executor thread initialized")
        while True:
            # i can't find another way to stabilize executor thread
            try:
                if self._executor_stopped and self._task_queue.empty():
                    self._executor_logger.debug('It\'s time to STOP')
                    break

                current_location = self.location
                destination, *destination_args = self._task_queue.get()
                self._current_task = [destination, *destination_args]

                self._executor_logger.debug(f'Need to move from {current_location} to {destination}')

                if destination in [StorageLocation.ASRS_PLACE, StorageLocation.ASRS_PICK]:
                    way_methods_list = self._generate_pick_place_waypoints(current_location,
                                                                           destination,
                                                                           destination_args)
                else:
                    way_methods_list = self._generate_way_methods_list(current_location, destination)

                if way_methods_list:
                    self._executor_logger.debug(f'Calling the methods from way_methods_list one by one')
                    self.status = StorageStatus.BUSY
                    for location, asrs_method, method_args in way_methods_list:
                        self._run_asrs_method_and_wait_till_execution(asrs_method, *method_args)
                        self.location = location
                    self.status = StorageStatus.IDLE
                else:
                    self.location = destination
                self._executor_logger.debug(f'And we are here: {self.location}')
                self._current_task = None
            except Exception as e:
                self._executor_logger.exception(e)

    def stop(self):
        """ Blocking method, waits for all queue terminating """
        self._executor_logger.debug('Get command to wait for completion al queue and to stop executor')
        self._executor_stopped = True
        self._executor_thread.join()


class ASRS:
    """ Class for ASRS config storing """
    ROWS = 5
    COLUMNS = 5
    SIDES = 2


class Storage(StorageCommandExecutorThread, ASRS):
    """ High level class, that realises communication with ASRS """
    DEBUG = True
    backup_file = 'storage_backup.json'

    def __init__(self, storage_hw_api: StorageHWAPI):
        self.st_api = storage_hw_api
        super().__init__(self.st_api)
        self.logger = logging.getLogger(f'{type(self).__name__}')
        if not self.DEBUG:
            self._load_state_and_location()

    def __repr__(self):
        return f'{type(self).__name__}()'

    def __del__(self):
        if not self.DEBUG:
            self.return_to_home()
            self._save_state_and_location()

    def _load_state_and_location(self):
        # loading current state
        pass

    def _save_state_and_location(self):
        # saving current state
        pass

    def _validate_side_row_column(self, side, row, column):
        if not 1 <= side <= self.SIDES:
            raise AttributeError(f'Number of sides must be in range of [1; {self.SIDES}], got {side}')
        if not 1 <= row <= self.ROWS:
            raise AttributeError(f'Number of sides must be in range of [1; {self.ROWS}], got {row}')
        if not 1 <= column <= self.COLUMNS:
            raise AttributeError(f'Number of sides must be in range of [1; {self.COLUMNS}], got {column}')

    def return_to_home(self):
        self.logger.debug(f'Returning to home')
        self.move_to_location(StorageLocation.HOME)

    def move_to_idle_position(self):
        self.logger.debug('Moving to the idle position')
        self.move_to_location(StorageLocation.ASRS)

    def pick_from_asrs(self, side, row, column):
        self._validate_side_row_column(side, row, column)
        self.logger.debug(f'Picking up the item. side: {side}, row: {row}, column: {column}')
        self.move_to_location(StorageLocation.ASRS_PICK, side, row, column)

    def place_to_asrs(self, side, row, column):
        self._validate_side_row_column(side, row, column)
        self.logger.debug(f'Placing down the item. side: {side}, row: {row}, column: {column}')
        self.move_to_location(StorageLocation.ASRS_PLACE, side, row, column)

    def move_to_conveyor_pick_place_position(self):
        self.logger.debug('Moving to conveyor pick&place position')
        self.move_to_location(StorageLocation.CONVEYOR)

    def pick_from_conveyor(self):
        self.logger.debug('Picking up the item from conveyor')
        self.move_to_idle_position()

    def place_to_conveyor(self):
        self.logger.debug('Placing down the item on conveyor')
        self.move_to_conveyor_pick_place_position()


if __name__ == '__main__':
    s = Storage(StorageHWAPIBySerial())
