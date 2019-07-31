from flask import Blueprint, make_response, jsonify, request, abort
from api.models import Block, Map
from api._db import db
from api import sockets
import gevent
import redis
import json

redis = redis.from_url('redis://localhost:6379')


api_app = Blueprint('api_app', __name__)
class SocketClients():
    def __init__(self):
        self.clients = {}
        self.pubsub = redis.pubsub()
        self.pubsub.subscribe('received_message')

    def __iter_data(self):
        for data in self.pubsub.listen():
            try:
                json.loads(data.get('data'))
            except:
                continue
            yield json.loads(data.get('data'))

    def register(self, client, map_id):
        if map_id in self.clients:
            self.clients[map_id].append(client)
        else:
            self.clients[map_id] = [client]

    def send(self, client, data, map_id):
        try:
            client.send(str(data))
        except Exception:
            self.clients[map_id].remove(client)

    def run(self):
        for data in self.__iter_data():
            message = data.get('message')
            map_id = data.get('map_id')
            if data and map_id:
                gevent.spawn(self.castForMap, message, map_id)

    def start(self):
        gevent.spawn(self.run)

    def castForMap(self, message, map_id):
        if map_id in self.clients:
            for client in self.clients[map_id]:
                gevent.spawn(self.send, client, message, map_id)

    
socket_clients = SocketClients()

socket_clients.start()

@sockets.route('/receive/<uuid:map_id>/')
def outbox(ws, map_id):
    socket_clients.register(ws, str(map_id))
    while not ws.closed:
        gevent.sleep(0.1)

@api_app.route('/add_blocks/<uuid:map_id>/', methods=["POST"])
def add_block(map_id):
    """
    blockを追加するapi
    TODO: DBへの反映
    現状はwebsocketへの配信しか行っていない
    """
    data = {
        'message': request.json,
        'map_id': str(map_id)
    }
    redis.publish('received_message', json.dumps(data)) 
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
