import requests
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
            if not self.db.publication_exists(item.find('id').text):
                new = {'id': item.find('id').text,
                       'link': item.find('link').text,
                       'url_photo': item.find('enclosure').get('url'),
                       'like': 0,
                       'dislike': 0}
                break
        return new
