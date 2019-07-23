from api._db import db
from datetime import datetime


class Block(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    block_id = db.Column(db.Integer, nullable=False)
    x = db.Column(db.Float, nullable=False)
    y = db.Column(db.Float, nullable=False)
    z = db.Column(db.Float, nullable=False)
    time = db.Column(db.Float, nullable=False)
    colorID = db.Column(db.Integer, nullable=False)
    put = db.Column(db.Boolean, nullable=False)
