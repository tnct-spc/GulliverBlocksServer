from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from uuid import uuid4


Base = declarative_base()

class Block(Base):
    __tablename__  = 'block'
    id = Column(UUID(as_uuid=True), default=uuid4, primary_key=True)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    z = Column(Integer, nullable=False)
    time = Column(Float, nullable=False)
    colorID = Column(String, nullable=False)
    map_id = Column(UUID(as_uuid=True), ForeignKey('map.id'), nullable=False)

    color_rule = relationship('ColorRule', backref='block', lazy=True)
    def __repr__(self):
        return "<Block(map_id='%s')>" % (self.map_id)


class Map(Base):
    __tablename__ = 'map'
    id = Column(UUID(as_uuid=True), default=uuid4, primary_key=True)
    name = Column(String, nullable=False)

    block = relationship('Block', backref='map', lazy=True)
    merge_map = relationship('MergeMap', backref='map', lazy=True)
    real_sense = relationship('RealSense', backref='map', lazy=True)
    color_rule = relationship('ColorRule', backref='map', lazy=True)
    def __repr__(self):
        return "<Map(name='%s')>" % (self.name)


class RealSense(Base):
    __tablename__ = 'real_sense'
    id = Column(UUID(as_uuid=True), default=uuid4, primary_key=True)
    name = Column(String, nullable=False)
    current_map_id = Column(UUID(as_uuid=True), ForeignKey('map.id'), nullable=False)
    def __repr__(self):
        return "<Realsense(name='%s')>" % (self.name)


class Merge(Base):
    __tablename__ = 'merge'
    id = Column(UUID(as_uuid=True), default=uuid4, primary_key=True)
    name = Column(String, nullable=False)
    def __repr__(self):
        return "<Merge(name='%s')>" % (self.name)


class MergeMap(Base):
    __tablename__ = 'merge_map'
    id = Column(UUID(as_uuid=True), default=uuid4, primary_key=True)
    map_id = Column(UUID(as_uuid=True), ForeignKey('map.id'), nullable=False)
    merge_id = Column(UUID(as_uuid=True), ForeignKey('merge.id'), nullable=False)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    rotate = Column(Integer, nullable=False)
    def __repr__(self):
        return "<MergeMap(merge_id='%s', map_id='%s')>" % (self.merge_id, self.map_id)


class ColorRule(Base):
    __tablename__ = 'color_rule'
    id = Column(UUID(as_uuid=True), default=uuid4, primary_key=True)
    map_id = Column(UUID(as_uuid=True), ForeignKey('map.id'), nullable=False)
    type = Column(String, nullable=False)
    block_id = Column(UUID(as_uuid=True), ForeignKey('block.id'), nullable=True)
    origin = Column(String, nullable=True)
    to = Column(String, nullable=False)
    def __repr__(self):
        return "<ColorRule(map_id='%s', type='%s')>" % (self.name, self.type)
