from api._app import app
from .views import api_app


app.register_blueprint(api_app)
