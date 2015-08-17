import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.exc import DetachedInstanceError
from mita.models import Base


class Node(Base):

    __tablename__ = 'nodes'
    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False, unique=True, index=True)
    created = Column(DateTime, index=True)
    keyname = Column(String(128))
    image_name = Column(String(128))
    size = Column(String(128))

    def __init__(self, name, keyname, image_name, size, labels=None, **kw):
        self.name = name
        self.keyname = keyname
        self.image_name = image_name
        self.size = size
        self.created = datetime.datetime.utcnow()
        if labels:
            for l in labels:
                Label(self, l)

    def __repr__(self):
        try:
            return '<Node %r>' % self.name
        except DetachedInstanceError:
            return '<Node detached>'


class Label(Base):

    __tablename__ = 'labels'
    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False, unique=True, index=True)
    node_id = Column(Integer, ForeignKey('nodes.id'))
    node = relationship('Node', backref=backref('labels', lazy='dynamic'))

    def __init__(self, node, name):
        self.node = node
        self.name = name

    def __repr__(self):
        try:
            return '<Label %r>' % self.name
        except DetachedInstanceError:
            return '<Label detached>'
