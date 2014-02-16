#!/usr/bin/env python
# -*- coding: utf-8 -*-

from shoutpy import ShoutcastDirectory, Station, Storage
import logging
import multiprocessing
import time
import re
import random


# def fetch(x):
#     return x*x


# def fetcher(stations, s_id):
#     time.sleep(random.randint(10))
#     return s_id, stations[s_id].update_history()


def main():
    logger = logging.getLogger('FetcherMain')

    logger.info('Starting up!')
    shoutcast = ShoutcastDirectory()

    stations = {}

    for line in open('genres.txt', 'r'):
        genre = line.strip()
        logger.info('Fetching stations of genre: %s' % genre)
        genre_stations = shoutcast.get_genre_top_stations(genre)
        for station_url in genre_stations:
            m = re.search('\?id=([0-9]*)', station_url)
            if not m:
                logger.warn('id not found: %s' % station_url)
                continue
            station_id = m.group(1)

            streaming_urls = shoutcast.get_station_urls(station_url)
            for i, url in enumerate(streaming_urls):
                if re.match('http://[0-9.:]*$', url):
                    logger.info('%s:%s => %s' % (station_id, i, url))
                    stations['%s:%s' % (station_id, i)] = url
                else:
                    logger.warn('Skipping station %s' % url)
            time.sleep(5)

    logger.info('Collected %d stations' % len(stations))
    storage = Storage('output')
    logger.info('Starting fetch process...')
    station_objects = []
    for s_id, url in stations.iteritems():
        station = Station(s_id, url, storage)
        station_objects.append(station)
        station.fetch_metadata()

    logger.debug('Prepare fetching...')
    while True:
        for s in station_objects:
            s.update_history()
    logger.info('Fetching stopped!')


if __name__ == '__main__':
    logging.basicConfig(format=u'%(asctime)s %(levelname)-8s %(name)s: %(message)s', level=logging.DEBUG)
    main()