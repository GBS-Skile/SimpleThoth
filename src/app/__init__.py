from flask import Flask, jsonify, request
from ..scenario import Scenario

app = Flask(__name__)
app.config.from_pyfile('config.cfg')

scenario = Scenario(app.config['SCENARIO_PATH'])

@app.route('/', methods=['POST'])
def run_scenario():
    req = request.get_json()

    res = scenario.action(req.get('context', {}), req.get('msg', ''))
    res['sess_id'] = req.get('sess_id', None)
    return jsonify(res)


if __name__ == '__main__':
    app.run()
