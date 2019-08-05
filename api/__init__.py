from api._app import app
from api._socket import sockets
from .views import api_app
from .websocket import ws

app.register_blueprint(api_app)
sockets.register_blueprint(ws)

