from flask import Flask
from .views import api_app


app = Flask(__name__)
app.register_blueprint(api_app)

