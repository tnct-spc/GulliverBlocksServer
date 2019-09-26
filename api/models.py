from api._db import db
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from werkzeug.security import generate_password_hash, check_password_hash


class Block(db.Model):
    id = db.Column(UUID(as_uuid=True), default=uuid4, primary_key=True)
    x = db.Column(db.Integer, nullable=False)
    y = db.Column(db.Integer, nullable=False)
    z = db.Column(db.Integer, nullable=False)
    time = db.Column(db.Float, nullable=False)
    colorID = db.Column(db.String, nullable=False)
    map_id = db.Column(UUID(as_uuid=True), db.ForeignKey('map.id'), nullable=False)
    pattern_name = db.Column(db.String, db.ForeignKey('pattern.name'), nullable=True)
    pattern_group_id = db.Column(UUID(as_uuid=True), nullable=True)

    color_rule = db.relationship('ColorRule', backref='block', lazy=True)

    def __repr__(self):
        return "<Block(map_id='%s')>" % self.map_id


class Map(db.Model):
    id = db.Column(UUID(as_uuid=True), default=uuid4, primary_key=True)
    name = db.Column(db.String, nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False)

    block = db.relationship('Block', backref='map', lazy=True)
    merge_map = db.relationship('MergeMap', backref='map', lazy=True)
    real_sense = db.relationship('RealSense', backref='map', lazy=True)
    color_rule = db.relationship('ColorRule', backref='map', lazy=True)

    def __repr__(self):
        return "<Map(name='%s')>" % self.name


class RealSense(db.Model):
    id = db.Column(UUID(as_uuid=True), default=uuid4, primary_key=True)
    name = db.Column(db.String, nullable=False)
    current_map_id = db.Column(UUID(as_uuid=True), db.ForeignKey('map.id'), nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return "<Realsense(name='%s')>" % self.name


class Merge(db.Model):
    id = db.Column(UUID(as_uuid=True), default=uuid4, primary_key=True)
    name = db.Column(db.String, nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False)

    merge_map = db.relationship('MergeMap', backref='merge', lazy=True)

    def __repr__(self):
        return "<Merge(name='%s')>" % self.name


class MergeMap(db.Model):
    id = db.Column(UUID(as_uuid=True), default=uuid4, primary_key=True)
    map_id = db.Column(UUID(as_uuid=True), db.ForeignKey('map.id'), nullable=False)
    merge_id = db.Column(UUID(as_uuid=True), db.ForeignKey('merge.id'), nullable=False)
    x = db.Column(db.Integer, nullable=False)
    y = db.Column(db.Integer, nullable=False)
    rotate = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return "<MergeMap(merge_id='%s', map_id='%s')>" % (self.merge_id, self.map_id)


class ColorRule(db.Model):
    id = db.Column(UUID(as_uuid=True), default=uuid4, primary_key=True)
    map_id = db.Column(UUID(as_uuid=True), db.ForeignKey('map.id'), nullable=False)
    type = db.Column(db.String, nullable=False)
    block_id = db.Column(UUID(as_uuid=True), db.ForeignKey('block.id'), nullable=True)
    origin = db.Column(db.String, nullable=True)
    to = db.Column(db.String, nullable=False)

    def __repr__(self):
        return "<ColorRule(map_id='%s', type='%s')>" % (self.map_id, self.type)


class Pattern(db.Model):
    __tablename__ = 'pattern'
    id = db.Column(UUID(as_uuid=True), default=uuid4, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    extend_to_right = db.Column(db.Boolean, nullable=False)
    extend_to_left = db.Column(db.Boolean, nullable=False)
    extend_to_top = db.Column(db.Boolean, nullable=False)
    extend_to_bottom = db.Column(db.Boolean, nullable=False)
    
    block = db.relationship('Block', backref='pattern', lazy=True)
    pattern_block = db.relationship('PatternBlock', backref='pattern', lazy=True)

    def __repr__(self):
        return "<Pattern(name='%s')>" % self.name


class PatternBlock(db.Model):
    __tablename__ = 'pattern_block'
    id = db.Column(UUID(as_uuid=True), default=uuid4, primary_key=True)
    x = db.Column(db.Integer, nullable=False)
    y = db.Column(db.Integer, nullable=False)
    z = db.Column(db.Integer, nullable=False)
    colorID = db.Column(db.String, nullable=False)
    pattern_id = db.Column(UUID(as_uuid=True), db.ForeignKey('pattern.id'), nullable=False)

    def __repr__(self):
        return "<PatternBlock(pattern_id='%s')>" % self.pattern_id


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(UUID(as_uuid=True), default=uuid4, primary_key=True)
    username = db.Column(db.String, nullable=False)
    password_hash = db.Column(db.String, nullable=False)

    map = db.relationship('Map', backref='user', lazy=True)
    realsense = db.relationship('RealSense', backref='user', lazy=True)
    merge = db.relationship('Merge', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def auth_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return "<User(username='%s')>" % self.username
