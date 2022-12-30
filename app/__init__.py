from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os


basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] =\
           'sqlite:///' + os.path.join(basedir, 'database.db')

db = SQLAlchemy(app)
from app.models import User, Resource, File

with app.app_context():
    db.create_all()


from app import routes
