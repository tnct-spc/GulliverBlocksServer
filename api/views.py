from flask import Blueprint, make_response, jsonify, request
from api.models import Block, Map
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
            "ID": block.id,
            "colorID": block.colorID,
            "time": block.time,
            "x": block.x,
            "y": block.y,
            "z": block.z
        }
        test_data["blocks"].append(tmp_dic)

    return make_response(jsonify(test_data))


@api_app.route('/create_map/', methods=["POST"])
def create_map():
    name = request.form['name']
    new_map = Map()
    new_map.name = name
    db.session.add(new_map)
    try:
        db.session.commit()
    except:
        db.session.rollback()
        return "error"
    return str(new_map.id)
