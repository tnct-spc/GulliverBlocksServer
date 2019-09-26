from flask import Blueprint, make_response, jsonify
from api.models import Block, Map, RealSense, ColorRule, Merge, MergeMap
from api._db import db
from math import sin, cos, radians
import copy
from sqlalchemy.orm import class_mapper, ColumnProperty


get_api_app = Blueprint('get_api_app', __name__)


def model_to_json(model, parse_models, ignore_field_names=None):
    if ignore_field_names is None:
        ignore_field_names = []

    data = []
    field_names = [prop.key for prop in class_mapper(model).iterate_properties if isinstance(prop, ColumnProperty)]

    for parse_model in parse_models:
        tmp_dict = {}
        for field_name in field_names:
            if field_name not in ignore_field_names:
                tmp_dict[field_name] = getattr(parse_model, field_name) if str(getattr(parse_model, field_name)) else None
        data.append(tmp_dict)

    return data


@get_api_app.route('/get_maps/')
def get_maps():
    maps = db.session.query(Map).all()

    data = {"maps": model_to_json(Map, maps)}

    return make_response(jsonify(data))


@get_api_app.route('/get_blocks/<uuid:map_id>/')
def get_blocks(map_id):
    blocks = db.session.query(Block).filter_by(map_id=map_id)

    data = {"blocks": model_to_json(Block, blocks)}

    return make_response(jsonify(data))


@get_api_app.route('/get_realsense/')
def get_realsense():
    data = {
        "realsense": []
    }
    for realsense in db.session.query(RealSense).all():
        print(realsense)
        current_map = ""
        if realsense.current_map_id is not None:
            current_map = db.session.query(Map).filter_by(id=realsense.current_map_id).first().name
        data["realsense"].append({
            "name": realsense.name,
            "online": True, # To-DO
            "current_map": current_map
        })
    return make_response(jsonify(data))


@get_api_app.route('/get_color_rules/<uuid:map_id>/')
def get_color_rules(map_id):
    color_rules = db.session.query(ColorRule).filter_by(map_id=map_id)

    data = {"rules": model_to_json(ColorRule, color_rules, ["id"])}

    for color_rule_data in data["rules"]:
        if color_rule_data["type"] == "ID":
            del color_rule_data["origin"]
        else:
            del color_rule_data["block_id"]

    return make_response(jsonify(data))


@get_api_app.route('/get_merges/')
def get_merges():
    merges = db.session.query(Merge)

    data = {"merges": model_to_json(Merge, merges)}

    return make_response(jsonify(data))


@get_api_app.route('/get_merge_maps/<uuid:merge_id>/')
def get_merge_maps(merge_id):
    merge_maps = db.session.query(MergeMap).filter_by(merge_id=merge_id)

    data = {"merge_maps": model_to_json(MergeMap, merge_maps, ["id", "merge_id"])}

    return make_response(jsonify(data))


@get_api_app.route('/get_merged_blocks/<uuid:merge_id>/')
def get_merged_blocks(merge_id):
    merge_maps = db.session.query(MergeMap).filter_by(merge_id=merge_id).all()
    merged_blocks = []

    for merge_map in merge_maps:
        blocks = db.session.query(Block).filter_by(map_id=merge_map.map_id).all()
        for _block in blocks:
            """
            ブロックの座標移動処理
            """
            block = copy.deepcopy(_block)
            rad = radians(90 * merge_map.rotate)
            tmp_x = block.x
            tmp_z = block.z
            block.x = round(tmp_x * cos(rad) - tmp_z * sin(rad))
            block.z = round(tmp_z * cos(rad) + tmp_x * sin(rad))

            block.x += merge_map.x
            block.z += merge_map.y

            merged_blocks.append(block)

    data = {"blocks": model_to_json(Block, merged_blocks)}

    return make_response(jsonify(data))
