import datetime
import logging
import random
import string
import sqlite3
import sys

from flask import Flask
from flask import Response
from flask import render_template
from flask import request
from flask import jsonify

import validators
import requests

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = Flask(__name__)

def setup_database(db):
    cursor = db.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS urls (timestamp text, id text, url text)")
    db.commit()

def id_generator(size=6, chars=string.ascii_lowercase + string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def insert_url(db, url, url_id):
    cursor = db.cursor()
    now = datetime.datetime.utcnow().isoformat()
    data = (now, url_id, url,)

    try:
        cursor.execute("""
                INSERT INTO urls
                (timestamp, id, url)
                VALUES
                (?, ?, ?)
                """, data)
        db.commit()
    except:
        raise

def get_url_from_id(db, url_id):
    cursor = db.cursor()
    data = (url_id,)

    try:
        cursor.execute("""
                SELECT * FROM urls
                WHERE id == ?
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
        log.warning("Invalid URL: {}".format(url))
        raise ValueError("Invalid URL")
    log.info("Valid URL: {}".format(url))

def url_reachable(url):
    try:
        r = requests.get(url, timeout=5)
    except:
        log.warning("Cannot reach {}".format(url))
        raise

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/url', defaults={'url': ''})
@app.route('/url/<path:url>')
def url(url):
    if request.method != "GET":
        response = Response("Nope")
        response.headers["What-are-you-doing?"] = "Leave me alone!"
        return response

    if len(url) <= 0:
        raise ValueError("No url found")

    if not url.startswith("http://") and not url.startswith("https://"):
        url = "{}{}".format("http://", url)

    try:
        url_valid(url)
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
    if not db_response is None:
        log.info(db_response)
        return jsonify(db_response)
    else:
        return render_template('404.html'), 404


@app.route('/')
def index():
    return render_template('index.html',
            greeting="Hello!",
            greeting_small="Shorten a URL and get a preview of the status quo.")

if __name__ == "__main__":
    log.debug("I'm alive")

    database_connection = sqlite3.connect('database.sqlite', check_same_thread=False)
    try:
        setup_database(database_connection)
    except:
        raise
    else:
        log.info("Database is setup")

    log.info("Starting webapp")
    app.run(host='0.0.0.0', debug=True)
    log.info("Done")
