from flask import Flask
from .views import api_app
from bugsnag.flask import handle_exceptions


app = Flask(__name__)
app.register_blueprint(api_app)
handle_exceptions(app)
