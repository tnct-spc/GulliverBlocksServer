from flask import Blueprint, make_response, jsonify, request
from api.models import Map, RealSense, ColorRule, Merge, MergeMap
from api._db import db


create_api_app = Blueprint('create_api_app', __name__)


@create_api_app.route('/create_map/', methods=["POST"])
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


@create_api_app.route('/create_color_rule/', methods=["POST"])
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


@create_api_app.route('/create_merge/', methods=["POST"])
def create_merge():
    if request.content_type == "application/json":
        try:
            request.json["name"]
            request.json["merge_maps"]
        except KeyError:
            return make_response('name or merge_maps missing'), 400

        new_merge = Merge(name=request.json["name"])
        db.session.add(new_merge)
        try:
            db.session.commit()
        except:
            db.session.rollback()
            return make_response('integrity error'), 500

        merge_id = new_merge.id
        merge_maps = request.json["merge_maps"]
        merge_map_objects = []
        for merge_map_data in merge_maps:
            try:
                merge_map_data["map_id"]
            except KeyError:
                return make_response('map_id missing'), 400
            try:
                merge_map_data["x"]
                merge_map_data["y"]
            except KeyError:
                return make_response('x or y missing'), 400
            try:
                merge_map_data["rotate"]
            except KeyError:
                return make_response('rotate missing'), 400

            merge_map_objects.append(
                MergeMap(
                    map_id=merge_map_data["map_id"],
                    merge_id=merge_id,
                    x=merge_map_data["x"],
                    y=merge_map_data["y"],
                    rotate=merge_map_data["rotate"]
                )
            )
        db.session.bulk_save_objects(merge_map_objects, return_defaults=True)
        try:
            db.session.commit()
        except:
            db.session.rollback()
            return make_response('integrity error'), 500

        return make_response('ok')
    else:
        return make_response('content type must be application/json'), 406
