import time

import pytest

from storage.hardware_api.storage_test_api import StorageLocation, StorageStatus, Storage, test_st_hw_api


@pytest.fixture()
def new_storage():
    print('prepare storage')
    return Storage(test_st_hw_api)


def _wait_till_status(storage: Storage, status: StorageStatus):
    while True:
        if storage.status is status:
            return
        time.sleep(0.5)


def test_common_variables(new_storage: Storage):
    assert new_storage.status == StorageStatus.IDLE
    assert new_storage.location == StorageLocation.HOME
    assert new_storage.queue.empty()
    assert new_storage.current_task is None


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
    assert new_storage.status is StorageStatus.BUSY

    _wait_till_status(new_storage, StorageStatus.IDLE)
    assert new_storage.status is StorageStatus.IDLE

    assert new_storage.location is location
