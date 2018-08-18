from flask import Flask, Blueprint, jsonify, request, make_response
from flask_cors import CORS

from conveyor.conveyor_hardware_api import Conveyor, Lock


app = Flask(__name__)
CORS(app)

conveyor_api = Blueprint('conveyor_api', __name__, url_prefix='/api/v1/conveyor')

cv = Conveyor([Lock('ZYL.1', 4, 18), Lock('ZYL.2', 17, 23), Lock('ZYL.3', 27, 24), Lock('ZYL.4', 22, 25)])


def _validate_lock_id_or_name(request_json):
    locks_ids = request_json.get("id") if isinstance(request_json.get("id"), list) else [request_json.get("id")]
    locks_names = request_json.get("name") if isinstance(request_json.get("name"), list) else [request_json.get("name")]
    if locks_names and not locks_ids:
        all_locks_names = [lock.name for lock in cv.locks]
        locks_ids = [all_locks_names.index(lock_name.upper()) for lock_name in locks_names]
    all_locks_ids = [cv.locks.index(lock) for lock in cv.locks]
    error = None
    unknown_locks = []
    for lock_id in locks_ids:
        if lock_id not in all_locks_ids:
            unknown_locks.append(lock_id)
    if unknown_locks:
        if len(unknown_locks) == 1:
            error = "Lock with id:{} is not attached to conveyor".format(unknown_locks[0])
        else:
            error = "Locks with ids:{} are not attached to conveyor".format(unknown_locks)
    return error, locks_ids if len(locks_ids) > 1 else locks_ids[0]


@conveyor_api.route("/lock/status", methods=["GET", "POST"])
def lock_status():
    params = request.json
    error, lock_id = _validate_lock_id_or_name(params)
    if not error:
        resp_json = {"status": 200, "body": {"lock({})".format(lock_id): cv.lock_state(lock_id)}}
        return make_response(jsonify(resp_json), 200)
    else:
        resp_json = {"status": 400, "body": error}
        return make_response(jsonify(resp_json), 400)


@conveyor_api.route("/lock/open", methods=["GET", "POST"])
def lock_open():
    params = request.json
    error, lock_id = _validate_lock_id_or_name(params)
    if not error:
        cv.lock_open(lock_id)
        resp_json = {"status": 200, "body": {"lock()".format(lock_id): "Has been opened"}}
        return make_response(jsonify(resp_json), 200)
    else:
        resp_json = {"status": 400, "body": error}
        return make_response(jsonify(resp_json), 400)


@conveyor_api.route("/lock/close", methods=["GET", "POST"])
def lock_close():
    params = request.json
    error, lock_id = _validate_lock_id_or_name(params)
    if not error:
        cv.lock_close(lock_id)
        resp_json = {"status": 200, "body": {"lock()".format(lock_id): "Has been closed"}}
        return make_response(jsonify(resp_json), 200)
    else:
        resp_json = {"status": 400, "body": error}
        return make_response(jsonify(resp_json), 400)


@conveyor_api.route("/lock/pass_one", methods=["GET", "POST"])
def lock_pass_one():
    params = request.json
    error, lock_id = _validate_lock_id_or_name(params)
    if not error:
        cv.lock_release_car(lock_id)
        resp_json = {"status": 200, "body": {"lock()".format(lock_id): "Car has been released"}}
        return make_response(jsonify(resp_json), 200)
    else:
        resp_json = {"status": 400, "body": error}
        return make_response(jsonify(resp_json), 400)


@conveyor_api.route("/locks/status", methods=["GET", "POST"])
def locks_status():
    params = request.json
    error, locks_ids = _validate_lock_id_or_name(params)
    if not error:
        resp_json = {
            "status": 200, "body": {
                "lock({})".format(lock_id): cv.lock_state(lock_id) for lock_id in locks_ids
            }
        }
        return make_response(jsonify(resp_json), 200)
    else:
        resp_json = {"status": 400, "body": error}
        return make_response(jsonify(resp_json), 400)


@conveyor_api.route("/locks/open", methods=["GET", "POST"])
def locks_open():
    params = request.json
    error, locks_ids = _validate_lock_id_or_name(params)
    if not error:
        for lock_id in locks_ids:
            cv.lock_open(lock_id)
        resp_json = {
            "status": 200, "body": {
                "lock({})".format(lock_id): "Has been opened" for lock_id in locks_ids
            }
        }
        return make_response(jsonify(resp_json), 200)
    else:
        resp_json = {"status": 400, "body": error}
        return make_response(jsonify(resp_json), 400)


@conveyor_api.route("/locks/close", methods=["GET", "POST"])
def locks_close():
    params = request.json
    error, locks_ids = _validate_lock_id_or_name(params)
    if not error:
        for lock_id in locks_ids:
            cv.lock_close(lock_id)
        resp_json = {
            "status": 200, "body": {
                "lock({})".format(lock_id): "Has been closed" for lock_id in locks_ids
            }
        }
        return make_response(jsonify(resp_json), 200)
    else:
        resp_json = {"status": 400, "body": error}
        return make_response(jsonify(resp_json), 400)


@conveyor_api.route("/locks/pass_one", methods=["GET", "POST"])
def locks_pass_one():
    params = request.json
    error, locks_ids = _validate_lock_id_or_name(params)
    if not error:
        for lock_id in locks_ids:
            cv.lock_release_car(lock_id)
        resp_json = {
            "status": 200, "body": {
                "lock({})".format(lock_id): "Car has been released" for lock_id in locks_ids
            }
        }
        return make_response(jsonify(resp_json), 200)
    else:
        resp_json = {"status": 400, "body": error}
        return make_response(jsonify(resp_json), 400)


@conveyor_api.route("/status", methods=["GET", "POST"])
def conveyor_status():
    resp_json = {"status": 200, "body": cv.locks_state()}
    return make_response(jsonify(resp_json), 200)


app.register_blueprint(conveyor_api)

if __name__ == "__main__":
    app.run()
