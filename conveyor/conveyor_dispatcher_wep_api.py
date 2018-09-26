from flask import Flask, Blueprint, jsonify, request, make_response
from flask_cors import CORS

from conveyor.conveyor_dispatcher import ConveyorDispatcher, ConveyorError
from utils import env


app = Flask(__name__)
CORS(app)

conveyor_api = Blueprint('conveyor_dispatcher_api', __name__, url_prefix='/api/v1/conveyor_dispatcher')

dispatcher = ConveyorDispatcher(env.conveyor_web_api_host, env.conveyor_web_api_port)


def _validate_parameter(request_json, parameter_name):
    error_message = ''
    try:
        parameter = request_json.get(parameter_name)
    except AttributeError:
        parameter, error_message = None, 'No "{}" parameter was sent'.format(parameter_name)
    else:
        if not isinstance(parameter, (int, str)):
            error_message = 'Wrong type for "{}" parameter'.format(parameter_name)
    return parameter, error_message


def _validate_request_parameters(request_json, lock=False):
    palette_id, error_message_palette = _validate_parameter(request_json, 'palette_id')
    res = {'parameters': [palette_id], 'errors': [error_message_palette]}
    if lock:
        lock_id, error_message_lock = _validate_parameter(request_json, 'lock_id')
        res['parameters'].append(lock_id)
        res['errors'].append(error_message_lock)
    return res


@conveyor_api.route('clear_pick_from_storage_lock', methods=['GET', 'POST'])
def clear_pick_from_storage_lock():
    try:
        dispatcher.clear_pick_from_storage_lock()
    except ConveyorError as e:
        resp_json = {'status': 400, 'body': e}
        return make_response(jsonify(resp_json), 400)
    else:
        resp_json = {
            'status': 200, 'body': 'Pick from storage lock has been cleared successfully'
        }
        return make_response(jsonify(resp_json), 200)


@conveyor_api.route('pick_palette_from_storage', methods=['GET', 'POST'])
def pick_palette_from_storage():
    try:
        new_palette_id = dispatcher.pick_palette_from_storage()
    except ConveyorError as e:
        resp_json = {'status': 400, 'body': e}
        return make_response(jsonify(resp_json), 400)
    else:
        resp_json = {
            'status': 200, 'body': 'New palette has been pick successfully. New palette id: {}'.format(new_palette_id)
        }
        return make_response(jsonify(resp_json), 200)


def operate_with_parametrized_request(error_message, lock=False):
    params = request.json
    res = _validate_request_parameters(params, lock)
    parameters, errors = res['parameters'], res['errors']
    if not any(errors):
        dispatcher.load_palette_to_storage(*parameters)
        resp_json = {
            'status': 200, 'body': error_message.format(*parameters)
        }
        return make_response(jsonify(resp_json), 200)
    else:
        resp_json = {'status': 400, 'body': '\n'.join(errors)}
        return make_response(jsonify(resp_json), 400)


@conveyor_api.route('move_palette_to_lock', methods=['GET', 'POST'])
def move_palette_to_lock():
    operate_with_parametrized_request('Palette with id "{}" has been moved to lock "{}" successfully', lock=True)


@conveyor_api.route('load_palette_to_storage', methods=['GET', 'POST'])
def load_palette_to_storage():
    operate_with_parametrized_request('Palette wit id "{}" has been load to storage successfully')


@conveyor_api.route('palettes_db', methods=['GET', 'POST'])
def palettes_db():
    resp_json = {
        'status': 200, 'body': dispatcher.db.palettes_db
    }
    return make_response(jsonify(resp_json), 200)


@conveyor_api.route('palettes_on_lock_db', methods=['GET', 'POST'])
def palettes_on_lock_db():
    resp_json = {
        'status': 200, 'body': dispatcher.db.palettes_on_lock_db
    }
    return make_response(jsonify(resp_json), 200)


app.register_blueprint(conveyor_api)

if __name__ == '__main__':
    app.run(env.conveyor_dispatcher_web_api_host, env.conveyor_dispatcher_web_api_port)
