from flask import Blueprint, make_response, jsonify, request, session
from api.models import Map, RealSense, User
from api.api_views.parse_help_lib import model_to_json
from api._db import db
from api.api_views.user import login_required


map_api_app = Blueprint('map_api_app', __name__)


@map_api_app.route('/get_maps/')
@login_required
def get_maps(user):
    maps = db.session.query(Map).filter_by(user_id=user.id).all()

    data = {"maps": model_to_json(Map, maps, ["user_id"])}

    return make_response(jsonify(data))


@map_api_app.route('/create_map/', methods=["POST"])
def create_map():
    try:
        user_id = session["user_id"]
    except KeyError:
        return make_response("you are not logged in"), 403
    if request.content_type == "application/json":
        try:
            request.json["name"]
        except KeyError:
            return make_response('name missing'), 400

        name = request.json["name"]
        new_map = Map(name=name, user_id=user_id)
        db.session.add(new_map)
        try:
            db.session.commit()
        except:
            db.session.rollback()
            return make_response('integrity error'), 500

        try:
            realsense = db.session.query(RealSense).first()
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
