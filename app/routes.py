from app import app
from flask import render_template, redirect, request, url_for, make_response
from app.db import user_exists, add_user, verify_login, add_user_resource, resource_exists, get_resources,\
get_single_resource, get_resource_owner, get_resource_files,add_single_file


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == '' or password == '':
            error = 'Please enter your credentials.'
        elif not verify_login(username, password):
            error = 'Wrong credentials.'
        else:
            print('Successfuly logged in as user:' + username)
            # TODO: create user session with JWT token (as a cookie?)
            # for tests, I just set up a simple cookie with name so I can distinguish between users

            # redirect to /<username>/home and set cookie to username
            resp = redirect(url_for('home', username=username))
            resp.set_cookie('user', username)
            return resp

    return render_template('login.html',error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm']

        if username == '' or password == '' or confirm == '':
            error = 'Please fill out all required information.'
        elif password != confirm:
            error = 'Passwords do not match.'
        elif user_exists(username):
            error = 'Username already exists'
        else:
            add_user(username, password)
            return redirect(url_for('login'))

    return render_template('register.html', error=error)


@app.route('/<username>/home', methods=['GET'])
def home(username):
    if user_exists(username):
        resources = get_resources(username)
        return render_template('home.html', username=username, resources=resources,n=len(resources))
    return 'Not found', 404


@app.route('/<username>/add_resource', methods=['GET','POST'])
def add_resource(username):
    error = None
    if not user_exists(username):
        return 'Not found', 404

    if request.method == 'POST':
        if request.form['name'] == '':
            error = 'Resource has to have a name.'
        elif resource_exists(username, request.form['name']):
            error = 'Resource with this name already exists.'
        else:
            add_user_resource(username, request.form['name'])
            return redirect(url_for('home', username=username))

    return render_template('add_resource.html', error=error)


@app.route('/<username>/<resource>', methods=['GET','POST'])
def show_resource(username, resource):
    error = None
    if user_exists(username) and resource_exists(username, resource):
        # adding new file
        if request.method == 'POST':
            name = request.form['name']
            content = request.form['content']
            if name == '' or content == '':
                error = 'Fill out file name and content.'
            # TODO: check if file exists?
            # TODO: add content to database (needs database rebuild)
            else:
                add_single_file(username,resource,name)
                return redirect(url_for('show_resource', username=username,resource=resource))

        # showing resource
        r = get_single_resource(username, resource)
        files = get_resource_files(r.id)
        owner = get_resource_owner(r.id)
        return render_template('resource.html', resource=r, owner=owner,files=files,n=len(files),error=error)
    return 'Not found', 404


