from flask_migrate import Migrate
from api._app import app
from api._db import db
from api._socket import sockets
from api.websocket import ws
from api.models import Block, Map, RealSense, MergeMap, Merge, Pattern, PatternBlock, ColorRule
import api.admin
from api.api_views.map import map_api_app
from api.api_views.block import block_api_app
from api.api_views.realsense import realsense_api_app
from api.api_views.color_rule import color_rule_api_app
from api.api_views.merge import merge_api_app


api_apps = [
    map_api_app,
    block_api_app,
    realsense_api_app,
    color_rule_api_app,
    merge_api_app
]

for api_app in api_apps:
    app.register_blueprint(api_app)
sockets.register_blueprint(ws)

Migrate(app, db, compare_type=True)
