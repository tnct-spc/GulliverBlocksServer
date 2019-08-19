from flask import Blueprint, make_response, jsonify, request
from api.models import Block, Map, RealSense, ColorRule, Merge, MergeMap
from api._db import db
from api._redis import redis_connection
import json
import time
from math import sin, cos, radians
import copy


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

    # mergeに含まれるブロックが変更されていたらそのデータを配信する
    if db.session.query(MergeMap).filter_by(map_id=map_id).count() > 0:
        merged_blocks_change_streaming(message=message, map_id=map_id)

    return make_response("ok")


def merged_blocks_change_streaming(message, map_id):
    changed_merges = {}
    merge_maps = db.session.query(MergeMap).filter_by(map_id=map_id).all()
    for merge_map in merge_maps:
        merge = db.session.query(Merge).filter_by(id=merge_map.merge_id).first()
        for _changed_block in message["blocks"]:
            """
                ブロックの座標移動処理
            """
            changed_block = copy.deepcopy(_changed_block)
            rad = radians(90 * merge_map.rotate)
            tmp_x = changed_block["x"]
            tmp_y = changed_block["y"]
            changed_block["x"] = round(tmp_x*cos(rad) - tmp_y*sin(rad))
            changed_block["y"] = round(tmp_y*cos(rad) + tmp_x*sin(rad))
            changed_block["x"] += merge_map.x
            changed_block["y"] += merge_map.y

            if merge.id in changed_merges.keys():
                changed_merges[merge.id].append(changed_block)
            else:
                changed_merges[merge.id] = [changed_block]

    for merge_id, blocks in changed_merges.items():
        data = {
            'merge_id': str(merge_id),
            'message': {'blocks': blocks}
        }
        redis_connection.publish('received_message', json.dumps(data))

    return


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


@api_app.route('/get_merged_blocks/<uuid:merge_id>/')
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


@api_app.route("/test/")
def test():
    patterns = {
        "road": {
            "blocks": [
                {
                    "x": 0,
                    "y": 0,
                    "z": 0,
                    "colorID": "white"
                },
                {
                    "x": 1,
                    "y": 0,
                    "z": 0,
                    "colorID": "black"
                },
                {
                    "x": 2,
                    "y": 0,
                    "z": 0,
                    "colorID": "black"
                },
                {
                    "x": 3,
                    "y": 0,
                    "z": 0,
                    "colorID": "white"
                }
            ],
            "extend_directions": [
                "top",
                "bottom"
            ]
        }
    }
    blocks = [
        Block(x=3, y=4, z=3, colorID="white", time=time.time()),
        Block(x=3, y=4, z=4, colorID="white", time=time.time()),
        Block(x=5, y=5, z=3, colorID="white", time=time.time()),
        Block(x=4, y=4, z=3, colorID="black", time=time.time()),
        Block(x=5, y=4, z=3, colorID="black", time=time.time()),
        Block(x=6, y=4, z=3, colorID="white", time=time.time()),

        Block(x=3, y=3, z=3, colorID="white", time=time.time()),
        Block(x=3, y=3, z=4, colorID="white", time=time.time()),
        Block(x=5, y=4, z=3, colorID="white", time=time.time()),
        Block(x=4, y=3, z=3, colorID="black", time=time.time()),
        Block(x=5, y=3, z=3, colorID="black", time=time.time()),
        Block(x=6, y=3, z=3, colorID="white", time=time.time()),

        Block(x=3, y=3, z=4, colorID="white", time=time.time()),
        Block(x=3, y=3, z=5, colorID="white", time=time.time()),
        Block(x=5, y=4, z=4, colorID="white", time=time.time()),
        Block(x=4, y=3, z=4, colorID="black", time=time.time()),
        Block(x=5, y=3, z=4, colorID="black", time=time.time()),
        Block(x=6, y=3, z=4, colorID="white", time=time.time()),

        Block(x=13, y=13, z=13, colorID="white", time=time.time()),
        Block(x=13, y=13, z=14, colorID="white", time=time.time()),
        Block(x=15, y=14, z=13, colorID="white", time=time.time()),
        Block(x=14, y=13, z=13, colorID="black", time=time.time()),
        Block(x=15, y=13, z=13, colorID="black", time=time.time()),
        Block(x=16, y=13, z=13, colorID="white", time=time.time())
    ]
    result = recognize_pattern(patterns, blocks)
    data = {}
    for pattern_name, _blocks in result.items():
        data[pattern_name] = []
        for blocks in _blocks:
            tmp = []
            for block in blocks:
                tmp.append({
                    "x": block.x,
                    "y": block.y,
                    "z": block.z,
                    "colorID": block.colorID
                })
            data[pattern_name].append(tmp)
    return make_response(jsonify(data))


def recognize_pattern(patterns, blocks):
    """
    patterns sample
    {
        "road": {
            "blocks": [
                {
                    左上のブロックの座標を原点とする
                    "x": 0,
                    "y": 0,
                    "z": 0,
                    "colorID": "white"
                },
                {
                    原点からの相対座標
                    "x": 1,
                    "y": 0,
                    "z": 0,
                    "colorID": "black"
                },
                {
                    "x": 2,
                    "y": 0,
                    "z": 0,
                    "colorID": "black"
                },
                {
                    "x": 3,
                    "y": 0,
                    "z": 0,
                    "colorID": "white"
                }
            ],
            "extend_directions": [
                "right",
                "left",
                "top",
                "bottom"
            ]
        }
    }
    """

    # x軸, y軸, z軸の順に若いものから並べていく
    for pattern_value in patterns.values():
        pattern_blocks = pattern_value.get("blocks")
        pattern_blocks.sort(key=lambda b: (b["z"], b["y"], b["x"]))

    """
    あらかじめ色でフィルターをかけて探索するブロックを厳選しておく
    """
    use_color = []
    for pattern_value in patterns.values():
        pattern_blocks = pattern_value.get("blocks")
        for pattern_block in pattern_blocks:
            if pattern_block.get("colorID") not in use_color:
                use_color.append(pattern_block.get("colorID"))
    target_blocks = [block for block in blocks if block.colorID in use_color]
    target_blocks.sort(key=lambda b: (b.z, b.y, b.x))

    """
    found_objects sample
    {
        "road": [
            [
                {block},
                {block},
                {block}
            ],
            [
                {block},
                {block},
                {block}
            ]
        ]
    }
    """
    found_objects = {}
    for pattern_name, pattern_value in patterns.items():
        pattern_blocks = pattern_value.get("blocks")
        """
        全探索をする
        """
        for b_index in range(len(target_blocks)):
            tmp_block_keeper = []
            """
            パターンに一致するか確認する 一致しないブロックがあればその時点で次のブロックに移行する
            """
            for ((p_index, pattern_block), block) in zip(enumerate(pattern_blocks), target_blocks[b_index:]):
                # 1個目はcolorIDのみを確認する(最初のブロックの相対座標は原点に設定されているので)
                if p_index == 0:
                    if not block.colorID == pattern_block.get("colorID"):
                        break
                # 1個目以降はcolorIDに加えて座標も確認する
                elif block.colorID == pattern_block.get("colorID"):
                    is_x_same = pattern_block.get("x") - pattern_blocks[p_index-1].get("x") == block.x - last_block.x
                    is_y_same = pattern_block.get("y") - pattern_blocks[p_index-1].get("y") == block.y - last_block.y
                    is_z_same = pattern_block.get("z") - pattern_blocks[p_index-1].get("z") == block.z - last_block.z
                    if not (is_x_same and is_y_same and is_z_same):
                        break
                else:
                    break

                last_block = block
                tmp_block_keeper.append(block)

                if p_index == len(pattern_blocks)-1:
                    if pattern_name in found_objects.keys():
                        found_objects[pattern_name].append(tmp_block_keeper)
                    else:
                        found_objects[pattern_name] = [tmp_block_keeper]

    """
    mergeできるものがあればする
    """
    for pattern_name, found_object in found_objects.items():
        pattern = patterns.get(pattern_name)
        pattern_blocks = pattern.get("blocks")
        extend_directions = pattern.get("extend_directions")
        tmp_pattern_blocks = sorted(pattern_blocks, key=lambda b: b["x"], reverse=True)
        pattern_width = tmp_pattern_blocks[0].get("x") + 1
        tmp_pattern_blocks = sorted(pattern_blocks, key=lambda b: b["z"], reverse=True)
        pattern_height = tmp_pattern_blocks[0].get("z") + 1

        """
        mergeできるものを全探索する
        """
        for extend_direction in extend_directions:
            for index in range(len(found_object)-1):
                for found_blocks in found_object[index+1:]:
                    x = found_object[index][0].x
                    _x = found_blocks[0].x
                    y = found_object[index][0].y
                    _y = found_blocks[0].y
                    z = found_object[index][0].z
                    _z = found_blocks[0].z

                    if extend_direction == "right":
                        if x+pattern_width == _x and y == _y and z == _z:
                            found_object[index].extend(found_blocks)
                            found_object.remove(found_blocks)
                    elif extend_direction == "left":
                        if x-pattern_width == _x and y == _y and z == _z:
                            found_object[index].extend(found_blocks)
                            found_object.remove(found_blocks)
                    elif extend_direction == "top":
                        if x == _x and y == _y and z+pattern_height == _z:
                            found_object[index].extend(found_blocks)
                            found_object.remove(found_blocks)
                    elif extend_direction == "bottom":
                        if x == _x and y == _y and z-pattern_height == _z:
                            found_object[index].extend(found_blocks)
                            found_object.remove(found_blocks)

    return found_objects
