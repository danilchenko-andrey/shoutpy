#!/usr/bin/env python
# -*- coding: utf-8 -*-

from shoutpy import ShoutcastDirectory, Station, Storage
import logging
import multiprocessing
import time
import re
import random


def fetch(station):
    time.sleep(random.randint(10))
    if not station.stored_meta:
        station.fetch_metadata()
    station.update_history()
    time.sleep(1)


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
        station_objects.append(Station(s_id, url, storage))

    logger.info('Starting scheduler..')
    pool = multiprocessing.Pool(10)
    while True:
        logger.debug('Prepare fetching...')
        pool.map(fetch, station_objects)
        logger.info('Fetch finished!')
        time.sleep(60)
    logger.info('Fetching stopped!')


if __name__ == '__main__':
    logging.basicConfig(format=u'%(asctime)s %(levelname)-8s %(name)s: %(message)s', level=logging.DEBUG)
    main()