#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Hans-Peter Jansen <hpj@urpla.net>
# License: GNU GPL 2 - see http://www.gnu.org/licenses/gpl2.txt for details
# vim:set et ts=8 sw=4:

import os
import sys
import time
import signal
import locale
import logging
import traceback
import threading

log = logging.getLogger('main')

from config import Config
from dedup import Dedup
from fetch import Fetch

MAIN_DELAY = 0.5
JOIN_TIMEOUT = 1.0

class Main(object):
    def __init__(self):
        # process command line options and load config files
        self._config = Config()
        self._threads = []
        self._exiting = False
        self._reload = False

        # signal handling
        for sig, action in (
            (signal.SIGINT, self.shutdown),
            (signal.SIGQUIT, self.shutdown),
            (signal.SIGTERM, self.shutdown),
            (signal.SIGHUP, lambda s, f: setattr(self, '_reload', True)),
            (signal.SIGPIPE, signal.SIG_IGN),
        ):
            try:
                signal.signal(sig, action)
            except AttributeError:
                pass

        log.trace(self._config)

    def shutdown(self, sig = None, frame = None):
        log.debug('shutdown(%s, sig: %s)', os.getpid(), sig)
        self._exiting = True
        self.stop_threads()

    def start_threads(self):
        log.debug('start_threads')
        # dedup thread
        dedup = Dedup(self._config)
        t = threading.Thread(target = dedup.run, daemon = True)
        t.start()
        self._threads.append((dedup, t))

        # fetcher threads
        for i in range(self._config.fetch_threads):
            fetch = Fetch(self._config, self._config.fetch_queue)
            t = threading.Thread(target = fetch.run, args = (t.name, ), daemon = True)
            t.start()
            self._threads.append((fetch, t))

    def stop_threads(self):
        log.debug('stop_threads')
        for p, t in self._threads:
            p.exit()
        for p, t in self._threads:
            t.join(timeout = JOIN_TIMEOUT)
        self._threads = []

    def run(self):
        """ main loop """
        ret = 0
        log.info('running (%s)', os.getpid())
        self.start_threads()
        while not self._exiting:
            time.sleep(MAIN_DELAY)
            if self._config.auto_reload and self._config.check_sections_reload():
                self._reload = True
                log.info('reload config')
            if self._reload:
                self.stop_threads()
                self._config.reload()
                self.start_threads()
                log.trace(self._config)
                self._reload = False
        log.info('finished')
        return ret


if __name__ == '__main__':
    # set C locale
    locale.setlocale(locale.LC_ALL, 'C')
    os.environ['LANG'] = 'C'
    ret = 0
    try:
        main = Main()
        ret = main.run()
    except SystemExit:
        pass
    except KeyboardInterrupt:
        log.info('terminated by ^C')
        ret = 4
    except:
        exc_type, exc_value, tb = sys.exc_info()
        log.error('internal error: %s',
            ''.join(traceback.format_exception(exc_type, exc_value, tb)))
        ret = 8
    sys.exit(ret)
