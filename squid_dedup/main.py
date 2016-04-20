#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Hans-Peter Jansen <hpj@urpla.net>
# License: GNU GPL 2 - see http://www.gnu.org/licenses/gpl2.txt for details
# vim:set et ts=8 sw=4:

import os
import time
import signal
import logging

log = logging.getLogger('main')


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
        self.config = config
        self.validaddrs = config.validaddrs
        self.loglevel = config.loglevel
        self._processes = []
        self._exiting = False

    def run(self):
        """ main loop """
        ret = 0
        log.info('Main.run(%s)', os.getpid())

        while not self._exiting:
            time.sleep(1)
        log.info('Main.run() finished', )
        return ret

    def shutdown(self, sig, _):
        log.debug('Main.shutdown(%s, sig: %s)', os.getpid(), sig)
        self._exiting = True
        for p in self._processes:
            p.shutdown()
        #for p in self._processes:
        #    p.join()

