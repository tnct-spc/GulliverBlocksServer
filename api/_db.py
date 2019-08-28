from flask_sqlalchemy import SQLAlchemy
from api._app import app


db = SQLAlchemy(app)