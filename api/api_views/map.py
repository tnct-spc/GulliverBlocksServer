from flask import Blueprint, make_response, jsonify, request
from api.models import Map, RealSense
from api.api_views.parse_help_lib import model_to_json
from api._db import db


map_api_app = Blueprint('map_api_app', __name__)


@map_api_app.route('/get_maps/')
def get_maps():
    maps = db.session.query(Map).all()

    data = {"maps": model_to_json(Map, maps)}

    return make_response(jsonify(data))


@map_api_app.route('/create_map/', methods=["POST"])
def create_map():
    if request.content_type == "application/json":
        try:
            request.json["name"]
            request.json["realsense_id"]
        except KeyError:
            return make_response('name or realsense missing'), 400

        name = request.json["name"]
        new_map = Map(name=name)
        db.session.add(new_map)
        try:
            db.session.commit()
        except:
            db.session.rollback()
            return make_response('integrity error'), 500

        try:
            realsense_id = request.json["realsense_id"]
            realsense = db.session.query(RealSense).filter_by(id=realsense_id).first()
            realsense.current_map_id = new_map.id
            db.session.commit()
        except:
            db.session.rollback()
            return make_response('integrity error'), 500

        map_data = {
            "ID": new_map.id,
            "name": name
        }
        return make_response(jsonify(map_data))
    else:
        return make_response('content type must be application/app'), 406
