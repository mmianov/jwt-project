from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import File, Resource, User

from app import db, app


# checks if username already exists
def user_exists(username):
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        return False if user is None else True


# add new user to database
def add_user(username, password):
    with app.app_context():
        user = User(username=username,password_hash=password, is_admin=False)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print("Added new user: " + username)


# verifies login credentials
def verify_login(username, password):
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        return False if user is None else user.check_password(password)


# adds resource for a user
def add_user_resource(username, resource_name):
    with app.app_context():
        # create resource for with user as owner
        user = User.query.filter_by(username=username).first()
        resource = Resource(name=resource_name, owner_id=user.id)
        db.session.add(resource)

        # give user read and write permissions
        user.read_resources.append(resource)
        user.write_resources.append(resource)

        db.session.commit()
        print("Created new resource: " + resource_name + " for user: " + username)


# checks if resource already exists
def resource_exists(username, resource_name):
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        resources = user.write_resources
        for r in resources:
            if r.name == resource_name:
                return True
        return False
    # maybe rewrite this function to use filter_by(owner, name) ?


# gets all resources for the user
def get_resources(username):
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        return user.write_resources
    # TODO: return read and write resource objects ? and then distinguish between them?


# gets resource from given username
def get_single_resource(username, resource_name):
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        resource = Resource.query.filter_by(name=resource_name,owner_id=user.id).first()
        return resource

     #TODO: search for resource in ALL users?


# gets owner of resource by resource id
def get_resource_owner(id):
    with app.app_context():
        resource = Resource.query.filter_by(id=id).first()
        owner = User.query.filter_by(id=resource.owner_id).first()
        return owner


# gets files of resource by resource id
def get_resource_files(id):
    with app.app_context():
        resource = Resource.query.filter_by(id=id).first()
        files = File.query.filter_by(resource_id=resource.id).all()
        print(files)
        return files


# TODO: for now, everything is owner centered - write and read permissions dont really apply
# this has to be changed later on (probably in some functions above as well)
# add file to resource
def add_single_file(username, resource, name):
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        resource = Resource.query.filter_by(owner_id=user.id,name=resource).first()
        file = File(name=name,resource_id=resource.id)
        db.session.add(file)
        db.session.commit()