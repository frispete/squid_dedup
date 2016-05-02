# -*- coding: utf-8 -*-

# Author: Hans-Peter Jansen <hpj@urpla.net>
# License: GNU GPL 2 - see http://www.gnu.org/licenses/gpl2.txt for details
# vim:set et ts=8 sw=4:

import queue
import urllib
import urllib.request
import logging
import threading

log = logging.getLogger('fetch')

BLOCKSIZE = 8192

class Fetch(threading.Thread):
    """ fetch objects from queue """
    def __init__(self, queue):
        self._queue = queue
        super().__init__()
        self._stop_event = threading.Event()
        self.setDaemon(True)

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.isSet()

    def run(self):
        while not self.stopped():
            try:
                url = self._queue.get(timeout = 0.5)
            except queue.Empty:
                continue
            log.debug('%s: fetch <%s>', self.name, url)
            try:
                response = urllib.request.urlopen(url)
            except urllib.error.URLError as e:
                log.error('open <%s> failed: %s', url, e)
            else:
                log.trace(response.info())
                while not self.stopped():
                    try:
                        data = response.read(BLOCKSIZE)
                    except Exception as e:
                        log.error('read <%s> failed: %s', url, e)
                    else:
                        if not data:
                            break
                if not self.stopped():
                    log.info('fetched <%s>', url)
        log.debug('%s: fetch stopped', self.name)
