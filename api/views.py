from flask import Blueprint, make_response, jsonify, request, abort
from api.models import Block, Map
from api._db import db
from api import sockets
import gevent


api_app = Blueprint('api_app', __name__)
class SocketClients():
    def __init__(self):
        self.clients = {}

    def register(self, client, map_id):
        if map_id in self.clients:
            self.clients[map_id].append(client)
        else:
            self.clients[map_id] = [client]

    def send(self, client, data, map_id):
        try:
            client.send(data)
        except Exception:
            self.clients[map_id].remove(client)

    def castForMap(self, message, map_id):
        if map_id in self.clients:
            for client in self.clients[map_id]:
                gevent.spawn(self.send, client, message, map_id)

    
socket_clients = SocketClients()

@sockets.route('/receive/<uuid:map_id>/')
def outbox(ws, map_id):
    socket_clients.register(ws, map_id)
    while not ws.closed:
        gevent.sleep(0.1)

@api_app.route('/add_blocks/<uuid:map_id>/', methods=["POST"])
def add_block(map_id):
    """
    blockを追加するapi
    TODO: DBへの反映
    現状はwebsocketへの配信しか行っていない
    """
    socket_clients.castForMap(str(request.json), map_id)
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
