from flask import Flask, Blueprint, jsonify, request, make_response
from flask_cors import CORS
from flask_socketio import SocketIO


app = Flask(__name__)
socketio = SocketIO(app)
CORS(app)

# TODO: refactor this in next iteration
# for debug purposes. in "prod" run by nginx (or uwsgi in my case)
if __name__ == "__main__":
    from storage.hardware_api.storage_test_api import test_st_hw_api, test_st
    st = test_st
else:
    from storage.hardware_api.storage_api import Storage, StorageHWAPIBySerial
    st = Storage(StorageHWAPIBySerial())

storage_api_url_prefix = '/api/v1/storage'
storage_api = Blueprint('storage_api', __name__, url_prefix=storage_api_url_prefix)


@app.errorhandler(404)
def _handle_api_error(ex):
    if request.path.startswith(storage_api_url_prefix):
        return make_response(jsonify({'status': 404, 'body': ''}), 404)
    else:
        return ex


def _validate_side_row_column(request_json):
    error = None
    side, row, column = (request_json.get(k) for k in ['side', 'row', 'column'])
    if not all([side, row, column]):
        error = "You need to pass 'row', 'side' and 'column'"
    elif not all(isinstance(arg, int) for arg in [side, row, column]):
        error = 'All args must be integer'
    elif not 1 <= side <= st.SIDES:
        error = f'Number of sides must be in range of [1; {st.SIDES}], got {side}'
    elif not 1 <= row <= st.ROWS:
        error = f'Number of sides must be in range of [1; {st.ROWS}], got {row}'
    elif not 1 <= column <= st.COLUMNS:
        error = f'Number of sides must be in range of [1; {st.COLUMNS}], got {column}'
    return error, side, row, column


@storage_api.route('/move_to/home', methods=['GET', 'POST'])
def move_to_home():
    st.return_to_home()

    resp_json = {"status": 200, "body": "added to queue"}
    return make_response(jsonify(resp_json), 200)


@storage_api.route('/move_to/idle_position', methods=['GET', 'POST'])
def move_to_idle_position():
    st.move_to_idle_position()

    resp_json = {"status": 200, "body": "added to queue"}
    return make_response(jsonify(resp_json), 200)


@storage_api.route('/move_to/conveyor', methods=['GET', 'POST'])
def move_to_conveyor():
    st.move_to_conveyor_pick_place_position()

    resp_json = {"status": 200, "body": "added to queue"}
    return make_response(jsonify(resp_json), 200)


@storage_api.route('/pick/asrs', methods=['GET', 'POST'])
def pick_asrs():
    params = request.json
    error, side, row, column = _validate_side_row_column(params)
    if error:
        resp_json = {"status": 400, "body": error}
        return make_response(jsonify(resp_json), 400)

    st.pick_from_asrs(side, row, column)

    resp_json = {"status": 200, "body": "added to queue"}
    return make_response(jsonify(resp_json), 200)


@storage_api.route('/pick/conveyor', methods=['GET', 'POST'])
def pick_conveyor():
    st.pick_from_conveyor()
    # return 400 if location is not CONVEYOR
    resp_json = {"status": 200, "body": "added to queue"}
    return make_response(jsonify(resp_json), 200)


@storage_api.route('/place/asrs', methods=['GET', 'POST'])
def place_asrs():
    params = request.json
    error, side, row, column = _validate_side_row_column(params)
    if error:
        resp_json = {"status": 400, "body": error}
        return make_response(jsonify(resp_json), 400)

    st.place_to_asrs(side, row, column)

    resp_json = {"status": 200, "body": "added to queue"}
    return make_response(jsonify(resp_json), 200)


@storage_api.route('/place/conveyor', methods=['GET', 'POST'])
def place_conveyor():
    st.place_to_conveyor()

    resp_json = {"status": 200, "body": "added to queue"}
    return make_response(jsonify(resp_json), 200)


@storage_api.route('/location', methods=['GET', 'POST'])
def location():
    _location = st.location

    resp_json = {"status": 200, "body": {'location': {'name': _location.name,
                                                      'value': _location.value}}}
    return make_response(jsonify(resp_json), 200)


@storage_api.route('/status', methods=['GET', 'POST'])
def status():
    _status = st.status
    
    resp_json = {"status": 200, "body": {'status': {'name': _status.name,
                                                    'value': _status.value}}}
    return make_response(jsonify(resp_json), 200)


@storage_api.route('/current_task', methods=['GET', 'POST'])
def current_task():
    _current_task = st.current_task
    if _current_task:
        _current_task, *_task_args = st.current_task

        resp_json = {"status": 200, "body": {'current_task': {'name': _current_task.name,
                                                              'value': _current_task.value,
                                                              'task_args': _task_args}}}
    else:
        resp_json = {"status": 200, "body": {'current_task': None}}
    return make_response(jsonify(resp_json), 200)


@storage_api.route('/debug/output', methods=['GET', 'POST'])
def debug_output():

    return b'<br>'.join(st_hw_api.ser.getvalue().split(b'\n\r'))


@storage_api.route('/queue', methods=['GET', 'POST'])
def queue():
    _queue = [[loc.name, loc.value, args] for loc, *args in st.queue.queue]
    resp_json = {"status": 200, "body": {"queue": _queue}}
    return make_response(jsonify(resp_json), 200)


app.register_blueprint(storage_api)


if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0')
    # app.run(host='0.0.0.0')
