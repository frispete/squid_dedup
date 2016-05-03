# -*- coding: utf-8 -*-

# Author: Hans-Peter Jansen <hpj@urpla.net>
# License: GNU GPL 2 - see http://www.gnu.org/licenses/gpl2.txt for details
# vim:set et ts=8 sw=4:

import queue
import urllib
import urllib.request
import logging

log = logging.getLogger('fetch')

BLOCKSIZE = 8192
QUEUE_TIMEOUT = 0.5

class Fetch:
    """ fetch objects from queue """
    def __init__(self, config, queue):
        self._config = config
        self._queue = queue
        self._exiting = False

    def exit(self):
        self._exiting = True

    def run(self, name):
        log.debug('%s: running', name)
        while not self._exiting:
            try:
                url = self._queue.get(timeout = QUEUE_TIMEOUT)
            except queue.Empty:
                continue
            log.debug('%s: <%s>', name, url)
            try:
                response = urllib.request.urlopen(url)
            except urllib.error.URLError as e:
                log.error('%s: open <%s> failed: %s', name, url, e)
            else:
                log.trace('%s: %s', self._name, response.info())
                while not self._exiting:
                    try:
                        data = response.read(BLOCKSIZE)
                    except Exception as e:
                        log.error('%s: read <%s> failed: %s', name, url, e)
                    else:
                        if not data:
                            break
                if not self._exiting:
                    log.info('%s: <%s> fetched', name, url)
        log.debug('%s: finished', name)
