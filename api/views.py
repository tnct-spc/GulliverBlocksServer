from flask import Blueprint, make_response, jsonify, request, abort
from api.models import Block, Map, RealSense
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
        return make_response('the realsese is not e3xsist'), 400
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
        return abort(406)
