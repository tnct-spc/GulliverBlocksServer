from flask import Blueprint, make_response, jsonify, request, abort
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
    if request.content_type == "application/json":
        name = request.json["name"]  # request.jsonにはcontent_typeがapplication/jsonのときにしかデータが入らない
        new_map = Map(name=name)
        db.session.add(new_map)
        try:
            db.session.commit()
        except:
            db.session.rollback()
            return abort(500)

        map_data = {
            "ID": new_map.id,
            "name": name
        }
        return make_response(jsonify(map_data))
    else:
        return abort(406)
