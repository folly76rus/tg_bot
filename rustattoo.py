import requests
import xml.etree.ElementTree as et
import re
from datetime import datetime

def converting_filed(field='', value='', br=False):
    """
    Функция для проверки на пустоту поля и преобразования его к выводу в сообщение
    :param field: Поле, которое проверяем и преобразовываем
    :param value: Значение, которое присваиваем полю, в случае если оно пустое
    :param br: Нуэжен ли перевод строки
    :return: Возвращает преобразованную строку
    """
    if field is None and not br:
        new_field = re.escape(value)
    elif field is None and br and value != '':
        new_field = '\n{0}'.format(re.escape(value))
    elif field and not br:
        new_field = re.escape(field)
    elif field and br:
        new_field = '\n{0}'.format(re.escape(field))
    else:
        new_field = ''

    return new_field


def get_date(date):
    new_date = re.findall(r'\d\d\s...\s\d{4}', date)
    new_date = datetime.strptime(str(new_date[0]), '%d %b %Y')
    new_date = new_date.strftime("%d.%m.%Y")
    if new_date:
        return '\n' + re.escape(str(new_date))
    else:
        return None


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
                       'author': converting_filed(item.find('author').text, br=False),
                       'author_url': item.find('authorurl').text,
                       'city': converting_filed(item.find('city').text, br=False),
                       'city_url': item.find('cityurl').text,
                       'description': converting_filed(item.find('description').text, br=True),
                       'pub_date': get_date(item.find('pubDate').text)}
                break
        return new