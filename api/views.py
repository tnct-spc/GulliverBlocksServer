from flask import Blueprint, make_response, jsonify
from api.models import Block
from api._db import db


api_app = Blueprint('api_app', __name__)


@api_app.route('/return_test_data/')
def return_test_data():
    blocks = db.session.query(Block)
    test_data = {
        "blocks": []
    }

    for block in blocks:
        tmp_dic = {
            "ID": block.block_id,
            "colorID": block.colorID,
            "put": block.put,
            "time": block.time,
            "x": block.x,
            "y": block.y,
            "z": block.z
        }
        test_data["blocks"].append(tmp_dic)

    return make_response(jsonify(test_data))
