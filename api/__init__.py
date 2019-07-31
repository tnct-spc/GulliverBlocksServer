from api._app import app
from api._socket import sockets
from .views import api_app
from bugsnag.flask import handle_exceptions


app.register_blueprint(api_app)

sockets.init_app(app)

# bugsnag handle
handle_exceptions(app)
