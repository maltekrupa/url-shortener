import logging
import time
import os
import io

from selenium import webdriver
from PIL import Image

import psycopg2
import psycopg2.extras

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

driver = webdriver.PhantomJS(
        service_args=['--ignore-ssl-errors=true'],
        executable_path='./phantomjs'
        )
driver.accept_untrusted_certs = True
driver.set_window_size(1366, 768)
driver.execute_script('document.body.style.background = "white"')


def get_urls(db):
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


def preview_exists(url_id):
    pwd = os.path.abspath("images")
    filename = pwd + "/" + str(url_id) + '.jpg'
    if os.path.isfile(filename):
        return True
    else:
        return False


def create_image_for_url(url_id, url):
    log.info("Grabbing image for {}.".format(url_id))
    driver.get(url)
    screen = driver.get_screenshot_as_png()
    image_object = io.BytesIO(screen)
    im = Image.open(image_object)
    im.save("images/{}.jpg".format(url_id), "JPEG", optimize=True, quality=80)
    log.info("Saved image for {}.".format(url_id))


def main():
    while True:
        try:
            urls = get_urls(database_connection)
        except Exception as e:
            log.error(e)
            time.sleep(0.5)
            continue

        for url in urls:
            try:
                if not preview_exists(url['id']):
                    create_image_for_url(url['id'], url['url'])
            except Exception as e:
                log.error(e)
                raise
                time.sleep(0.5)
                continue

        time.sleep(0.5)
        log.debug("Found no new urls.")


if __name__ == '__main__':
    log.info("I'm alive")

    database_connection = psycopg2.connect("dbname=urls user=postgres")
    main()
