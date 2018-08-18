from flask import Flask, jsonify, make_response, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


@app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/<path:path>', methods=['GET', 'POST'])
def catch_all(path):
    print(path, request.json)
    return make_response(jsonify({'status': 200, 'body': 'yasos bib'}))


# just for logs monitoring
app.run(port=5000)
