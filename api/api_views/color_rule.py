from flask import Blueprint, make_response, jsonify, request
from api.models import ColorRule, MergeMap
from api.api_views.parse_help_lib import model_to_json
from api._db import db


color_rule_api_app = Blueprint('color_rule_api_app', __name__)


@color_rule_api_app.route('/get_color_rules/<uuid:map_id>/')
def get_color_rules(map_id):
    color_rules = db.session.query(ColorRule).filter_by(map_id=map_id)

    data = {"rules": model_to_json(ColorRule, color_rules, ["id"])}

    for color_rule_data in data["rules"]:
        if color_rule_data["type"] == "ID":
            del color_rule_data["origin"]
        else:
            del color_rule_data["block_id"]

    return make_response(jsonify(data))

@color_rule_api_app.route('/get_merged_color_rules/<uuid:merge_id>/')
def get_merged_color_rules(merge_id):
    merge_maps = db.session.query(MergeMap).filter_by(merge_id=merge_id).all()
    rules = []
    for merge_map in merge_maps:
        color_rules = db.session.query(ColorRule).filter_by(map_id=merge_map.map_id).all()
        rules.extend(model_to_json(ColorRule, color_rules, ["id"]))
    data = {"rules": rules}

    for color_rule_data in data["rules"]:
        if color_rule_data["type"] == "ID":
            del color_rule_data["origin"]
        else:
            del color_rule_data["block_id"]
    return make_response(jsonify(data))

@color_rule_api_app.route('/create_color_rule/', methods=["POST"])
def create_color_rule():
    if request.content_type == "application/json":
        try:
            request.json["map_id"]
        except KeyError:
            return make_response('map_id missing'), 400
        try:
            request.json["type"]
        except KeyError:
            return make_response('type missing'), 400
        try:
            request.json["to"]
        except KeyError:
            return make_response('to missing'), 400

        type = request.json["type"]
        if type == "ID":
            try:
                request.json["block_id"]
            except KeyError:
                return make_response('block_id missing'), 400

            block_id = request.json["block_id"]
            to = request.json["to"]
            map_id = request.json["map_id"]
            db.session.add(ColorRule(type=type, block_id=block_id, to=to, map_id=map_id))
        else:
            try:
                request.json["origin"]
            except KeyError:
                return make_response('origin missing'), 400

            origin = request.json["origin"]
            to = request.json["to"]
            map_id = request.json["map_id"]
            db.session.add(ColorRule(type=type, origin=origin, to=to, map_id=map_id))

        try:
            db.session.commit()
        except:
            db.session.rollback()
            return make_response('integrity error'), 500

        return make_response("ok")
    else:
        return make_response('content type must be application/app'), 406
