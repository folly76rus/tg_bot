import re
import os.path
import requests
from urllib.parse import urlparse
import xml.etree.ElementTree as et


class RusTattoo:
    url = 'http://rustattoo.ru/system/tattoo-rss.xml'

    def __init__(self, sql_lighter):
        # инициализируем соединение с БД
        self.db = sql_lighter

    def new_publication(self):
        new = {}
        root = et.fromstring(requests.get(self.url).content.decode('utf-8'))
        for item in root.iter('item'):
            if self.db.publication_exists(item.find('id').text) == False:
                new = {'id': item.find('id').text,
                       'link': item.find('link').text,
                       'url_photo': item.find('enclosure').get('url'),
                       'like': 0,
                       'dislike': 0}
                break
        return new

    # def download_image(self, url):
    #     r = requests.get(url, allow_redirects=True)
    #
    #     a = urlparse(url)
    #     filename = os.path.basename(a.path)
    #     open(filename, 'wb').write(r.content)
    #
    #     return filename

    # def update_lastkey(self, new_key):
    #     self.lastkey = new_key
    #
    #     with open(self.lastkey_file, "r+") as f:
    #         data = f.read()
    #         f.seek(0)
    #         f.write(str(new_key))
    #         f.truncate()
    #
    #     return new_key
