import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy_utils import ScalarListType
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

    labels = Column(ScalarListType())

    def __init__(self, name, keyname, image_name, size):
        self.name = name
        self.keyname = keyname
        self.image_name = image_name
        self.size = size
        self.created = datetime.datetime.utcnow()

    def __repr__(self):
        try:
            return '<Node %r>' % self.name
        except DetachedInstanceError:
            return '<Node detached>'
