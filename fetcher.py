#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from shoutpy import ShoutcastDirectory, Station, Storage
import logging
import time
import re
import sys


def main(genre):
    logger = logging.getLogger('FetcherMain')

    logger.info('Starting up!')
    shoutcast = ShoutcastDirectory()

    stations = {}

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
                break
            else:
                logger.warn('Skipping station %s' % url)
        time.sleep(5)

    logger.info('Collected %d stations' % len(stations))
    os.makedirs('output-%s' % genre)
    storage = Storage('output-%s' % genre)
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
        time.sleep(60)
    logger.info('Fetching stopped!')


if __name__ == '__main__':
    logging.basicConfig(format=u'%(asctime)s %(levelname)-8s %(name)s: %(message)s', level=logging.DEBUG)
    main(sys.argv[1])