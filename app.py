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

    try:
        cursor.execute("""
                INSERT INTO urls
                (timestamp, id, url)
                VALUES
                ('{}', '{}', '{}')
                """.format(now, url_id, url))
        db.commit()
    except:
        raise

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

@app.route('/url/', defaults={'url': ''})
@app.route('/url/<path:url>')
def url(url):
    if request.method != "GET":
        response = Response("Nope")
        response.headers["What-are-you-doing?"] = "Leave me alone!"
        return response

    if len(url) <= 0:
        raise ValueError("No url found")

    if not url.startswith("http://") or not url.startswith("https://"):
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
        "id": url_id,
        "url": url
        })

@app.route('/')
def index():
    return render_template('index.html',
            greeting="Hello!",
            greeting_small="Shorten a URL and get a preview of the status quo.")

def main():
    try:
        url_id = insert_url(database_connection, sys.argv[1])
    except:
        raise
    else:
        log.info("Created URL entry with ID {}".format(url_id))

if __name__ == "__main__":
    log.debug("I'm alive")

    database_connection = sqlite3.connect('database.sqlite')
    try:
        setup_database(database_connection)
    except:
        raise
    else:
        log.info("Database is setup")

    log.info("Starting webapp")
    app.run(host='0.0.0.0')
    log.info("Done")
