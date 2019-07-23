from api._app import app
from .views import api_app
from bugsnag.flask import handle_exceptions


app.register_blueprint(api_app)

# bugsnag handle
handle_exceptions(app)
