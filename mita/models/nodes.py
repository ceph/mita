import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.exc import DetachedInstanceError
from mita.models import Base
from mita.util import get_jenkins_name


class Node(Base):

    __tablename__ = 'nodes'
    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False, index=True)
    created = Column(DateTime, index=True)
    keyname = Column(String(128))
    image_name = Column(String(128))
    size = Column(String(128))
    identifier = Column(String(128), nullable=False, unique=True, index=True)
    idle_since = Column(DateTime)

    def __init__(self, name, keyname, image_name, size, identifier, labels=None, **kw):
        self.name = name
        self.keyname = keyname
        self.image_name = image_name
        self.size = size
        self.identifier = identifier
        self.created = datetime.datetime.utcnow()
        self.idle_since = None
        if labels:
            for l in labels:
                Label(self, l)

    def labels_match(self, labels):
        """
        Get a list of labels and see if this Node has them all
        Returns a boolean
        """
        for l in self.labels:
            if l.name not in labels:
                return False
        return True

    @property
    def cloud_name(self):
        return u'%s__%s' % (self.name, self.identifier)

    @property
    def jenkins_name(self):
        if not hasattr(self, "_jenkins_name"):
            self._jenkins_name = get_jenkins_name(self.identifier)
        return self._jenkins_name

    @property
    def idle(self):
        return bool(self.idle_since)

    def __repr__(self):
        try:
            return '<Node %r>' % self.name
        except DetachedInstanceError:
            return '<Node detached>'


class Label(Base):

    __tablename__ = 'labels'
    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False, index=True)
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
