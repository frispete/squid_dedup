# -*- coding: utf-8 -*-

# Author: Hans-Peter Jansen <hpj@urpla.net>
# License: GNU GPL 2 - see http://www.gnu.org/licenses/gpl2.txt for details
# vim:set et ts=8 sw=4:

import os
import time
import signal
import logging
import datetime
import multiprocessing

log = logging.getLogger('process')


class Process(multiprocessing.Process):
    def __init__(self, config, name = None):
        super(Process, self).__init__()
        self._config = config
        self._exit = multiprocessing.Event()
        self._name = name or self.__class__.__name__

    def name(self):
        return self._name

    def exiting(self):
        return self._exit.is_set()

    def shutdown(self, sig = None, _ = None):
        log.debug('Process.shutdown(%s, sig = %s)', os.getpid(), sig)
        self._exit.set()

    def run(self):
        log.debug('Process.run(%s, %s)', self._name, os.getpid())
        # ignore keyboard interrupts
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        # termination signals
        try:
            for s in (signal.SIGINT, signal.SIGQUIT, signal.SIGTERM):
                signal.signal(s, self.shutdown)
        except AttributeError:
            pass


class Delay(object):
    """Delay execution for delay seconds,
    as long as time between construction and instance calls is lower than delay
    returns False, if delay is cancelled (process exiting), and True otherwise
    """
    INTERVAL = 1
    def __init__(self, parent, delay, name = None, interval = INTERVAL):
        self._parent = parent
        self._delay = delay
        self._name = name or parent.name()
        self._interval = interval
        self._end = time.time() + self._delay
        log.trace('Delay(%s, %.1f sec) initialized', self._name, self._delay)

    def end(self):
        return datetime.datetime.fromtimestamp(self._end)

    def __call__(self):
        if not self._parent.exiting():
            dt = self._end - time.time()
            if dt > 0:
                log.trace('Delay(%s): waiting %.1f sec', self._name, dt)
            while dt > 0 and not self._parent.exiting():
                time.sleep(min(dt, self._interval))
                dt = self._end - time.time()
                #log.trace('Delay(%s): %.1f sec', self._name, dt)
            self._end = time.time() + self._delay
        if self._parent.exiting():
            log.trace('Delay(%s): cancelled', self._name)
            return False
        else:
            log.trace('Delay(%s): finished', self._name)
            return True
