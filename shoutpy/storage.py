#!/usr/bin/env python
# -*- coding: utf-8 -*-

import multiprocessing
import logging


class Storage(object):

    def __init__(self, output_dir):
        self._meta_file = open('%s/metadata.csv' % output_dir, 'w')
        self._meta_file.write('station,genre,url,title\n')
        self._meta_file.flush()

        self._stream_file = open('%s/stream.csv' % output_dir, 'a')
        self._stream_file.write('station,timestamp,track\n')
        self._lock = multiprocessing.Lock()
        self._meta_lock = multiprocessing.Lock()
        self._logger = logging.getLogger('Storage')
        self._logger.info('Initialized storage writing to %s' % output_dir)

    def __del__(self):
        self._meta_file.close()
        self._stream_file.close()

    def store_meta(self, station_id, metadata):
        self._logger.debug('Storing metadata from station %s: waiting for lock...' % station_id)
        with self._meta_lock:
            self._meta_file.writelines(['%s,%s,%s,%s\n' %
                                        (station_id, r['genre'], r['url'], r['title']) for r in metadata])
            self._meta_file.flush()

    def store(self, station_id, playlist):
        self._logger.debug('Storing playlist from station %s: waiting for lock...' % station_id)
        with self._lock:
            self._logger.debug('Storing %d songs from station %s...' % (len(playlist), station_id))
            self._stream_file.writelines(['%s,%s\n' % (station_id, p) for p in playlist])
            self._stream_file.flush()
            self._logger.info('%d songs from station %s stored!' % (len(playlist), station_id))

