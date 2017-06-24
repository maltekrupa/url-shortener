import datetime
import logging
import os
import random
import string
import urllib

from pytz import utc

from flask import Flask
from flask import render_template
from flask import request
from flask import send_file
from flask import jsonify

from flask_wtf.csrf import CSRFProtect
from flask_wtf.csrf import CSRFError

import validators
import requests

import psycopg2
import psycopg2.extras

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]
csrf = CSRFProtect(app)


def setup_database(db):
    cursor = db.cursor()
    cursor.execute("""
                   CREATE TABLE
                   IF NOT EXISTS
                   urls
                   (timestamp timestamptz, id text, url text)
                   """)
    db.commit()


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
    return "No shirt, no CSRF? No service!", 400


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


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
        response = jsonify({"error": "invalid url"})
        response.headers['Get your *@#% together'] = "Please"
        return response

    url_id = id_generator()

    try:
        insert_url(database_connection, url, url_id)
    except Exception as e:
        log.error("Couldn't write to database: {}".format(e))
        return jsonify({"error": "database error"})
    else:
        log.info("Created {} for: {}".format(url_id, url))

    return jsonify({
        "error": None,
        "id": url_id,
        "url": url
        })


@app.route('/<string(length=6):url_id>')
def id(url_id):
    db_response = get_url_from_id(database_connection, url_id)
    if db_response is None:
        return render_template('404.html'), 404
    else:
        log.info("ID {} is valid".format(url_id))
        log.debug("DB Response: {}".format(db_response))
        user_friendly_date = pretty_date(db_response['timestamp'])
        return render_template(
                               'id.html',
                               data=db_response,
                               user_friendly_date=user_friendly_date), 200


@app.route('/<string(length=6):url_id>/img')
def id_image(url_id):
    db_response = get_url_from_id(database_connection, url_id)
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


if __name__ == "__main__":
    log.debug("I'm alive")

    database_connection = psycopg2.connect("dbname=urls user=postgres")
    try:
        setup_database(database_connection)
    except:
        raise
    else:
        log.info("Database is setup")

    log.info("Starting webapp")
    app.run(host='0.0.0.0', debug=True)

    log.info("Done")
