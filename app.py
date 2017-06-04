import random
import string
import sqlite3
import sys
from uuid import uuid4

def setup_database(db):
    cursor = db.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS urls (url text, uuid text, url_id text)")
    db.commit()

def id_generator(size=6, chars=string.ascii_lowercase + string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def insert_url(db, url):
    cursor = db.cursor()

    picture_uuid = uuid4()
    url_id = id_generator()

    cursor.execute("""
            INSERT INTO urls
            (url, uuid, url_id)
            VALUES
            ('{}', '{}', '{}')
            """.format(url, picture_uuid, url_id))
    db.commit()
    return picture_uuid, url_id

def main():
    database_connection = sqlite3.connect('database.sqlite')
    try:
        setup_database(database_connection)
    except:
        raise

    try:
        picture_uuid, url_id = insert_url(database_connection, sys.argv[1])
    except:
        raise

if __name__ == "__main__":
    main()
