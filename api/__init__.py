from flask_migrate import Migrate
from bugsnag.flask import handle_exceptions
import bugsnag
from settings import BUGSNAG_API_KEY, FLASK_ENV
from api._app import app
from api._db import db
from api._socket import sockets
from api.views import api_app
from api.websocket import ws
from api.models import Block, Map, RealSense, MergeMap, Merge, Pattern, PatternBlock, ColorRule
import api.admin


sockets.register_blueprint(ws)

bugsnag.configure(
    api_key=BUGSNAG_API_KEY,
    project_root=".",
    release_stage = FLASK_ENV,
)
handle_exceptions(app)

Migrate(app, db, compare_type=True)

app.register_blueprint(api_app)
