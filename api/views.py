from flask import Blueprint, make_response, jsonify, request
from api.models import Block, Map, RealSense, ColorRule, Merge, MergeMap
from api._db import db
from api._redis import redis_connection
import json
import time
from math import sin, cos, radians


api_app = Blueprint('api_app', __name__)


@api_app.route('/debug_add_blocks/<uuid:map_id>/', methods=["POST"])
def add_block_for_debug(map_id):
    """
    postされたものをそのままwebsocketに流すコード, debug用
    """
    data = {
        'message': request.json,
        'map_id': str(map_id)
    }
    redis_connection.publish('received_message', json.dumps(data))
    return make_response('ok')


@api_app.route('/add_blocks/<uuid:realsense_id>/', methods=["POST"])
def add_block(realsense_id):
    """
    blockを追加/削除するapi
    """
    if db.session.query(RealSense).filter_by(id=realsense_id).count() <= 0:
        return make_response('the realsense is not exists.'), 400
    map_id = db.session.query(RealSense).filter_by(id=realsense_id).first().current_map_id

    # blockのvalidate
    try:
        blocks = request.json['blocks']
    except KeyError:
        return make_response('blocks parameter missing'), 400
    put_blocks = []
    delete_blocks = []
    for block in blocks:
        try:
            is_put = block['put']
            block['x']
            block['y']
            block['z']
        except KeyError:
            return make_response('put, x, y or z missing'), 400
        if is_put:
            try:
                block['colorID']
            except KeyError:
                return make_response('colorID missing'), 400
            put_blocks.append(block)
        else:
            delete_blocks.append(block)

    deleted_block_ids = []
    for b in delete_blocks:
        block_object = db.session.query(Block).filter_by(x=b['x'], y=b['y'], z=b['z']).first()
        deleted_block_ids.append(block_object.id)
        db.session.delete(block_object)
    put_block_objects = [
        Block(
            x=b['x'],
            y=b['y'],
            z=b['z'],
            time=time.time(),
            colorID=b['colorID'],
            map_id=map_id
        )for b in put_blocks
    ]
    db.session.bulk_save_objects(put_block_objects, return_defaults=True)

    try:
        db.session.commit()
    except:
        return make_response('integrity error'), 500

    # websocket 配信
    message = {
        'blocks': []
    }
    message['blocks'].extend([{
        'put': False,
        'ID': str(block_id)
        } for block_id in deleted_block_ids])
    message['blocks'].extend([{
            "put": True,
            "ID": str(block.id),
            "colorID": block.colorID,
            "time": block.time,
            "x": block.x,
            "y": block.y,
            "z": block.z
        } for block in put_block_objects])
    data = {
        'message': message,
        'map_id': str(map_id)
    }
    redis_connection.publish('received_message', json.dumps(data))
    return make_response('ok')


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
    maps_data = {
        "maps": []
    }
    for map in maps:
        tmp_dic = {
            "ID": map.id,
            "name": map.name
        }
        maps_data["maps"].append(tmp_dic)

    return make_response(jsonify(maps_data))


@api_app.route('/create_map/', methods=["POST"])
def create_map():
    if request.content_type == "application/json":
        try:
            request.json["name"]
        except KeyError:
            return make_response('name missing'), 400

        name = request.json["name"]
        new_map = Map(name=name)
        db.session.add(new_map)
        try:
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


@api_app.route('/get_color_rules/<uuid:map_id>/')
def get_color_rules(map_id):
    color_rules = db.session.query(ColorRule).filter_by(map_id=map_id)
    data = {
        "rules": []
    }
    for rule in color_rules:
        if rule.type == "ID":
           data["rules"].append({
                "type": rule.type,
                "block_id": rule.block_id,
                "to": rule.to,
                "map_id": rule.map_id
           })
        else:
            data["rules"].append({
                "type": rule.type,
                "origin": rule.origin,
                "to": rule.to,
                "map_id": rule.map_id
            })
    return make_response(jsonify(data))


@api_app.route('/create_color_rule/', methods=["POST"])
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


@api_app.route('/get_merges/')
def get_merges():
    merges = db.session.query(Merge)
    data = {
        "merges": []
    }
    for merge in merges:
        data["merges"].append({
            "ID": merge.id,
            "name": merge.name
        })
    return make_response(jsonify(data))


@api_app.route('/create_merge/', methods=["POST"])
def create_merge():
    if request.content_type == "application/json":
        try:
            request.json["name"]
        except KeyError:
            return make_response('name missing'), 400

        db.session.add(Merge(name=request.json["name"]))
        try:
            db.session.commit()
        except:
            db.session.rollback()
            return make_response('integrity error'), 500

        return make_response('ok')
    else:
        return make_response('content type must be application/json'), 406


@api_app.route('/get_merge_maps/<uuid:merge_id>/')
def get_merge_maps(merge_id):
    merge_maps = db.session.query(MergeMap).filter_by(merge_id=merge_id)
    data = {
        "merge_maps": []
    }
    for merge_map in merge_maps:
        data["merge_maps"].append({
            "map_id": merge_map.map_id,
            "x": merge_map.x,
            "y": merge_map.y,
            "rotate": merge_map.rotate
        })
    return make_response(jsonify(data))


@api_app.route('/create_merge_map/', methods=["POST"])
def create_merge_map():
    if request.content_type == "application/json":
        try:
            request.json["merge_maps"]
        except KeyError:
            return make_response('merge_map data missing'), 400
        try:
            request.json["merge_id"]
        except KeyError:
            return make_response('merge_id missing'), 400

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
                    merge_id=request.json["merge_id"],
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


@api_app.route('/get_merged_map/<uuid:merge_id>/')
def get_merged_map(merge_id):
    merge_maps = db.session.query(MergeMap).filter_by(merge_id=merge_id)
    merged_blocks = []

    for merge_map in merge_maps:
        _map = db.session.query(Map).get(merge_map.map_id)
        blocks = db.session.query(Block).filter_by(map_id=_map.id)
        for block in blocks:
            """
            ブロックの座標移動処理
            """
            rad = radians(90*merge_map.rotate)
            tmp_x = block.x
            tmp_y = block.y
            block.x = round(tmp_x*cos(rad) - tmp_y*sin(rad))
            block.y = round(tmp_y*cos(rad) + tmp_x*sin(rad))

            block.x += merge_map.x
            block.y += merge_map.y

            merged_blocks.append(block)

    data = {
        "blocks": []
    }
    for merged_block in merged_blocks:
        data["blocks"].append({
            "ID": merged_block.id,
            "colorID": merged_block.colorID,
            "time": merged_block.time,
            "x": merged_block.x,
            "y": merged_block.y,
            "z": merged_block.z
        })

    return make_response(jsonify(data))


@api_app.route('/get_realsenses/')
def get_realsense():
    realsenses = db.session.query(RealSense)
    data = {
        "realsenses": []
    }
    for realsense in realsenses:
        data["realsenses"].append({
            "ID": realsense.id,
            "name": realsense.name
        })
    return make_response(jsonify(data))


@api_app.route('/create_realsense/', methods=["POST"])
def create_realsense():
    if request.content_type == "application/json":
        try:
            request.json["name"]
        except KeyError:
            return make_response('name missing'), 400
        try:
            request.json["current_map_id"]
        except KeyError:
            return make_response('current_map_id missing'), 400

        realsense = RealSense(name=request.json["name"], current_map_id=request.json["current_map_id"])
        db.session.add(realsense)
        try:
            db.session.commit()
        except:
            db.session.rollback()
            return make_response('integrity error'), 500

        return make_response("ok")
    else:
        return make_response('content type must be application/app'), 406
