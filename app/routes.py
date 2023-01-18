from app import app
# import jwt
import datetime
from functools import wraps
from flask import render_template, redirect, request, url_for, make_response, send_file, Response
from app.db import user_exists, add_user_to_database, verify_login, add_user_resource, resource_exists, get_resources,\
get_single_resource, get_resource_owner, get_resource_files,add_single_file,get_shared_resources,get_resource_users,\
get_all_users, add_user_to_resource, delete_user_from_resource, delete_resource, add_note_to_resource, get_note,\
update_note, delete_note, get_user, get_user_by_id, is_user, is_owner, is_in_resource, is_write, is_read,file_exists

from flask_jwt_extended import create_access_token
from flask_jwt_extended import set_access_cookies
from flask_jwt_extended import unset_jwt_cookies
from flask_jwt_extended import decode_token




def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = None
        if 'access_token_cookie' in request.cookies:
            token = request.cookies['access_token_cookie']
        if not token:
            return render_template('error-permission.html',error="Authorization component missing")
        try:
            # data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            data = decode_token(token)['sub']
            current_user = get_user_by_id(data['user_id'])
            print(current_user.username)
            print((current_user.id, args, kwargs))
            return f(current_user, *args, **kwargs)
        except Exception as e:
            print(e)
            return render_template('error-permission.html', error="You are not authorized to perform this action.")

    return decorator



@app.route('/')
def index():
    return render_template('index_boot.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        print("POST req")
        username = request.form['username']
        password = request.form['password']

        if username == '' or password == '':
            error = 'Please enter your credentials.'
        elif not verify_login(username, password):
            error = 'Wrong credentials.'
            print("wrong creds")
        else:
            user = get_user(username)
            access_token = create_access_token(identity={"user_id":user.id})
            # jwt = encode_jwt(user.id)
            print('Successfuly logged in as user:' + username)

            # redirect to /<username>/home and set JWT
            resp = redirect(url_for('home', username=username))
            set_access_cookies(resp, access_token)
            # resp.set_cookie('Auth', value=jwt,httponly=True)
            return resp

    return render_template('login_boot.html',error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm']
        print(username, password, confirm)
        if username == '' or password == '' or confirm == '':
            error = 'Please fill out all fields.'
        elif password != confirm:
            error = 'Passwords do not match.'
        elif user_exists(username):
            error = 'Username already exists'
        else:
            add_user_to_database(username, password)
            return redirect(url_for('login'))

    return render_template('register_boot.html', error=error)



@app.route('/<username>/home', methods=['GET'])
@token_required
def home(current_user, username):
    if not is_user(current_user.id, username):
        nav_user = get_user_by_id(current_user.id).username
        return render_template('error-permission.html', error="You are not authorized to perform this action.",username=username,nav_user=nav_user), 403

    resources = get_resources(username)
    print(resources)
    nav_user = get_user_by_id(current_user.id).username
    return render_template('home_boot.html', username=username, resources=resources,nav_user=nav_user)


@app.route('/<username>/resources', methods=['GET'])
@token_required
def resources(current_user, username):
    nav_user = get_user_by_id(current_user.id).username
    if not user_exists(username):
        return render_template('error-permission.html', error="Page not found",username=username,nav_user=nav_user), 404

    if not is_user(current_user.id, username):
        return render_template('error-permission.html', error="You are not authorized to perform this action.",username=username,nav_user=nav_user), 403

    my_resources = get_resources(username)
    shared_resources = get_shared_resources(username)
    shared_users = []
    for r in shared_resources:
        shared_users.append(get_resource_owner(r.id))

    print(shared_users)
    return render_template('resources.html', username=username, my_resources=my_resources,
                           shared_resources=shared_resources,shared_users=shared_users,
                           n=len(my_resources),m=len(shared_resources),nav_user=nav_user)


@app.route('/<username>/<resource>', methods=['GET','POST'])
@token_required
def resource_view(current_user, username,resource):
    nav_user = get_user_by_id(current_user.id).username

    if not user_exists(username):
        return render_template('error-permission.html', error="Page not found",username=username,nav_user=nav_user), 404

    if get_single_resource(username,resource) is None:
        return render_template('error-permission.html', error="Page not found",
                               username=username, nav_user=nav_user), 404

    owner = is_owner(current_user.id,username, resource)
    collab = is_in_resource(current_user, username, resource)
    write = is_write(current_user, username, resource)

    if not owner and not collab:
        return render_template('error-permission.html', error="You are not authorized to perform this action.",username=username,nav_user=nav_user), 403

    if request.method == 'POST' and owner:
        # delete resource
        delete_resource(username, resource)
        return redirect(url_for('resources', username=username))
    else:
        files = get_resource_files(username, resource)
        return render_template('resource-view.html', username=username, resource=resource, files=files, n=len(files),
                               owner=owner,write=write,nav_user=nav_user)


@app.route('/<username>/add_resource', methods=['GET','POST'])
@token_required
def add_resource(current_user, username):
    nav_user = get_user_by_id(current_user.id).username
    error = None
    if not user_exists(username):
        return render_template('error-permission.html', error="Page not found",username=username,nav_user=nav_user), 404

    if not is_user(current_user.id, username):
        return render_template('error-permission.html', error="You are not authorized to perform this action.",username=username,nav_user=nav_user), 403

    if request.method == 'POST':
        if request.form['name'] == '':
            error = 'Resource has to have a name.'
        elif resource_exists(username, request.form['name']):
            error = 'Resource with this name already exists.'
        else:
            add_user_resource(username, request.form['name'])
            return redirect(url_for('resources', username=username))

    return render_template('add-resource-boot.html', username=username,error=error)


@app.route('/<username>/<resource>/users', methods=['GET','POST'])
@token_required
def manage_users(current_user, username, resource):
    nav_user = get_user_by_id(current_user.id).username
    if not user_exists(username):
        return render_template('error-permission.html', error="Page not found",username=username,nav_user=nav_user), 404

    if get_single_resource(username, resource) is None:
        return render_template('error-permission.html', error="Page not found",
                               username=username, nav_user=nav_user), 404

    if not is_owner(current_user.id, username, resource):
        return render_template('error-permission.html', error="You are not authorized to perform this action.",username=username,nav_user=nav_user), 403

    if request.method == 'POST':
        deleted_user = request.form['user']
        delete_user_from_resource(username, resource, deleted_user)
        # get new list of resource users
        users = get_resource_users(username, resource)
        return render_template('users.html', users=users, username=username, resource=resource, n=len(users),nav_user=nav_user)
    else:
        users = get_resource_users(username, resource)
        return render_template('users.html', users=users, username=username, resource=resource, n=len(users),nav_user=nav_user)


@app.route('/<username>/<resource>/add_user', methods=['GET','POST'])
@token_required
def add_user(current_user, username, resource):
    nav_user = get_user_by_id(current_user.id).username
    error = None
    if not user_exists(username):
        return render_template('error-permission.html', error="Page not found",username=username,nav_user=nav_user), 404

    if get_single_resource(username, resource) is None:
        return render_template('error-permission.html', error="Page not found",
                               username=username, nav_user=nav_user), 404

    if not is_owner(current_user.id, username, resource):
        return render_template('error-permission.html', error="You are not authorized to perform this action.",username=username,nav_user=nav_user), 403

    users = get_all_users(username)

    if request.method == 'POST':
        read_only = False
        user = request.form['user']
        try:
            read_only = request.form['read']
            if read_only == 'on':
                read_only = True
        except:
            pass

        if not add_user_to_resource(username, resource, user, read_only):
            error = "User already in resource."
            return render_template('add-user.html', users=users, username=username, resource=resource, n=len(users), error=error,nav_user=nav_user)
        # get newly added user and render user management
        users = get_resource_users(username, resource)
        return redirect(url_for('manage_users', users=users, username=username, resource=resource, n=len(users)))
    else:
        return render_template('add-user.html',users=users, username=username,resource=resource,n=len(users),nav_user=nav_user)



@app.route('/<username>/<resource>/add_note', methods=['GET','POST'])
@token_required
def add_note(current_user, username, resource):
    nav_user = get_user_by_id(current_user.id).username
    error = None
    if not user_exists(username):
        return render_template('error-permission.html', error="Page not found",username=username,nav_user=nav_user), 404

    if get_single_resource(username, resource) is None:
        return render_template('error-permission.html', error="Page not found",
                               username=username, nav_user=nav_user), 404

    if not is_write(current_user, username, resource):
        return render_template('error-permission.html', error="You are not authorized to perform this action.",username=username,nav_user=nav_user), 403

    if request.method == 'POST':
        note_name = request.form['name']
        content = request.form['content']
        print("Note name: " + note_name + "| content: " + content)

        if note_name == '' or content == '':
            error = "Please fill out the fields"
            return render_template('add-note.html', username=username, resource=resource, error=error,nav_user=nav_user)

        add_note_to_resource(username, resource,note_name, content)
        files = get_resource_files(username, resource)
        return redirect(url_for('resource_view', username=username, resource=resource,nav_user=nav_user))
    else:
        return render_template('add-note.html',username=username, resource=resource,nav_user=nav_user)


@app.route('/<username>/<resource>/<file>', methods=['GET','POST'])
@token_required
def note_view(current_user, username, resource,file):
    nav_user = get_user_by_id(current_user.id).username
    error = None
    if not user_exists(username):
        return render_template('error-permission.html', error="Page not found",username=username,nav_user=nav_user), 404

    if get_single_resource(username, resource) is None:
        return render_template('error-permission.html', error="Page not found",
                               username=username, nav_user=nav_user), 404

    # check if note exists
    if not file_exists(username,resource,file):
        return render_template('error-permission.html', error="Page not found", username=username,
                               nav_user=nav_user), 404

    write = is_write(current_user, username, resource)
    read =  is_read(current_user, username, resource)
    print("Write: " + str(write))
    print("Read: " + str(read))

    if not write and not read:
        return render_template('error-permission.html', error="You are not authorized to perform this action.",username=username,nav_user=nav_user), 403

    readonly = (not write)

    if request.method == 'POST':
        if request.form['button'] == 'save' and write:
            # get current note id
            note = get_note(username, resource, file)
            # get new values
            name = request.form['name']
            content = request.form['content']
            # update values in the database
            update_note(note.id, name, content)
            # return to resource view
            return redirect(url_for('resource_view', username=username, resource=resource, read=readonly,nav_user=nav_user))

        elif request.form['button'] == 'download':
            name = request.form['name']
            content = request.form['content']
            return Response(
                content,
                mimetype='text/plain',
                headers={'Content-disposition': 'attachment; filename=' + name + ".txt"})

        elif request.form['button'] == 'delete' and write:
            # get current note id
            note = get_note(username, resource, file)
            # delete note
            delete_note(note.id)
            # return to resource view
            return redirect(url_for('resource_view', username=username, resource=resource,nav_user=nav_user))

        note = get_note(username, resource, file)
        return render_template('note-view.html', username=username, resource=resource, note=note, file=file, error=error, read=readonly,nav_user=nav_user)

    else:
        note = get_note(username, resource, file)
        return render_template('note-view.html', username=username, resource=resource, note=note, file=file, error=error,
                               read=readonly,nav_user=nav_user)



@app.route('/<username>/profile', methods=['GET'])
@token_required
def user_profile(current_user, username):
    nav_user = get_user_by_id(current_user.id).username
    if not user_exists(username):
        return render_template('error-permission.html', error="Page not found",username=username,nav_user=nav_user), 404

    if not is_user(current_user.id, username):
        return render_template('error-permission.html', error="You are not authorized to perform this action.",username=username,nav_user=nav_user), 403

    user = get_user(username)
    my_res = get_resources(username)
    shared_res = get_shared_resources(username)

    return render_template('profile.html', user=user, username=username, owned=len(my_res), shared=len(shared_res),nav_user=nav_user)


@app.route('/logout', methods=['GET'])
@token_required
def logout(current_user):
    resp = redirect(url_for('index'))
    unset_jwt_cookies(resp)
    return resp


@app.errorhandler(404)
def page_not_found(e):
    return render_template('error-permission.html', error="Page not found"),404




