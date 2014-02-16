#!/usr/bin/env python
# -*- coding: utf-8 -*-

import mechanize
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import logging

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1700.68 YaBrowser/14.2.1700.8703 Safari/537.36'


class Station(object):

    def __init__(self, station_id, url, storage=None, max_length=100):
        self._id = station_id
        self._url = url
        self._history = []
        self._max_length = max_length
        self._storage = storage
        self._browser = mechanize.Browser()
        self._browser.addheaders = [('User-Agent', USER_AGENT)]
        self._logger = logging.getLogger('Station-%s' % station_id)
        self.stored_meta = False

    def get_id(self):
        return self._id

    def fetch_metadata(self):
        self._logger.debug('Fetching metadata...')
        response = self._browser.open('%s/index.html' % self._url)
        if response.code != 200:
            self._logger.error('Failed to fetch metadata: returned http %d' % response.code)
            return None
        soup = BeautifulSoup(response.read())
        tables = soup.find_all('table')
        if len(tables) == 0:
            self._logger.error('Failed to fetch metadata: no tables found')
            return None
        status_html = str(tables[3])
        soup2 = BeautifulSoup(status_html)
        cells = soup2.find_all('td')
        title = cells[9].find('b').find(text=True)
        self._logger.debug('Station title: %s' % title)
        genre = cells[13].find('b').find(text=True)
        self._logger.debug('Station genre: %s' % genre)
        url = cells[15].find('a', href=True)['href']
        self._logger.debug('Station url: %s' % url)
        self._storage.store_meta(self._id, {'title': title, 'genre': genre, 'url': url})
        self.stored_meta = True
        return {'title': title, 'genre': genre, 'url': url}

    def _fetch_current_playlist(self):
        self._logger.debug('Fetching current playlist...')
        response = self._browser.open('%s/played.html' % self._url)
        if response.code != 200:
            self._logger.error('Failed to fetch playlist: returned http %d' % response.code)
            return
        soup = BeautifulSoup(response.read())
        tables = soup.find_all('table')
        if len(tables) == 0:
            self._logger.error('Failed to fetch playlist: no tables found')
            return
        playlist_html = str(tables[2])
        soup2 = BeautifulSoup(playlist_html)
        cells = soup2.find_all('td')
        result = []
        for i, c in enumerate(cells):
            if i in {0, 1, 4}:
                continue
            result.append(c.find(text=True))
        if len(result) == 0:
            self._logger.error('Failed to fetch playlist: no history detected!')
            return
        first_time = datetime.strptime(result[0], '%H:%M:%S')
        now = datetime.now()
        delta = now - first_time
        hours_distance = (delta.seconds / 3600) % 24
        now_fixed = now - timedelta(seconds=(delta - timedelta(hours=hours_distance)).seconds)

        self._logger.debug('Found %d history items' % (len(result) / 2))
        for i in xrange(len(result) / 2):
            ts_raw = datetime.strptime(result[2*i], '%H:%M:%S')
            delta = first_time - ts_raw
            ts = now_fixed - delta
            ts -= timedelta(microseconds=ts.microsecond)  # drop resolution to seconds
            yield (result[2*i], ts, result[2*i+1])

    def _merge_playlist_to_history(self, playlist):
        if len(self._history) == 0:
            return playlist[::-1]
        result = list(self._history)
        first_time = self._history[-1][1]
        for played_track in playlist[::-1]:
            track_time = played_track[1]
            if track_time > first_time:
                result.append(played_track)
        return result

    def _new_tracks(self, playlist):
        if len(self._history) == 0:
            return playlist[::-1]
        result = []
        first_time = self._history[-1][1]
        for played_track in playlist[::-1]:
            track_time = played_track[1]
            if track_time > first_time:
                result.append(played_track)
        return result

    def update_history(self):
        playlist = list(self._fetch_current_playlist())
        new_tracks = self._new_tracks(playlist)
        if self._storage and len(new_tracks) > 0:
            self._logger.info('Have %d new tracks in history' % len(new_tracks))
            self._storage.store(self._id, ['%s,%s,%s' % (p[0], p[1], p[2]) for p in new_tracks])
            for p in new_tracks:
                self._logger.debug('New track: at %s: %s' % (p[0], p[2]))
        self._history = self._merge_playlist_to_history(playlist)
        if len(self._history) > self._max_length:
            self._history = self._history[(len(self._history)-self._max_length):]
        return new_tracks

    def get_history(self):
        for track in self._history:
            yield track