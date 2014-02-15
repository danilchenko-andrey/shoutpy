#!/usr/bin/env python
# -*- coding: utf-8 -*-

from shoutpy import ShoutcastDirectory, Station, Storage
import logging
import multiprocessing
import time
import re


queue = multiprocessing.Queue()


def fetcher(n):
    logger = logging.getLogger('Fetcher-%s' % n)
    while True:
        logger.debug('Running...')
        station = queue.get()
        station.update_history()
        queue.task_done()


def scheduler(stations):
    logger = logging.getLogger('Scheduler')
    while True:
        logger.info('Queue size: %d' % queue.qsize())
        if queue.qsize() > len(stations):
            logger.warn('Too big queue size!')
        for s in stations:
            queue.put(s)
        time.sleep(600)


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

    logger.info('Starting fetchers...')
    fetchers = []
    for t in xrange(10):
        fetcher_process = multiprocessing.Process(target=fetcher, args=t)
        fetcher_process.start()
        fetchers.append(fetcher_process)

    try:
        scheduler(station_objects)
    except:
        logger.error('Stopping fetchers!')
        for p in fetchers:
            p.terminate()
        queue.close()
    logger.info('Fetching stopped!')


if __name__ == '__main__':
    logging.basicConfig(format=u'%(asctime)s %(levelname)-8s %(name)s: %(message)s', level=logging.DEBUG)
    main()