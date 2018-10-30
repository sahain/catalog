from flask import Flask, render_template, request, redirect, jsonify, \
    url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from models import Base, User, Category, Item
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import functools
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
CLIENT_SECRET = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_secret']

APPLICATION_NAME = "Catalog App"

# Connect to Database and create database session
engine = create_engine('postgresql://catalog_user:catalog_db@localhost/catalog')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'),
            200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['email'].split('@')[0]
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; \
        height: 300px;border-radius: 150px;-webkit-border-radius: 150px; \
        -moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


def createUser(login_session):
    newUser = User(username=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except SQLAlchemyError:
        return None


@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        resp_msg = 'Successfully disconnected.'
        response = make_response(json.dumps(resp_msg), 200)
        response.headers['Content-Type'] = 'application/json'
        flash(resp_msg)
        print(response)
        return redirect(url_for('index'))
    else:
        # if token is invalid
        resp_msg = 'Failed to revoke token for given user.'
        response = make_response(
            json.dumps(resp_msg), 400)
        response.headers['Content-Type'] = 'application/json'
        flash(resp_msg)
        print(response)
        return redirect(url_for('index'))


def login_required(func):
    """Ensure user is logged in"""
    @functools.wraps(func)
    def wrap_login_req(*args, **kwargs):
        if 'username' not in login_session:
            return redirect('/login')
        return func(*args, **kwargs)
    return wrap_login_req


# JSON API for catalog endpoint
@app.route('/catalog.json')
def catalogJSON():
    categories = session.query(Category).all()
    return jsonify(categories=[c.serialize for c in categories])


@app.route('/catalog/<category_name>/items.json')
def category_items_indexJSON(category_name):
    category = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(
        category=category).all()
    return jsonify(Items=[i.serialize for i in items])


@app.route('/catalog/<category_name>/item/<item_title>.json')
def itemJSON(category_name, item_title):
    item = session.query(Item).filter_by(title=item_title).one()
    return jsonify(item=item.serialize)


@app.route('/', methods=['GET', 'POST'])
@app.route('/categories/', methods=['GET', 'POST'])
def index():
    categories = session.query(Category).all()
    items = session.query(Item).order_by(Item.id.desc()).limit(8)
    if 'username' not in login_session:
        return render_template(
            'public_index.html', categories=categories, items=items)
    else:
        return render_template(
            'index.html', categories=categories, items=items)


@app.route('/category/new', methods=['GET', 'POST'])
@login_required
def new_category():
    if request.method == 'POST':
        cat_name = request.form['name'].lower()
        new_category = Category(
                       name=cat_name, user_id=login_session['user_id'])
        session.add(new_category)
        flash('created {}'.format(new_category.name))
        session.commit()
        return redirect(url_for('index'))
    else:
        return render_template('new_category.html')


@app.route('/category/<category_name>')
def show_category(category_name):
    category = session.query(Category).filter_by(name=category_name).first()
    return render_template('show_category.html')


@app.route('/catalog/<category_name>/items')
def category_items_index(category_name):
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(name=category_name).first()
    creator = getUserInfo(category.user_id)
    items = session.query(Item).filter_by(
        category=category).all()
    if 'username' not in login_session \
            or creator.id != login_session['user_id']:
        return render_template('public_items_index.html',
                               category=category,
                               items=items, categories=categories,
                               creator=creator)
    else:
        return render_template('items_index.html', category=category,
                               items=items, categories=categories,
                               creator=creator)


@app.route('/catalog/<category_name>/items/new', methods=['GET', 'POST'])
@login_required
def new_category_item(category_name):
    category = session.query(Category).filter_by(name=category_name).first()
    if login_session['user_id'] != category.user_id:
        return "<script>function myFunction() \
            {alert('You are not authorized to add items to this category. \
                Please create your own category in order to add items.');} \
                </script><body onload='myFunction()''>"
    if request.method == 'POST':
        newItem = Item(
            title=request.form['title'],
            description=request.form['description'],
            category_id=category.id,
            user_id=category.user_id)
        session.add(newItem)
        session.commit()
        flash("item created")
        return redirect(url_for('category_items_index',
                                category_name=category_name))
    else:
        return render_template('new_category_item.html',
                               category_name=category_name)


@app.route('/catalog/<category_name>/<item_title>')
def show_item(category_name, item_title):
    item = session.query(Item).filter_by(title=item_title).first()
    creator = getUserInfo(item.user_id)
    category = item.category
    if 'username' not in login_session \
            or creator.id != login_session['user_id']:
        return render_template('public_show_item.html', item=item)
    else:
        return render_template('show_item.html', item=item)


@app.route('/catalog/<item_title>/edit', methods=['GET', 'POST'])
@login_required
def edit_item(item_title):
    item = session.query(Item).filter_by(title=item_title).first()
    category = item.category
    if login_session['user_id'] != category.user_id:
        return "<script>function myFunction() \
            {alert('You are not authorized to edit items in this category. \
            Please create your own category in order to add items.');} \
            </script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['title']:
            item.title = request.form['title']
        if request.form['description']:
            item.description = request.form['description']
        session.add(item)
        session.commit()
        # flash("{} edited").format(item.title)
        return redirect(url_for('category_items_index',
                                category_name=category.name))
    else:
        return render_template('edit_item.html', item=item, category=category)


@app.route('/catalog/<item_title>/delete', methods=['GET', 'POST'])
@login_required
def delete_item(item_title):
    item = session.query(Item).filter_by(title=item_title).first()
    category = item.category
    if login_session['user_id'] != category.user_id:
        return "<script>function myFunction() \
            {alert('You are not authorized to delete items in this category. \
            Please create your own category in order to add items.');} \
            </script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        flash("item removed")
        return redirect(url_for('category_items_index',
                                category_name=category.name))
    else:
        return render_template(
            'delete_item.html', item=item, category=category)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
