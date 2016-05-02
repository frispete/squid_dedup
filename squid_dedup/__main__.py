#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Hans-Peter Jansen <hpj@urpla.net>
# License: GNU GPL 2 - see http://www.gnu.org/licenses/gpl2.txt for details
# vim:set et ts=8 sw=4:

import os
import sys
import signal
import locale
import logging
import traceback

log = logging.getLogger('main')

from config import Config
from dedup import Dedup
from fetch import Fetch

class Main(object):
    def __init__(self, config):
        # termination signals
        try:
            for s in (signal.SIGINT, signal.SIGQUIT, signal.SIGTERM):
                signal.signal(s, self.shutdown)
        except AttributeError:
            pass

        # ignore signals
        try:
            for s in (signal.SIGHUP, signal.SIGPIPE):
                signal.signal(s, signal.SIG_IGN)
        except AttributeError:
            pass

        log.trace('Main(%s)', config)
        self._config = config
        self._loglevel = config.loglevel
        self._threads = []
        self._exiting = False

    def run(self):
        """ main loop """
        ret = 0
        log.info('Main.run(%s)', os.getpid())

        if 1:
            for i in range(self._config.fetch_threads):
                fetch = Fetch(self._config.fetch_queue)
                fetch.start()
                self._threads.append(fetch)

        dedup = Dedup(self._config, self._exiting)
        while not self._exiting:
            if not dedup():
                break

        self.shutdown()

        log.info('Main.run() finished', )
        return ret

    def shutdown(self, sig = None, _ = None):
        log.debug('Main.shutdown(%s, sig: %s)', os.getpid(), sig)
        self._exiting = True
        for t in self._threads:
            t.stop()
        for t in self._threads:
            t.join(0.1)
        # forced exit
        os._exit(3)


if __name__ == '__main__':
    # set C locale
    locale.setlocale(locale.LC_ALL, 'C')
    os.environ['LANG'] = 'C'

    # process command line options and load config files
    config = Config()

    ret = 0
    try:
        main = Main(config)
        ret = main.run()
    except KeyboardInterrupt:
        log.info('terminated by ^C')
        ret = 4
    except:
        exc_type, exc_value, tb = sys.exc_info()
        log.error('internal error: %s',
            ''.join(traceback.format_exception(exc_type, exc_value, tb)))
        ret = 8

    sys.exit(ret)
