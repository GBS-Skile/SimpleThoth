from flask import Flask, jsonify, request
import os
from ..scenario import Scenario

app = Flask(__name__)
app.config.from_pyfile('config.cfg')

scenario_path = os.environ.get('SCENARIO_PATH')
if not scenario_path:
    raise FileNotFoundError('Please set SCENARIO_PATH environment variable')
scenario = Scenario(scenario_path)

@app.route('/', methods=['POST'])
def run_scenario():
    req = request.get_json()

    res = scenario.action(req.get('context', {}), req.get('msg', ''))
    res['sess_id'] = req.get('sess_id', None)
    return jsonify(res)


if __name__ == '__main__':
    app.run()
