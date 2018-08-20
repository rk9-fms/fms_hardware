import time

import pytest

from storage.hardware_api.storage_test_api import StorageLocation, StorageStatus, Storage, test_st_hw_api


@pytest.fixture()
def new_storage():
    print('prepare storage')
    return Storage(test_st_hw_api)


def _wait_till_status(storage: Storage, status: StorageStatus):
    while True:
        if storage.status.value is status:
            return
        time.sleep(0.5)


def test_common_variables(new_storage: Storage):
    assert new_storage.status.value == StorageStatus.IDLE
    assert new_storage.location.value == StorageLocation.HOME
    assert new_storage.queue.empty()
    assert new_storage.current_task.value is None


@pytest.mark.parametrize('location', [
    # StorageLocation.HOME,
    StorageLocation.HOME_CENTER,
    StorageLocation.ASRS,
    StorageLocation.PRE_CONVEYOR,
    StorageLocation.CONVEYOR
])
def test_simple_movement_to_location(location: StorageLocation, new_storage: Storage):
    new_storage.move_to_location(location)

    _wait_till_status(new_storage, StorageStatus.BUSY)
    assert new_storage.status.value is StorageStatus.BUSY

    _wait_till_status(new_storage, StorageStatus.IDLE)
    assert new_storage.status.value is StorageStatus.IDLE

    assert new_storage.location.value is location


def test_callbacks(new_storage: Storage):
    callbacks_signs_list = ['status_cb', 'location_cb', 'queue_cb', 'current_task_cb']
    status_sign, location_sign, queue_sign, current_task_sign = callbacks_signs_list

    cbs_assertion_list = []

    # register all calbacks
    new_storage.status.register_callback(lambda x: cbs_assertion_list.append((status_sign, x)))
    new_storage.location.register_callback(lambda x: cbs_assertion_list.append((location_sign, x)))
    new_storage.queue.register_callback(lambda x: cbs_assertion_list.append((queue_sign, list(x.queue))))
    new_storage.current_task.register_callback(lambda x: cbs_assertion_list.append((current_task_sign, x)))

    # init some actions
    new_storage.move_to_idle_position()
    _wait_till_status(new_storage, StorageStatus.BUSY)
    _wait_till_status(new_storage, StorageStatus.IDLE)

    unique_cbs_assertions = {cb_sign[0] for cb_sign in cbs_assertion_list}
    assert all(True if sign in unique_cbs_assertions else False for sign in callbacks_signs_list)
