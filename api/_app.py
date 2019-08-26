import os
from flask import Flask
from settings import DATABASE_URL


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_TYPE'] = 'redis'
app.config['SECRET_KEY'] = os.urandom(24)
