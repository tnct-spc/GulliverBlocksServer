from api._app import app
from flask_sqlalchemy import SQLAlchemy
from settings import DATABASE_URI


app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
db = SQLAlchemy(app)
