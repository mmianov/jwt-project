from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table
from passlib.hash import pbkdf2_sha256
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy
from app import db



#Base = declarative_base()


read_association_table = Table('read_association', db.Model.metadata,
    Column('read_user_id', Integer, ForeignKey('users.id')),
    Column('resource_id', Integer, ForeignKey('resources.id'))
)

write_association_table = Table('write_association', db.Model.metadata,
    Column('write_user_id', Integer, ForeignKey('users.id')),
    Column('resource_id', Integer, ForeignKey('resources.id'))
)


class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True,autoincrement='auto')
    username = Column(String)
    password_hash = Column(String)
    is_admin = Column(Boolean, default=False)

    read_resources = relationship("Resource", secondary=read_association_table, back_populates="read_users")
    write_resources = relationship("Resource", secondary=write_association_table, back_populates="write_users")

    def set_password(self, password):
        self.password_hash = pbkdf2_sha256.hash(password)

    def check_password(self, password):
        return pbkdf2_sha256.verify(password, self.password_hash)


class Resource(db.Model):
    __tablename__ = 'resources'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    owner_id = Column(Integer, ForeignKey('users.id'))
    #owner = relationship('User', back_populates='username')

    all_files = relationship('File', back_populates='resource')

    read_users = relationship("User", secondary=read_association_table, back_populates="read_resources")
    write_users = relationship("User", secondary=write_association_table, back_populates="write_resources")


class File(db.Model):
    __tablename__ = 'files'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    #content = Column(String,nullable=True)
    resource_id = Column(Integer, ForeignKey('resources.id'))
    resource = relationship('Resource', back_populates='all_files')

    def __repr__(self):
        return self.name

