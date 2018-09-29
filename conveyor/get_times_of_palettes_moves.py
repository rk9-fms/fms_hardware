from conveyor.conveyor_hardware_api import Conveyor, Lock
from itertools import cycle
from datetime import datetime
from time import sleep
import json


cv = Conveyor([Lock('ZYL.1', 4, 18), Lock('ZYL.2', 17, 23), Lock('ZYL.3', 27, 24), Lock('ZYL.4', 22, 25)])
locks_cycle = cycle(cv.locks)
times = {
    "1->2": [],
    "2->3": [],
    "3->4": [],
    "4->1": []
}
end_lock = None
for _ in range(10):
    for __ in range(4):
        start_lock = next(locks_cycle) if not end_lock else end_lock
        start_lock.pass_one()
        movement_start_time = datetime.now()
        end_lock = next(locks_cycle)
        end_lock_is_busy = end_lock.is_busy
        while not end_lock_is_busy:
            sleep(0.1)
            end_lock_is_busy = end_lock.is_busy
        movement_end_time = datetime.now()
        movement_time = movement_end_time - movement_start_time
        times["{}->{}".format(start_lock.id, end_lock.id)].append(str(movement_time))
with open("movement_times.json", "w") as mt:
    mt.write(json.dumps(times, sort_keys=True, indent=4))
