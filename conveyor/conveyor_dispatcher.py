from enum import Enum
from time import sleep
from itertools import cycle

import requests

from conveyor.palettes_db import PalettesDB, PaletteStatusType
from utils import env


class ConveyorLockIDs(Enum):
    PickFromStorage = 1
    LoadToStorage = 4


class ConveyorError(Exception):
    """Base class for exceptions in this module."""

    pass


class ConveyorWebApiError(ConveyorError):
    """Exception raised for errors with conveyor web api."""

    def __init__(self, message):
        self.message = message


class ConveyorDispatchingError(ConveyorError):
    """Exception raised for errors occurred within conveyor dispatching process."""

    def __init__(self, message):
        self.message = message


class ConveyorDispatcher:
    """Conveyor dispatcher base class."""

    def __init__(self, host, port):
        self.db = PalettesDB()
        self.conveyor_dispatcher_logic = ConveyorDispatcherLogic(host, port, self.db)

    def __del__(self):
        self.db.close()

    def clear_pick_from_storage_lock(self):
        """Clears pick from storage lock."""

        self.conveyor_dispatcher_logic.clear_lock(ConveyorLockIDs.PickFromStorage.value)

    def pick_palette_from_storage(self):
        """
        Picks palette from storage. Lock, on which dispatcher will be awaiting a palette, should be empty(cleared).
        :return: new palette id;
        """

        return self.conveyor_dispatcher_logic.pick_palette_from_storage()

    def move_palette_to_lock(self, palette_id, lock_to_id):
        """
        Moves palette with a given id to lock with a given id.
        :param palette_id: palette, which should be moved;
        :param lock_to_id: lock, to which palette should be moved;
        """

        self.conveyor_dispatcher_logic.move_palette_to_lock(palette_id, lock_to_id)

    def load_palette_to_storage(self, palette_id):
        """
        Loads palette with a given id to storage.
        :param palette_id: palette, which should be loaded to storage;
        """

        self.conveyor_dispatcher_logic.load_palette_to_storage(palette_id)


class ConveyorDispatcherLogic:
    """Conveyor dispatcher class that realizes all dispatching logic"""

    def __init__(self, host, port, db):
        self.db = db
        self.api_connection = ConveyorHardwareAPIConnection(host, port)
        self.helpers = ConveyorDispatchingHelpers(db, self.api_connection)

    def _make_palette_first_on_lock(self, palette_id):
        """
        Makes palette with a given id first on lock, which it stays on.
        :param palette_id: palette, which should be the first on lock;
        """

        palette_lock_id = self.db.get_palette_lock(palette_id)
        palettes_on_lock = self.db.get_palettes_on_lock(palette_lock_id)
        palettes_before = palettes_on_lock[:palettes_on_lock.index(palette_id)]
        if not palettes_before:
            return
        for palette_before_id in palettes_before:
            self.helpers.check_if_palette_is_available(palette_before_id)
        for palette_before_id in palettes_before:
            self.api_connection.pass_one_palette_from_locks(palette_lock_id)
            self.helpers.mark_palette_as_in_transit(palette_before_id)
            self.helpers.wait_palette_on_lock(palette_lock_id)
        next_lock_id = self.helpers.get_nex_lock_id(palette_lock_id)
        self.helpers.wait_palette_on_lock_if_necessary(next_lock_id)
        for palette_before_id in palettes_before:
            self.helpers.mark_palette_as_arrived(palette_before_id, next_lock_id)

    def pick_palette_from_storage(self):
        """Picks new palette from storage."""

        self.helpers.wait_palette_on_lock(ConveyorLockIDs.PickFromStorage.value)
        new_id = self.db.pick_palette_from_storage()
        return new_id

    def clear_lock(self, lock_id, wait=True):
        """
        Clears lock with a given id.
        :param lock_id: lock id;
        :param wait: is it necessary to wait palettes on next lock;
        """

        palettes_on_lock = self.db.get_palettes_on_lock(lock_id)
        if not palettes_on_lock:
            return
        for palette_on_lock_id in palettes_on_lock:
            self.helpers.check_if_palette_is_available(palette_on_lock_id)
        for palette_on_lock_id in palettes_on_lock:
            self.api_connection.pass_one_palette_from_locks(lock_id)
            self.helpers.mark_palette_as_in_transit(palette_on_lock_id)
            if palette_on_lock_id != palettes_on_lock[-1]:
                self.helpers.wait_palette_on_lock(lock_id)
        next_lock_id = self.helpers.get_nex_lock_id(lock_id)
        if wait:
            self.helpers.wait_palette_on_lock_if_necessary(next_lock_id)
        for palette_on_lock_id in palettes_on_lock:
            self.helpers.mark_palette_as_arrived(palette_on_lock_id, next_lock_id)

    def move_palette_to_lock(self, palette_id, lock_to_id):
        """
        Clears way for palette with a given id.
        :param palette_id: palette, which should be moved to given lock;
        :param lock_to_id: lock, to which palette should be moved;
        """

        palette_lock_id = self.db.get_palette_lock(palette_id)
        self.helpers.check_if_palette_is_available(palette_id)
        palette_route = self.helpers.mapper(palette_lock_id, lock_to_id)
        if not palette_route:
            self._make_palette_first_on_lock(palette_id)
            return
        palettes_on_lock = self.db.get_palettes_on_lock(palette_lock_id)
        palettes_before = palettes_on_lock[:palettes_on_lock.index(palette_id)]
        for palette_before_id in palettes_before:
            self.helpers.check_if_palette_is_available(palette_before_id)
        palettes_on_route = [self.db.get_palettes_on_lock(lock_id) for lock_id in palette_route]
        for palettes_on_lock in palettes_on_route:
            for palette_on_route_id in palettes_on_lock:
                self.helpers.check_if_palette_is_available(palette_on_route_id)
        self.clear_lock(lock_to_id, wait=False)
        palettes_on_route = [self.db.get_palettes_on_lock(lock_id) for lock_id in palette_route]
        movable_palettes = []
        for palettes_on_lock in reversed(palettes_on_route):
            movable_palettes.extend(palettes_on_lock)
        movable_palettes.extend(palettes_before)
        movable_palettes.append(palette_id)
        for i in range(len(palettes_before) + 1):
            self.api_connection.pass_one_palette_from_locks(palette_lock_id)
            if i < len(palettes_before):
                self.helpers.wait_palette_on_lock(palette_lock_id)
        self.api_connection.open_locks(palette_route[:-1])
        for movable_palette_id in movable_palettes:
            self.helpers.mark_palette_as_in_transit(movable_palette_id)
        for movable_palette_id in movable_palettes:
            self.helpers.wait_palette_on_lock(lock_to_id)
            if movable_palette_id != palette_id:
                self.api_connection.pass_one_palette_from_locks(lock_to_id)
            else:
                self.helpers.mark_palette_as_arrived(movable_palette_id, lock_to_id)
        next_lock_id = self.helpers.get_nex_lock_id(lock_to_id)
        self.helpers.wait_palette_on_lock_if_necessary(next_lock_id)
        for movable_palette_id in movable_palettes[:-1]:
            self.helpers.mark_palette_as_arrived(movable_palette_id, next_lock_id)
        self.api_connection.close_locks(palette_route[:-1])

    def load_palette_to_storage(self, palette_id):
        """
        Loads palette to storage.
        :param palette_id: palette, which should be loaded to storage;
        """

        self.helpers.check_if_palette_is_available(palette_id)
        self.api_connection.pass_one_palette_from_locks(ConveyorLockIDs.LoadToStorage.value)
        self.helpers.mark_palette_as_in_transit(palette_id)
        sleep(self.db.get_storage_awaiting_time())
        self.db.load_palette_to_storage(palette_id)


class ConveyorDispatchingHelpers:
    """Class that provides dispatching helpers, e.g. palette waiting methods and etc."""

    def __init__(self, db, api_connection):
        self.db = db
        self.api_connection = api_connection
        self.lock_ids = self.api_connection.get_locks_ids()

    def get_nex_lock_id(self, start_lock_id):
        """
        Founds a next lock id from a given one.
        :param start_lock_id: lock id, for which next lock should be found;
        :return: next lock id;
        """

        self.api_connection.get_lock_status(start_lock_id)
        full_route = cycle(self.lock_ids)
        while True:
            lock_id = next(full_route)
            if lock_id == start_lock_id:
                break
        next_lock_id = next(full_route)
        return next_lock_id

    def mapper(self, lock_from_id, lock_to_id):
        """
        Makes a map for palette from one lock to another.
        :param lock_from_id: start lock;
        :param lock_to_id: end lock;
        :return: list with a lock ids, which are on route;
        """

        self.api_connection.get_lock_status(lock_from_id)
        self.api_connection.get_lock_status(lock_to_id)
        full_route = cycle(self.lock_ids)
        route = []
        lock_id = next(full_route)
        while lock_id != lock_from_id:
            lock_id = next(full_route)
        while lock_id != lock_to_id:
            lock_id = next(full_route)
            route.append(lock_id)
        return route

    def check_if_palette_is_available(self, palette_id):
        """
        Checks if palette with given id is available. If palette is not available, raises ConveyorDispatchingError.
        :param palette_id: palette, which should be checked;
        """

        is_available = self.db.get_palette_status(palette_id, PaletteStatusType.Available.value)
        if not is_available:
            raise ConveyorDispatchingError(
                'Attempting to operate palette with id: {} ,which is not available.'.format(palette_id))

    def mark_palette_as_in_transit(self, palette_id):
        """
        Marks palette as 'in transit'.
        :param palette_id: palette, which is in transit;
        """

        self.db.remove_palette_from_lock(palette_id)
        self.db.update_palette_status(palette_id, PaletteStatusType.Available.value, False)
        self.db.update_palette_status(palette_id, PaletteStatusType.InTransit.value, True)

    def mark_palette_as_arrived(self, palette_id, lock_id):
        """
        Marks palette as 'arrived'.
        :param palette_id: palette, which is arrived to lock;
        :param lock_id: lock, on which palette arrived;
        """

        self.db.update_palette_status(palette_id, PaletteStatusType.Available.value, True)
        self.db.update_palette_status(palette_id, PaletteStatusType.InTransit.value, False)
        self.db.add_palette_to_lock(palette_id, lock_id)

    def wait_palette_on_lock(self, lock_id):
        """
        Waits palette on lock with a given id.
        :param lock_id: lock id;
        """

        control_lock_status = self.api_connection.get_lock_status(lock_id)
        control_lock_is_busy = control_lock_status['is_busy']
        while not control_lock_is_busy:
            sleep(0.1)
            control_lock_is_busy = self.api_connection.get_lock_status(lock_id)['is_busy']

    def wait_palette_on_lock_if_necessary(self, lock_id):
        """
        Waits palette on lock with given id, if there are no palettes on lock.
        :param lock_id: lock, on which palette should be waited;
        """

        palettes_on_lock = self.db.get_palettes_on_lock(lock_id)
        if palettes_on_lock:
            return
        self.wait_palette_on_lock(lock_id)


class ConveyorHardwareAPIConnection:
    """Class that provides connection to conveyor API and methods to work with it"""

    def __init__(self, host, port):
        self.hv_api_url = 'http://{}:{}/api/v1/conveyor/'.format(host, port)

    def _send_request(self, endpoint, data=None):
        """
        Sends request to a given endpoint with a given data to conveyor api.
        :param endpoint: endpoint for conveyor api;
        :param data: sent data;
        :return: response;
        """

        return requests.post(self.hv_api_url + endpoint, json=data)

    def get_locks_ids(self):
        """
        Gets conveyor locks ids. If request couldn't be resolved, raises ConveyorWebApiError.
        :return: list of conveyor locks;
        """

        r = self._send_request('status')
        if r.status_code != 200:
            raise ConveyorWebApiError("Can't get conveyor status.")
        response_data = r.json()
        locks_state = response_data['body']['locks_state']
        return [lock['id'] for lock in locks_state]

    def get_lock_status(self, lock_id):
        """
        Gets status of lock with a given id. If request couldn't be resolved, raises ConveyorWebApiError.
        :param lock_id: lock, for which status should be get;
        :return: lock status;
        """

        data = {'ids': [lock_id]}
        r = self._send_request('locks/status', data)
        if r.status_code != 200:
            error_message = r.json()['data']
            raise ConveyorWebApiError("Can't get status of lock with id: {}.\n{}".format(lock_id, error_message))
        response_data = r.json()
        return response_data['body'][0]

    def _send_operation_request(self, lock_ids, endpoint, error_message):
        """
        Sends an operation request (open, close or pass_one) to conveyor api.
        If request couldn't be resolved, raises ConveyorWebApiError.
        :param lock_ids: locks, which conveyor should operate with;
        :param endpoint: operation endpoint for conveyor api;
        :param error_message: message, which would be shown if an error occurs;
        """

        if not lock_ids:
            return
        data = {'ids': lock_ids if isinstance(lock_ids, list) else [lock_ids]}
        r = self._send_request(endpoint, data)
        if r.status_code != 200:
            error_message = r.json()['body']
            raise ConveyorWebApiError(error_message.format(lock_ids) + '\n' + error_message)

    def pass_one_palette_from_locks(self, lock_ids):
        """
        Passes one palette from locks with a given ids.
        :param lock_ids: locks, from which palettes should be passed;
        """

        self._send_operation_request(lock_ids, 'locks/pass_one', "Can't pass one palette from locks with ids: {}")

    def open_locks(self, lock_ids):
        """
        Opens locks with a given ids.
        :param lock_ids: locks, which should be opened;
        """

        self._send_operation_request(lock_ids, 'locks/open', "Can't open locks with ids: {}")

    def close_locks(self, lock_ids):
        """
        Closes locks with a given ids.
        :param lock_ids: locks, which should be closed;
        """

        self._send_operation_request(lock_ids, 'locks/close', "Can't close locks with ids: {}")


if __name__ == '__main__':
    cv = ConveyorDispatcher(env.conveyor_web_api_host, env.conveyor_web_api_port)
