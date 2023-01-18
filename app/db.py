from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import File, Resource, User

from app import db, app


def get_user(username):
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        return user

def get_user_by_id(user_id):
    with app.app_context():
        user = User.query.filter_by(id=user_id).first()
        return user


# checks if username already exists
def user_exists(username):
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        return False if user is None else True


# add new user to database
def add_user_to_database(username, password):
    print("adding user")
    with app.app_context():
        user = User(username=username,password_hash=password, is_admin=False)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print("Added new user: " + username)


# verifies login credentials
def verify_login(username, password):
    print("veryfing login")
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        return False if user is None else user.check_password(password)


# adds resource for a user
def add_user_resource(username, resource_name):
    with app.app_context():
        # create resource for with user as owner
        user = User.query.filter_by(username=username).first()
        # TWO PARAMETERS - resource name to differenitate from resources but ALSO
        # owner id to differentiate users (many users can have the same resource name)
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


# get all resources OWNED by user
def get_resources(username):
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        user_id = user.id
        resources = Resource.query.filter_by(owner_id=user_id).all()
        # for r in resources:
        #     print("Write users: ", r.owner_id)
        #     print("Read users: ",r.read_users[0].id)
        #     print("Write users: ", r.write_users[0].id)
        return resources


# get all resources SHARED with the user (both read and write)
def get_shared_resources(username):
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        # get all read and write resources
        write_resources = user.write_resources
        read_resources = user.read_resources
        # eliminate duplicates:
        # > if user has write, then they have to have read as well, but we don't want to show the resource twice
        all_res = list(set(write_resources + read_resources))
        # eliminate resouces that are owned by the user
        shared = []
        for r in all_res:
            if r.owner_id != user.id:
                shared.append(r)
        print(shared)
        return shared


# get files of resource by resource id
def get_resource_files(username, resource):
    with app.app_context():
        # get username and user_id
        user = User.query.filter_by(username=username).first()

        # get resource with the name <resource> AND owned by user_id
        res = Resource.query.filter_by(name=resource, owner_id=user.id).first()
        print(res.all_files)
        return res.all_files


# get all users that have either read of write access to the resource
def get_resource_users(username, resource):
    # get username and user_id
    user = User.query.filter_by(username=username).first()
    # get resource with the name <resource> AND owned by user_id
    res = Resource.query.filter_by(name=resource, owner_id=user.id).first()
    # get read and write users
    read_users = res.read_users
    write_users = res.write_users
    # get rid of permission duplicates
    all_users = list(set(read_users + write_users))
    users = []
    for u in all_users:
        if u.id != user.id:
            users.append(u)
    #print(users)
    return users


# gets owner of resource by resource id
def get_resource_owner(id):
    with app.app_context():
        resource = Resource.query.filter_by(id=id).first()
        owner = User.query.filter_by(id=resource.owner_id).first()
        return owner


# get ALL users except for the user itself
def get_all_users(username):
    user = User.query.filter_by(username=username).first()
    users = User.query.all()
    for u in users:
        if u.id == user.id:
            users.remove(u)
    #rint(users)
    return users


# add user to specified resource
def add_user_to_resource(username, resource, added_user, read):
    # get username and user_id
    user = User.query.filter_by(username=username).first()
    # get resource with the name <resource> AND owned by user_id
    res = Resource.query.filter_by(name=resource, owner_id=user.id).first()
    # get added user
    added_u = User.query.filter_by(username=added_user).first()
    if added_u in res.read_users or added_u in res.write_users:
        return False
    # add this user to resource - read access guaranteed
    res.read_users.append(added_u)
    # check if user is not read-only (meaning write access)
    if not read:
        res.write_users.append(added_u)
    db.session.commit()
    print("Added user: " + added_user + " to: " + resource)
    return True


# delete user from specified resource
def delete_user_from_resource(username, resource, deleted_user):
    # get username and user_id
    user = User.query.filter_by(username=username).first()
    # get resource with the name <resource> AND owned by user_id
    res = Resource.query.filter_by(name=resource, owner_id=user.id).first()
    # get deleted user
    deleted_u = User.query.filter_by(username=deleted_user).first()

    if deleted_u in res.read_users:
        res.read_users.remove(deleted_u)
        print("Deleted: " + deleted_u.username + " from " + resource + " (read)")
    if deleted_u in res.write_users:
        res.write_users.remove(deleted_u)
        print("Deleted: " + deleted_u.username + " from " + resource + " (write)")
    db.session.commit()
    return "User successfully deleted"


# TODO: test if all files are deleted (probably wont bother deleting users)
def delete_resource(username, resource):
    # get username and user_id
    user = User.query.filter_by(username=username).first()
    # get resource with the name <resource> AND owned by user_id
    res = Resource.query.filter_by(name=resource, owner_id=user.id).first()
    all_files = res.all_files
    # delete all files within the resource
    for f in all_files:
        print("Deleted file: " + f.name + " from: " + res.name)
        db.session.delete(f)
    # delete the resource itself
    db.session.delete(res)
    db.session.commit()
    print("Deleted resource: " + resource +" of user: " + username)


# add note to specified resource
def add_note_to_resource(username, resource,name,content):
    # get username and user_id
    user = User.query.filter_by(username=username).first()
    # get resource with the name <resource> AND owned by user_id
    res = Resource.query.filter_by(name=resource, owner_id=user.id).first()
    # create a new file
    file = File(name=name,content=content)
    # add to database
    db.session.add(file)
    # add file to the resource
    res.all_files.append(file)
    db.session.commit()
    print("Added: " + name + " to resource: " + resource)


# get content of specified note
def get_note(username, resource, name):
    # get username and user_id
    user = User.query.filter_by(username=username).first()
    # get resource with the name <resource> AND owned by user_id
    res = Resource.query.filter_by(name=resource, owner_id=user.id).first()
    # get note in that resource
    note = File.query.filter_by(resource_id=res.id,name=name).first()
    return note


def update_note(file_id, name, content):
    with app.app_context():
        note = File.query.filter_by(id=file_id).first()
        note.name = name
        note.content = content
        db.session.commit()
        print("Changed name of note of id: " + str(file_id) + " to " + name)


def delete_note(file_id):
    with app.app_context():
        note = File.query.filter_by(id=file_id).first()
        print("Deleted note:id=" + str(file_id) + ", name=" +note.name)
        db.session.delete(note)
        db.session.commit()


def get_user(username):
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        return user


# check if <username> matches the actual user
def is_user(user_id, username):
    with app.app_context():
        session_user = User.query.filter_by(id=user_id).first()
        if session_user.username == username:
            return True
        return False


# check if user is the owner of specific resource
def is_owner(user_id, username, resource):
    # get username and user_id
    user = User.query.filter_by(username=username).first()
    # get resource with the name <resource> AND owned by user_id
    res = Resource.query.filter_by(name=resource, owner_id=user.id).first()
    if res.owner_id == user_id:
        return True
    return False


# check if actual user can view specific resource of specific user (actual refers to JWT verified)
def is_in_resource(actual_user, username, resource):
    # get username and user_id
    user = User.query.filter_by(username=username).first()
    # get resource with the name <resource> AND owned by user_id
    res = Resource.query.filter_by(name=resource, owner_id=user.id).first()
    for u in (res.read_users+res.write_users):
        if u.id == actual_user.id:
            return True
    return False


def is_write(actual_user, username, resource):
    # get username and user_id
    user = User.query.filter_by(username=username).first()
    # get resource with the name <resource> AND owned by user_id
    res = Resource.query.filter_by(name=resource, owner_id=user.id).first()
    for u in res.write_users:
        if u.id == actual_user.id:
            return True
    return False


def is_read(actual_user, username, resource):
    # get username and user_id
    user = User.query.filter_by(username=username).first()
    # get resource with the name <resource> AND owned by user_id
    res = Resource.query.filter_by(name=resource, owner_id=user.id).first()
    for u in res.read_users:
        if u.id == actual_user.id:
            return True
    return False


def file_exists(username, resource,filename):
    # get username and user_id
    user = User.query.filter_by(username=username).first()
    # get resource with the name <resource> AND owned by user_id
    res = Resource.query.filter_by(name=resource, owner_id=user.id).first()
    for f in res.all_files:
        if f.name == filename:
            return True
    return False












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



# FUNCTIONALITY

# user at home has two types of resources:
# 1. user's OWN resources (query only resources that are owned by user)
# 2. Shared for me resources -> other people resources (that this user has write or write to)
# > there has to be some kind of distinction between read and write resources (maybe some kind of badge or two
#   separate categories


# files should be of any types and cannot be edited directly in the app
# serilized data in database?