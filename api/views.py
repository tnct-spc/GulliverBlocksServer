from flask import Blueprint, make_response, jsonify
from api.models import Block, Map
from api._db import db


api_app = Blueprint('api_app', __name__)


@api_app.route('/get_blocks/<uuid:map_id>/')
def get_blocks(map_id):
    blocks = db.session.query(Block).filter_by(map_id=map_id)
    blocks_data = {
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
        blocks_data["blocks"].append(tmp_dic)

    return make_response(jsonify(blocks_data))


@api_app.route('/get_maps/')
def get_maps():
    maps = db.session.query(Map)
    maps_data ={
        "maps": []
    }
    for map in maps:
        tmp_dic = {
            "ID": map.id,
            "name": map.name
        }
        maps_data["maps"].append(tmp_dic)

    return make_response(jsonify(maps_data))
