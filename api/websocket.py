from flask import Blueprint
from api._redis import redis_connection
import gevent
import redis
import json


ws = Blueprint('websocket_app', __name__)


class SocketClients():
    def __init__(self):
        self.clients = {}
        self.pubsub = redis_connection.pubsub()
        self.pubsub.subscribe('received_message')

    def __iter_data(self):
        for data in self.pubsub.listen():
            try:
                json.loads(data.get('data'))
            except:
                continue
            yield json.loads(data.get('data'))

    def register(self, client, uuid):
        if uuid in self.clients:
            self.clients[uuid].append(client)
        else:
            self.clients[uuid] = [client]

    def send(self, client, data, uuid):
        try:
            client.send(str(data))
        except Exception:
            self.clients[uuid].remove(client)

    def run(self):
        for data in self.__iter_data():
            message = data.get('message')
            map_id = data.get('map_id')
            merge_id = data.get('merge_id')
            if data and map_id:
                gevent.spawn(self.castForMap, message, map_id)
            elif data and merge_id:
                gevent.spawn(self.castForMerge, message, merge_id)

    def start(self):
        gevent.spawn(self.run)

    def castForMap(self, message, map_id):
        if map_id in self.clients:
            for client in self.clients[map_id]:
                gevent.spawn(self.send, client, message, map_id)

    def castForMerge(self, message, merge_id):
        if merge_id in self.clients:
            for client in self.clients[merge_id]:
                gevent.spawn(self.send, client, message, merge_id)

    
socket_clients = SocketClients()
socket_clients.start()


@ws.route('/receive/<uuid:uuid>/')
def outbox(ws, uuid):
    socket_clients.register(ws, str(uuid))
    while not ws.closed:
        gevent.sleep(0.1)
