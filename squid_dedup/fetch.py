# -*- coding: utf-8 -*-

# Author: Hans-Peter Jansen <hpj@urpla.net>
# License: GNU GPL 2 - see http://www.gnu.org/licenses/gpl2.txt for details
# vim:set et ts=8 sw=4:

import time
import queue
import urllib
import urllib.request
import logging
from collections import defaultdict

log = logging.getLogger('fetch')

BLOCKSIZE = 8192
QUEUE_TIMEOUT = 0.5

class Fetch:

    _done = defaultdict(set)

    """ fetch objects from queue """
    def __init__(self, config, queue):
        self._config = config
        self._queue = queue
        self._exiting = False

        self._delay = config.fetch_delay

        # prepare proxies
        proxies = {}
        if self._config.http_proxy:
            proxies['http'] = self._config.http_proxy
        if self._config.https_proxy:
            proxies['https'] = self._config.https_proxy
        if proxies:
            proxy_support = urllib.request.ProxyHandler(proxies)
            opener = urllib.request.build_opener(proxy_support)
            urllib.request.install_opener(opener)

    def exit(self):
        self._exiting = True

    def run(self, name):
        log.debug('%s: running', name)
        while not self._exiting:
            try:
                newurl, url = self._queue.get(timeout = QUEUE_TIMEOUT)
            except queue.Empty:
                continue
            log.debug('%s: %s, %s', name, newurl, url)
            if newurl in Fetch._done:
                Fetch._done[newurl].add(url)
                log.debug('%s: %s is fetched already: %s', name, url, newurl)
                log.trace('%s: %s', Fetch._done[newurl])
                continue
            Fetch._done[newurl].add(url)
            time.sleep(self._delay)
            try:
                response = urllib.request.urlopen(url)
            except urllib.error.URLError as e:
                log.error('%s: open <%s> failed: %s', name, url, e)
            else:
                # check, if object is cached already
                header = response.info()
                log.trace('%s: %s\n%s', name, url, header)
                try:
                    xcache = header['X-Cache']
                except KeyError:
                    pass
                else:
                    if xcache.startswith('HIT'):
                        log.debug('%s: %s is cached already', name, url)
                        continue
                # object isn't fetched already, do it now
                log.debug('%s: fetching %s', name, url)
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
