# -*- coding: utf-8 -*-
"""
Simple backend for the temporary storage of meshes.
"""

import json

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.schema import MetaData
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship
from sqlalchemy.exc import DataError

Base = declarative_base()


class Job(Base):
    __tablename__ = 'job'
    id = Column(Integer, primary_key=True)
    timestamp = Column(Integer)


class Resource(Base):
    __tablename__ = 'resource'
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('job.id'))
    data = Column(Text)
    job = relationship("Job", back_populates="resources")


Job.resources = relationship(
    "Resource", order_by=Resource.id, back_populates="job")


class Store(object):

    def __init__(self, db_src='sqlite://'):
        self.db_src = db_src
        self.engine = create_engine(self.db_src)
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)

    def add(self, data):
        sess = self.Session()
        sess.add(data)
        sess.commit()

    def update(self, data):
        sess = self.Session()
        sess.update(data)
        sess.commit()

    def query_resource(self, resource_id):
        sess = self.Session()
        obj = sess.query(Resource).filter_by(id=resource_id).first()
        if obj:
            return json.loads(obj.data)
        return {}
