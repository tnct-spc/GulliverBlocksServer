from flask_sockets import Sockets 
from ._app import app

sockets = Sockets(app)
