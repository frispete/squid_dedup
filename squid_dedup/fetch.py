# -*- coding: utf-8 -*-

# Author: Hans-Peter Jansen <hpj@urpla.net>
# License: GNU GPL 2 - see http://www.gnu.org/licenses/gpl2.txt for details
# vim:set et ts=8 sw=4:

import os
import logging

from lib import profile
from lib import process

log = logging.getLogger('worker')

class Worker(process.Process):

    @profile.profile(fn = 'checker_${date}_$time')
    def run(self):
        """periodically do some work"""
        super().run()
        log.debug('%s.run(pid: %s)', self.name(), os.getpid())
        config = self.config
        delay = process.Delay(self, config.worker_delay)
        while not self.exiting():
            log.trace('%s.loop()', self.name())
            delay()

    def shutdown(self, sig = None, _ = None):
        """intercept shutdown for clean up"""
        log.debug(  '%s.shutdown(%s, sig = %s)', self.name(), os.getpid(), sig)
        super().shutdown(sig, _)
