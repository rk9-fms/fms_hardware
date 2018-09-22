from flask import Flask, Blueprint, jsonify, request, make_response
from flask_cors import CORS
from multiprocessing.pool import ThreadPool

from conveyor.conveyor_hardware_api import Conveyor, Lock


app = Flask(__name__)
CORS(app)

conveyor_api = Blueprint('conveyor_api', __name__, url_prefix='/api/v1/conveyor')

cv = Conveyor([Lock('ZYL.1', 4, 18), Lock('ZYL.2', 17, 23), Lock('ZYL.3', 27, 24), Lock('ZYL.4', 22, 25)])


def _validate_lock_id_or_name(request_json):
    try:
        lock_ids = request_json.get("ids")
        lock_names = request_json.get("names")
    except AttributeError:
        lock_ids = None
        lock_names = None
    error = None
    unknown_locks = []
    if lock_ids:
        parameter = lock_ids
        parameter_name = "ids"
        conveyor_lock_ids = [lock.id for lock in cv.locks]
        for lock_id in lock_ids:
            if lock_id not in conveyor_lock_ids:
                unknown_locks.append(lock_id)
    elif lock_names:
        parameter = lock_names
        parameter_name = "names"
        conveyor_lock_names = [lock.name for lock in cv.locks]
        for lock_name in lock_names:
            if lock_name not in conveyor_lock_names:
                unknown_locks.append(lock_name)
    else:
        parameter = None
        parameter_name = None
        error = "No data was sent"
    if unknown_locks:
            error = "Locks with {}:{} are not attached to conveyor".format(parameter_name, unknown_locks)
    return error, parameter


@conveyor_api.route("/locks/status", methods=["GET", "POST"])
def locks_status():
    params = request.json
    error, locks = _validate_lock_id_or_name(params)
    if not error:
        resp_json = {
            "status": 200, "body": [
                {
                    "id": cv.lock_state(lock).lock.id,
                    "name": cv.lock_state(lock).lock.name,
                    "status": cv.lock_state(lock).state.name,
                    "is_busy": cv.lock_state(lock).lock.is_busy,
                } for lock in locks
                ]
            }
        return make_response(jsonify(resp_json), 200)
    else:
        resp_json = {"status": 400, "body": error}
        return make_response(jsonify(resp_json), 400)


@conveyor_api.route("/locks/open", methods=["GET", "POST"])
def locks_open():
    params = request.json
    error, locks = _validate_lock_id_or_name(params)
    if not error:
        p = ThreadPool(len(cv.locks))
        p.map(cv.lock_open, tuple(locks))
        p.close()
        p.join()
        resp_json = {
            "status": 200, "body": {
                "lock(id:{}, name: {})".format(cv.lock_state(lock).lock.id, cv.lock_state(lock).lock.name):
                    "Has been opened" for lock in locks
            }
        }
        return make_response(jsonify(resp_json), 200)
    else:
        resp_json = {"status": 400, "body": error}
        return make_response(jsonify(resp_json), 400)


@conveyor_api.route("/locks/close", methods=["GET", "POST"])
def locks_close():
    params = request.json
    error, locks = _validate_lock_id_or_name(params)
    if not error:
        p = ThreadPool(len(cv.locks))
        p.map(cv.lock_close, tuple(locks))
        p.close()
        p.join()
        resp_json = {
            "status": 200, "body": {
                "lock(id:{}, name: {})".format(cv.lock_state(lock).lock.id, cv.lock_state(lock).lock.name):
                    "Has been closed" for lock in locks
            }
        }
        return make_response(jsonify(resp_json), 200)
    else:
        resp_json = {"status": 400, "body": error}
        return make_response(jsonify(resp_json), 400)


@conveyor_api.route("/locks/pass_one", methods=["GET", "POST"])
def locks_pass_one():
    params = request.json
    error, locks = _validate_lock_id_or_name(params)
    if not error:
        p = ThreadPool(len(cv.locks))
        p.map(cv.lock_pass_one, tuple(locks))
        p.close()
        p.join()
        resp_json = {
            "status": 200, "body": {
                "lock(id:{}, name: {})".format(cv.lock_state(lock).lock.id, cv.lock_state(lock).lock.name):
                    "Car has been released" for lock in locks
            }
        }
        return make_response(jsonify(resp_json), 200)
    else:
        resp_json = {"status": 400, "body": error}
        return make_response(jsonify(resp_json), 400)


@conveyor_api.route("/status", methods=["GET", "POST"])
def conveyor_status():
    resp_json = {
        "status": 200, "body": {
            "conveyor_state": cv.state.name, "locks_state": [
                {
                    "id": lock.lock.id,
                    "name": lock.lock.name,
                    "status": lock.state.name,
                    "is_busy": lock.lock.is_busy,
                } for lock in cv.locks_state()
            ]
        }
    }
    return make_response(jsonify(resp_json), 200)


app.register_blueprint(conveyor_api)

if __name__ == "__main__":
    app.run()
