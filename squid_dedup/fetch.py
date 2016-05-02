# -*- coding: utf-8 -*-

# Author: Hans-Peter Jansen <hpj@urpla.net>
# License: GNU GPL 2 - see http://www.gnu.org/licenses/gpl2.txt for details
# vim:set et ts=8 sw=4:

import urllib
import urllib.request
import logging
import threading

log = logging.getLogger('fetch')

class Fetch(threading.Thread):
    """ fetch objects from queue """
    def __init__(self, queue):
        self._queue = queue
        super().__init__()

    def run(self):
        while True:
            url = self._queue.get()
            if url is None:
                break
            log.debug('fetch <%s>', url)
            try:
                response = urllib.request.urlopen(url)
            except urllib.error.URLError as e:
                log.error('open <%s> failed: %s', url, e)
            else:
                log.trace(response.info())
                try:
                    response.read()
                except Exception as e:
                    log.error('read <%s> failed: %s', url, e)
                else:
                    log.info('fetched <%s>', url)
