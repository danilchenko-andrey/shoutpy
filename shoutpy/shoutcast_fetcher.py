#!/usr/bin/env python
# -*- coding: utf-8 -*-
import cookielib

import mechanize
from bs4 import BeautifulSoup
import logging


_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1700.68 YaBrowser/14.2.1700.8703 Safari/537.36'


def _set_m3u(browser, url):
    browser.open(url)
    browser.select_form(name='form1')
    browser['player'] = ['others']
    browser.submit()


class ShoutcastDirectory(object):

    def __init__(self):
        self._logger = logging.getLogger('ShoutcastDirectory')
        self._logger.debug('Initializing browser...')
        self._browser = mechanize.Browser()
        cj = cookielib.LWPCookieJar()
        self._browser.set_cookiejar(cj)
        self._browser.addheaders = [('User-Agent', _USER_AGENT)]
        self._logger.debug('Updating settings...')
        _set_m3u(self._browser, 'http://shoutcast.com/settings')
        self._logger.info('Initialized!')

    def get_top_genres(self):
        self._logger.debug('Getting genres list...')
        response = self._browser.open('http://www.shoutcast.com/')
        soup = BeautifulSoup(response.read())
        for li in soup.find_all('li', {'class': 'prigen'}):
            yield li.find('a').find(text=True)

    def get_genre_top_stations(self, genre):
        response = self._browser.open('http://www.shoutcast.com/radio/%s' % genre.replace(' ', '%20'))
        soup = BeautifulSoup(response.read())
        for container in soup.find_all('div', {'class': 'thumbnail'}):
            yield container.find('a', href=True)['href']

    def get_station_urls(self, url):
        response = self._browser.open(url)
        lines = response.readlines()
        for line in lines[1:]:
            parts = line.strip().split('=', 1)
            if parts[0].startswith('File'):
                yield parts[1]









