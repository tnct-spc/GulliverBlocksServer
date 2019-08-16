from flask_migrate import Migrate
from api._app import app
from api._socket import sockets
from api.views import api_app
from api.websocket import ws
from api._db import db


app.register_blueprint(api_app)
sockets.register_blueprint(ws)

Migrate(app, db, compare_type=True)
