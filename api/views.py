from flask import Blueprint, make_response, jsonify, request
from api.models import Block, Map, RealSense, ColorRule, Merge, MergeMap, Pattern, PatternBlock
from api._db import db
from api._redis import redis_connection
import json
import time
from math import sin, cos, radians
import copy
from uuid import uuid4
from threading import Thread


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
        ) for b in put_blocks
    ]
    db.session.bulk_save_objects(put_block_objects, return_defaults=True)

    try:
        db.session.commit()
    except:
        return make_response('integrity error'), 500

    # ブロックのパターン認識を非同期でする
    _blocks = db.session.query(Block).filter_by(map_id=map_id).all()
    thread = Thread(target=recognize_pattern, args=[_blocks])
    thread.start()

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
            changed_block["x"] = round(tmp_x * cos(rad) - tmp_y * sin(rad))
            changed_block["y"] = round(tmp_y * cos(rad) + tmp_x * sin(rad))
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

        new_merge = Merge(name=request.json["name"])
        db.session.add(new_merge)
        try:
            db.session.commit()
        except:
            db.session.rollback()
            return make_response('integrity error'), 500

        return make_response(jsonify({"message": "ok", "merge_id": str(new_merge.id)}))
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
            rad = radians(90 * merge_map.rotate)
            tmp_x = block.x
            tmp_y = block.y
            block.x = round(tmp_x * cos(rad) - tmp_y * sin(rad))
            block.y = round(tmp_y * cos(rad) + tmp_x * sin(rad))

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


@api_app.route("/get_patterns/")
def get_patterns():
    patterns = db.session.query(Pattern).all()
    data = {}
    for pattern in patterns:
        data[pattern.name] = {}
        blocks = db.session.query(Block).filter_by(pattern_name=pattern.name).all()
        for block in blocks:
            if str(block.pattern_group_id) in data[pattern.name].keys():
                data[pattern.name][str(block.pattern_group_id)].append({
                    "ID": str(block.id),
                    "x": block.x,
                    "y": block.y,
                    "z": block.z,
                    "colorID": block.colorID,
                    "time": block.time
                })
            else:
                data[pattern.name][str(block.pattern_group_id)] = [{
                    "ID": str(block.id),
                    "x": block.x,
                    "y": block.y,
                    "z": block.z,
                    "colorID": block.colorID,
                    "time": block.time
                }]
    return make_response(jsonify(data))


def recognize_pattern(blocks):
    """
    patterns sample
    {
        "road": {
            "blocks": [
                {
                    左下のブロックの座標を原点とする
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
    # PatternとPatternBlockを使いやすいように加工する
    _patterns = db.session.query(Pattern).all()
    patterns = {}
    for patten in _patterns:
        patterns[patten.name] = {}
        patterns[patten.name]["blocks"] = db.session.query(PatternBlock).filter_by(pattern_id=patten.id).all()
        patterns[patten.name]["blocks"].sort(key=lambda b: b.x**2 + b.y**2 + b.z**2)

        patterns[patten.name]["extend_directions"] = []
        tmp_pattern_extend_directions = [
            [patten.extend_to_right, "right"],
            [patten.extend_to_left, "left"],
            [patten.extend_to_top, "top"],
            [patten.extend_to_bottom, "bottom"]
        ]
        for tmp_pattern_extend_direction in tmp_pattern_extend_directions:
            if tmp_pattern_extend_direction[0]:
                patterns[patten.name]["extend_directions"].append(tmp_pattern_extend_direction[1])

    """
    あらかじめ色でフィルターをかけて探索するブロックを厳選しておく
    """
    use_color = []
    for pattern_value in patterns.values():
        pattern_blocks = pattern_value.get("blocks")
        for pattern_block in pattern_blocks:
            if pattern_block.colorID not in use_color:
                use_color.append(pattern_block.colorID)
    target_blocks = copy.deepcopy([block for block in blocks if block.colorID in use_color])
    target_blocks.sort(key=lambda _b: _b.x ** 2 + _b.y ** 2 + _b.z ** 2)

    """
    found_patterns sample
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
    found_patterns = {}
    for pattern_name, pattern_value in patterns.items():
        pattern_blocks = pattern_value.get("blocks")
        """
        全探索をする
        ブロックを一つ選び、それを原点のブロックとしたときに
        パターンの各ブロックの相対座標を選んだブロックの絶対座標に足して
        その座標を持ち、パターンと色が同じブロックが存在するか確認する
        """
        used_blocks = []
        for block in target_blocks:
            if block not in used_blocks:
                found_blocks = []
                for index, pattern_block in enumerate(pattern_blocks):
                    found_block = None
                    # 相対座標の原点に設定するので、1個目はcolorIDのみ確認する
                    if index == 0:
                        if block.colorID == pattern_block.colorID:
                            found_block = block
                    # 2個目からはcolorIDに加えて座標も確認する
                    else:
                        for _block in target_blocks:
                            if _block not in used_blocks:
                                is_x_same = block.x + pattern_block.x == _block.x
                                is_y_same = block.y + pattern_block.y == _block.y
                                is_z_same = block.z + pattern_block.z == _block.z
                                is_color_same = pattern_block.colorID == _block.colorID
                                if is_x_same and is_y_same and is_z_same and is_color_same:
                                    found_block = _block
                    if found_block:
                        found_blocks.append(found_block)
                    else:
                        # 条件に当てはまるブロックが見つからなかったら、すぐに次の候補に進む
                        break

                # パターンに一致するブロック群を保存する
                if len(found_blocks) == len(pattern_blocks):
                    if pattern_name in found_patterns.keys():
                        found_patterns[pattern_name].append(found_blocks)
                    else:
                        found_patterns[pattern_name] = [found_blocks]
                    # パターンとして認識したブロックは探索対象から除外する
                    used_blocks.extend(found_blocks)

    """
    merge処理
    """
    for pattern_name, found_pattern_objects in found_patterns.items():
        pattern = patterns.get(pattern_name)
        merged_objects = []
        """
        見つけたパターンに一致するブロック群それぞれにマージできるものがあるか確認する
        """
        for found_pattern_object in found_pattern_objects:
            if found_pattern_object not in [merged_blocks for objects in merged_objects for merged_blocks in objects]:
                tmp_merged_objects = []
                tmp_merged_objects = merge_found_object(
                    pattern=pattern,
                    found_pattern_objects=found_pattern_objects,
                    merge_base_object=found_pattern_object,
                    merged_objects=tmp_merged_objects
                )
                if tmp_merged_objects:
                    merged_objects.append(tmp_merged_objects)
        if merged_objects:
            for objects in merged_objects:
                tmp_blocks = []
                # それぞれのブロックを一つにまとめる
                for blocks in objects:
                    found_patterns[pattern_name].remove(blocks)
                    tmp_blocks.extend(blocks)
                found_patterns[pattern_name].append(tmp_blocks)

    # dbに反映
    for pattern_name, found_objects in found_patterns.items():
        pattern = db.session.query(Pattern).filter_by(name=pattern_name).first()
        for found_blocks in found_objects:
            pattern_group_id = uuid4()
            for found_block in found_blocks:
                found_block.pattern_group_id = pattern_group_id
                found_block.pattern_name = pattern.name
                db.session.add(found_block)
    try:
        db.session.commit()
    except:
        db.session.rollback()
        return make_response('integrity error'), 500

    return found_patterns


# 再帰させるために関数化した
def merge_found_object(pattern, found_pattern_objects, merge_base_object, merged_objects):
    pattern_blocks = pattern.get("blocks")
    extend_directions = pattern.get("extend_directions")
    tmp_pattern_blocks = sorted(pattern_blocks, key=lambda b: b.x, reverse=True)
    pattern_width = tmp_pattern_blocks[0].x + 1
    tmp_pattern_blocks = sorted(pattern_blocks, key=lambda b: b.z, reverse=True)
    pattern_height = tmp_pattern_blocks[0].z + 1

    """
    mergeできるものを全探索する
    """
    can_merge_objects = []
    for found_blocks in found_pattern_objects:
        if found_blocks not in merged_objects:
            x = merge_base_object[0].x
            _x = found_blocks[0].x
            y = merge_base_object[0].y
            _y = found_blocks[0].y
            z = merge_base_object[0].z
            _z = found_blocks[0].z
            for extend_direction in extend_directions:
                if extend_direction == "right":
                    if x + pattern_width == _x and y == _y and z == _z:
                        can_merge_objects.append(found_blocks)
                elif extend_direction == "left":
                    if x - pattern_width == _x and y == _y and z == _z:
                        can_merge_objects.append(found_blocks)
                elif extend_direction == "top":
                    if x == _x and y == _y and z + pattern_height == _z:
                        can_merge_objects.append(found_blocks)
                elif extend_direction == "bottom":
                    if x == _x and y == _y and z - pattern_height == _z:
                        can_merge_objects.append(found_blocks)

    # マージできるものがあればマージリストにいれて、さらに連結部分のマージが可能かどうかも確認する
    if can_merge_objects:
        if not merged_objects:
            merged_objects.append(merge_base_object)
        merged_objects.extend(can_merge_objects)
        for can_merge_object in can_merge_objects:
            merged_objects = merge_found_object(pattern, found_pattern_objects, can_merge_object, merged_objects)

    return merged_objects
