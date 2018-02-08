import datetime
import logging
import os
import random
import string
import urllib
import sys

from pytz import utc

from flask import Flask
from flask import render_template
from flask import request
from flask import send_file
from flask import send_from_directory
from flask import jsonify
from flask import g
from flask import make_response

from flask_wtf.csrf import CSRFProtect
from flask_wtf.csrf import CSRFError

from functools import wraps
from flask import request, Response

from functools import update_wrapper

import validators
import requests

import psycopg2
import psycopg2.extras

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]
csrf = CSRFProtect(app)

basic_auth_username = os.environ["BASIC_AUTH_USERNAME"]
basic_auth_password = os.environ["BASIC_AUTH_PASSWORD"]


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == basic_auth_username and password == basic_auth_password


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


def nocache(f):
    def new_func(*args, **kwargs):
        resp = make_response(f(*args, **kwargs))
        resp.cache_control.no_cache = True
        return resp
    return update_wrapper(new_func, f)


def id_generator(
    size=6,
    chars=string.ascii_lowercase +
    string.ascii_uppercase +
    string.digits
):
    return ''.join(random.choice(chars) for _ in range(size))


def insert_url(db, url, url_id):
    cursor = db.cursor()
    now = datetime.datetime.now(utc)
    data = (now, url_id, url,)

    try:
        cursor.execute("""
                INSERT INTO urls
                (timestamp, id, url)
                VALUES
                (%s, %s, %s)
                """, data)
        db.commit()
    except:
        raise


def get_all_urls(db):
    cursor = db.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
        cursor.execute("""
                SELECT * FROM urls
                ORDER BY timestamp DESC
                """)
    except:
        raise
    else:
        result = cursor.fetchall()
        return result


def get_url_from_id(db, url_id):
    cursor = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
    data = (url_id,)

    try:
        cursor.execute("""
                SELECT * FROM urls
                WHERE id = %s
                ORDER BY timestamp DESC
                LIMIT 1
                """, data)
    except:
        raise
    else:
        result = cursor.fetchone()
        return result


def url_valid(url):
    if not validators.url(url, public=True):
        log.warning("Invalid URL ({}).".format(url))
        raise ValueError("Invalid URL or URN")
    log.info("Valid URL or URN: {}".format(url))


def url_reachable(url):
    try:
        requests.get(url, timeout=5)
    except:
        log.warning("Cannot reach {}".format(url))
        raise


def pretty_date(time=False):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    """
    now = datetime.datetime.now(utc)
    if type(time) is int:
        diff = now - datetime.datetime.fromtimestamp(time)
    elif isinstance(time, datetime.datetime):
        diff = now - time
    elif not time:
        diff = now - now
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(second_diff) + " seconds ago"
        if second_diff < 120:
            return "a minute ago"
        if second_diff < 3600:
            return str(int(second_diff / 60)) + " minutes ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return str(int(second_diff / 3600)) + " hours ago"
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return str(day_diff) + " days ago"
    if day_diff < 31:
        return str(int(day_diff / 7)) + " weeks ago"
    if day_diff < 365:
        return str(int(day_diff / 30)) + " months ago"
    return str(int(day_diff / 365)) + " years ago"


@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    log.info("Invalid CSRF")
    return "No shirt, no CSRF, no service!", 400


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
            'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/admin', methods=["GET"])
@requires_auth
def admin():
    db = get_db()

    all_urls = get_all_urls(db)

    return render_template('admin.html', urls=all_urls)


@app.route('/url/', methods=["GET", "POST"])
def url():
    if request.method != "POST":
        return render_template('404.html'), 404

    url = urllib.parse.unquote(request.form['url'])

    if not url.startswith("http://") and not url.startswith("https://"):
        url = "{}{}".format("http://", url)

    real_url = "//".join(list(filter(None, url.split('/')[:3])))
    try:
        url_valid(real_url)
        log.info("Validated {}.".format(real_url))
    except:
        response = jsonify({"message": "invalid url"})
        response.headers['Get your *@#% together'] = "Please"
        return response

    url_id = id_generator()

    try:
        db = get_db()
        insert_url(db, url, url_id)
    except Exception as e:
        log.error("Couldn't write to database: {}".format(e))
        return jsonify({"message": "database error"})
    else:
        log.info("Created {} for: {}".format(url_id, url))

    return jsonify({
        "message": None,
        "id": url_id,
        "url": url
    })


@app.route('/<string(length=6):url_id>')
def id(url_id):
    db = get_db()
    db_response = get_url_from_id(db, url_id)
    if db_response is None:
        return render_template('404.html'), 404
    else:
        log.info("ID {} is valid".format(url_id))
        user_friendly_date = pretty_date(db_response['timestamp'])
        return render_template(
            'id.html',
            data=db_response,
            user_friendly_date=user_friendly_date), 200


@app.route('/<string(length=6):url_id>/img')
@nocache
def id_image(url_id):
    db = get_db()
    db_response = get_url_from_id(db, url_id)
    if db_response is None:
        return render_template('404.html'), 404
    else:
        log.info("ID {} is valid. Let's serve an image.".format(url_id))
        pwd = os.path.abspath("images")
        filename = pwd + "/" + str(url_id) + '.jpg'
        if os.path.isfile(filename):
            return send_file(filename, mimetype='image/jpg')
        else:
            log.info("Image for {} is not yet ready!".format(url_id))
            return send_file('static/waiting.jpg', mimetype='image/jpg')


@app.route('/')
def index():
    return render_template('index.html')


@app.before_first_request
def setup():
    log.debug("I'm alive")

    db = get_db()

    try:
        setup_database(db)
    except:
        raise
    else:
        log.info("Database is setup")

    log.info("Starting webapp")


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'postgres'):
        g.postgres = connect_db()
    return g.postgres


def connect_db():
    database_host = os.environ["DATABASE_HOST"]
    database_port = os.environ["DATABASE_PORT"]
    database_user = os.environ["DATABASE_USER"]
    database_password = os.environ["DATABASE_PASSWORD"]

    try:
        db = psycopg2.connect(
            host=database_host,
            port=database_port,
            user=database_user,
            password=database_password,
            connect_timeout=5
        )
    except psycopg2.OperationalError as e:
        log.error("Database timeout: {}".format(e))
        sys.exit(1)
    else:
        return db


def setup_database(db):
    cursor = db.cursor()
    cursor.execute("""
                   CREATE TABLE
                   IF NOT EXISTS
                   urls
                   (timestamp timestamptz, id text, url text)
                   """)
    db.commit()


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'postgres'):
        g.postgres.close()

if __name__ == "__main__":
    print("I'm alive!")
    app.run(host='0.0.0.0')
