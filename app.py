import logging
import random
import string
import sqlite3
import sys

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def setup_database(db):
    cursor = db.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS urls (id text, url text)")
    db.commit()

def id_generator(size=6, chars=string.ascii_lowercase + string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def insert_url(db, url):
    cursor = db.cursor()

    url_id = id_generator()

    cursor.execute("""
            INSERT INTO urls
            (id, url)
            VALUES
            ('{}', '{}')
            """.format(url_id, url))
    db.commit()
    return url_id

def main():
    log.debug("I'm alive")
    database_connection = sqlite3.connect('database.sqlite')
    try:
        setup_database(database_connection)
    except:
        raise
    else:
        log.info("Database is setup")

    try:
        url_id = insert_url(database_connection, sys.argv[1])
    except:
        raise
    else:
        log.info("Created URL entry with ID {}".format(url_id))

if __name__ == "__main__":
    main()
    log.info("Done")
