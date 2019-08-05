from flask import Blueprint, make_response, jsonify, request, abort
from api.models import Block, Map, RealSense, ColorRule
from api._db import db
from api._redis import redis_connection
import json
import time



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
        block_object = db.session.query(Block).filter_by(x = b['x'], y=b['y'], z=b['z']).first()
        deleted_block_ids.append(block_object.id)
        db.session.delete(block_object)
    put_block_objects = [Block(x=b['x'], y=b['y'], z=b['z'], time=time.time(), colorID=b['colorID'], map_id=map_id) for b in put_blocks]
    db.session.bulk_save_objects(put_block_objects, return_defaults = True)

    try:
        db.session.commit()
    except:
        return make_response('integrity error'), 500

    # websocket 配信
    message = {}
    message['blocks'] = []
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


@api_app.route('/create_map/', methods=["POST"])
def create_map():
    if request.content_type == "application/json":
        name = request.json["name"]  # request.jsonにはcontent_typeがapplication/jsonのときにしかデータが入らない
        new_map = Map(name=name)
        db.session.add(new_map)
        try:
            db.session.commit()
        except:
            db.session.rollback()
            return abort(500)

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
            db.session.roleback()
            return make_response('integrity error'), 500

        return make_response("ok")
    else:
        return make_response('content type must be application/app'), 406
