from api._app import app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://localhost/g_test'
db = SQLAlchemy(app)
