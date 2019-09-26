from flask import Blueprint, make_response, jsonify, request
from api.models import RealSense, Map
from api._db import db


realsense_api_app = Blueprint('realsense_api_app', __name__)


@realsense_api_app.route('/get_realsenses/')
def get_realsenses():
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
