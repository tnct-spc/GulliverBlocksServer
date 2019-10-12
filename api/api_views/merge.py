from flask import Blueprint, make_response, jsonify, request
from api.models import Merge, MergeMap, Block, ViewRight
from api.api_views.parse_help_lib import model_to_json
from api._db import db
from math import sin, cos, radians
import copy
from api.api_views.user import login_required


merge_api_app = Blueprint('merge_api_app', __name__)


@merge_api_app.route('/get_merges/')
@login_required
def get_merges(user):
    merges = db.session.query(Merge).filter_by(user_id=user.id).all()
    data = {"merges": model_to_json(Merge, merges, ["user_id"])}

    view_rights = db.session.query(ViewRight).filter_by(user_id=user.id).all()
    share_merges = []
    for view_right in view_rights:
        share_merge = db.session.query(Merge).filter_by(id=view_right.map_or_merge_id).first()
        if share_merge:
            share_merges.append(share_merge)
    data["merges"].extend(model_to_json(Merge, share_merges, ["user_id"]))

    return make_response(jsonify(data))


@merge_api_app.route('/get_merge_maps/<uuid:merge_id>/')
def get_merge_maps(merge_id):
    merge_maps = db.session.query(MergeMap).filter_by(merge_id=merge_id)

    data = {"merge_maps": model_to_json(MergeMap, merge_maps, ["id", "merge_id"])}

    return make_response(jsonify(data))


@merge_api_app.route('/get_merged_blocks/<uuid:merge_id>/')
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


@merge_api_app.route('/create_merge/', methods=["POST"])
@login_required
def create_merge(user):
    if request.content_type == "application/json":
        try:
            request.json["name"]
            request.json["merge_maps"]
        except KeyError:
            return make_response('name or merge_maps missing'), 400

        new_merge = Merge(name=request.json["name"], user_id=user.id)
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

@merge_api_app.route('/update_merge/', methods=["POST"])
def update_merge():
    if request.content_type != "application/json":
        return make_response('content type must be application/json'), 406
    try:
        name = request.json["name"]
        world_id = request.json["ID"]
    except KeyError:
        return make_response('name or WorldId missing'), 400
    db.session.query(Merge).filter_by(id=world_id).first().name = name
    db.session.commit()
    return make_response('ok')

@merge_api_app.route('/del_merge/', methods=["post"])
def del_merge():
    if request.content_type != "application/json":
        return make_response('content type must be application/json'), 406
    try:
        merge_id = request.json["ID"]
    except KeyError:
        return make_response('Mergeid missing'), 400
    merge = db.session.query(Merge).filter_by(id=merge_id).first()
    db.session.delete(merge)
    db.session.commit()
    return make_response('ok')