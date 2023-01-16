from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import os
from flask_jwt_extended import JWTManager
from datetime import timedelta


basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] =\
           'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SECRET_KEY']= '014f5c54523ace161a2d7ad17fdae47f'
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

jwt = JWTManager(app)

db = SQLAlchemy(app)

from app.models import User, Resource, File

with app.app_context():
    db.create_all()

from app import routes
