from flask import Blueprint, make_response, jsonify
from datetime import datetime


api_app = Blueprint('api_app', __name__)


@api_app.route('/return_test_data/')
def return_test_data():
    test_data = {
        "1": {
            "x": 1,
            "y": 2,
            "z": 3,
            "time": datetime.now().timestamp(),
            "colorID": 1,
            "put": True,
        },
        "2": {
            "x": 1,
            "y": 3,
            "z": 3,
            "time": datetime.now().timestamp(),
            "colorID": 1,
            "put": True,
        },
        "3": {
            "x": 2,
            "y": 2,
            "z": 3,
            "time": datetime.now().timestamp(),
            "colorID": 1,
            "put": True,
        },
        "4": {
            "x": 1,
            "y": 2,
            "z": 4,
            "time": datetime.now().timestamp(),
            "colorID": 1,
            "put": True,
        },
        "5": {
            "x": 1,
            "y": 2,
            "z": 2,
            "time": datetime.now().timestamp(),
            "colorID": 1,
            "put": True,
        },
    }
    return make_response(jsonify(test_data))
