import json


with open('environments.json', 'r') as r:
    envs = json.load(r)
conveyor_web_api_host = envs['conveyor'].get('web_api_host', 'localhost')
conveyor_web_api_port = envs['conveyor'].get('web_api_port', 5000)
conveyor_dispatcher_web_api_host = envs['conveyor'].get('dispatcher_web_api_host', 'localhost')
conveyor_dispatcher_web_api_port = envs['conveyor'].get('dispatcher_web_api_port', 5000)
