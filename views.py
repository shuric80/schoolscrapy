#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import sys
import re
import time
import requests
from bs4 import BeautifulSoup
import logging

import model

logger  = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

s = requests.Session()
header = {
     'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'}


def load_school(id, session):
    ## страница школы
    url = 'http://www.edu.ru/schools/catalog/school/{}'.format(id)
    request = session.get(url, headers = header)
    return request.text, request.status_code


def load_catalog(id, page, session):
    #  страница с каталого школ региона
    url = 'http://www.edu.ru/schools/catalog/{}/_page/{}/'.format(id, page)
    request = session.get(url, headers = header)
    return request.text, request.status_code


def load_index_page(session):
    url = 'http://www.edu.ru/schools/catalog/'
    request = session.get(url, headers = header)
    return request.text, request.status_code


def parse_index_page(text):
    soup = BeautifulSoup(text,"html.parser")
    lid = []
    pattern = '/schools/catalog/(\d+)/'
    for line in soup.find_all(href=re.compile('/schools/catalog/\d+/')):
        lid.append(re.findall(pattern, line.get('href')))

    return list(map(lambda x: int(x[0]), lid))


def parse_school_page(text, code):
    soup = BeautifulSoup(text, "html.parser")
    pattern = dict()
    pattern["director"] = u"Директор ([А-Яа-я, ]+)"
    pattern["place"] = u"Принадлежность ([А-Яа-я, ]+)"
    pattern["type"] = u"Тип ([А-Яа-я, ]+)"
    pattern["phone"] = u"Телефон ([0-9\(\)-;\s]+)"
    pattern["address"] = u"Адрес ([0-9а-яА-Я ,-\.]+)"
    pattern["email"] = u"E-mail:\n([\.a-zA-Z0-9@-]+)"
    pattern["site"] = u"Интернет сайт\n\n.+ href=.+(www[\S, @]+)</a>.+"

    text = soup.get_text()

    result = dict()
    result['title'] = soup.find('h1').next
    result['code'] = code

    for k,v in pattern.items():
        try:
            result[k] = re.findall(v, text)[0]
        except IndexError:
            result[k] = None

    return result


def parse_region_page(text):
    soup = BeautifulSoup(text, "html.parser")
    list_id = soup.find_all(href=re.compile('/schools/catalog/school/'))
    pattern = '/schools/catalog/school/(\d+)'
    lid = []

    for line in list_id:
        url  = line.get('href')
        lid.append(int(re.findall(pattern, url)[0]))

    return lid


if __name__ == '__main__':
    logger.info('Start app')
    logger.info('Create database.')
    model.db_init()

    logger.info('Load title page')
    content, code = load_index_page(s)

    if code != 200:
        logger.error('Index page return: {}'.format(code))
        sys.exit(1)

    list_index_regions = parse_index_page(content)
    for index in list_index_regions:
        # пройдемся по страницам, как выходим за пределы номеров страниц, цикл прекращаем.
        for page in range(1,100):
            content, code = load_catalog(index, page, s)

            if code != 200:
                logging.info('Max number page is {}'.format(page))
                break

            list_index_schools = parse_region_page(content)
            # берем коды школ со страницы
            for cid in list_index_schools:
                time.sleep(3)
                content, code = load_school(cid, s)

                if code != 200:
                    logging.error('School page return wrong code:{} \n{}'.format(code, content))
                    continue

                d = parse_school_page(content, cid)
                ret = model.add_school(d)

                if ret:
                    logger.info('Done. New school saved:{}'.format(cid))
                else:
                    logger.error('School didn\'t save. code:{}'.format(cid))
