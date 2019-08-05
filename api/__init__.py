from api._app import app
from api._socket import sockets
from .views import api_app
from .websocket import ws
from bugsnag.flask import handle_exceptions
from flask_migrate import Migrate
from api._db import db


app.register_blueprint(api_app)
sockets.register_blueprint(ws)
Migrate(app, db)


# bugsnag handle
handle_exceptions(app)
