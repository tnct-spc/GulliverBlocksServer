from api._db import db
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4


class Block(db.Model):
    id = db.Column(UUID(as_uuid=True), default=uuid4, primary_key=True)
    x = db.Column(db.Float, nullable=False)
    y = db.Column(db.Float, nullable=False)
    z = db.Column(db.Float, nullable=False)
    time = db.Column(db.Float, nullable=False)
    colorID = db.Column(db.String, nullable=False)
    map_id = db.Column(UUID(as_uuid=True), db.ForeignKey('map.id'), nullable=False)

    color_rule = db.relationship('ColorRule', backref='block', lazy=True)


class Map(db.Model):
    id = db.Column(UUID(as_uuid=True), default=uuid4, primary_key=True)
    name = db.Column(db.String, nullable=False)

    block = db.relationship('Block', backref='map', lazy=True)
    merge_map = db.relationship('MergeMap', backref='map', lazy=True)
    real_sense = db.relationship('RealSense', backref='map', lazy=True)
    color_rule = db.relationship('ColorRule', backref='map', lazy=True)


class RealSense(db.Model):
    id = db.Column(UUID(as_uuid=True), default=uuid4, primary_key=True)
    name = db.Column(db.String, nullable=False)
    current_map_id = db.Column(UUID(as_uuid=True), db.ForeignKey('map.id'), nullable=False)


class Merge(db.Model):
    id = db.Column(UUID(as_uuid=True), default=uuid4, primary_key=True)
    name = db.Column(db.String, nullable=False)


class MergeMap(db.Model):
    id = db.Column(UUID(as_uuid=True), default=uuid4, primary_key=True)
    map_id = db.Column(UUID(as_uuid=True), db.ForeignKey('map.id'), nullable=False)
    merge_id = db.Column(UUID(as_uuid=True), db.ForeignKey('merge.id'), nullable=False)
    x = db.Column(db.Float, nullable=False)
    y = db.Column(db.Float, nullable=False)
    rotate = db.Column(db.Integer, nullable=False)


class ColorRule(db.Model):
    id = db.Column(UUID(as_uuid=True), default=uuid4, primary_key=True)
    map_id = db.Column(UUID(as_uuid=True), db.ForeignKey('map.id'), nullable=False)
    type = db.Column(db.String, nullable=False)
    block_id = db.Column(UUID(as_uuid=True), db.ForeignKey('block.id'), nullable=True)
    origin = db.Column(db.String, nullable=True)
    to = db.Column(db.String, nullable=False)
