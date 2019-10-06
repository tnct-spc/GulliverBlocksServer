from flask import Blueprint, make_response, jsonify, request
from api.models import Map, RealSense, ViewRight
from api.api_views.parse_help_lib import model_to_json
from api._db import db
from api.api_views.user import login_required


map_api_app = Blueprint('map_api_app', __name__)


@map_api_app.route('/get_maps/')
@login_required
def get_maps(user):
    maps = db.session.query(Map).filter_by(user_id=user.id).all()
    data = {"maps": model_to_json(Map, maps, ["user_id"])}

    view_rights = db.session.query(ViewRight).filter_by(user_id=user.id).all()
    share_maps = []
    for view_right in view_rights:
        share_map = db.session.query(Map).filter_by(id=view_right.map_or_merge_id).first()
        if share_map:
            share_maps.append(share_map)
    data["maps"].extend(model_to_json(Map, share_maps, ["user_id"]))

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

@map_api_app.route('/update_map/', methods=["POST"])
def update_merge():
    if request.content_type != "application/json":
        return make_response('content type must be application/json'), 406
    try:
        name = request.json["name"]
        world_id = request.json["WorldId"]
    except KeyError:
        return make_response('name or WorldId missing'), 400
    db.session.query(Map).filter_by(id=world_id).first().name = name
    db.session.commit()
    return make_response('ok')

