#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Hans-Peter Jansen <hpj@urpla.net>
# License: GNU GPL 2 - see http://www.gnu.org/licenses/gpl2.txt for details
# vim:set et ts=8 sw=4:

import os
import sys
import locale
import logging
import traceback

from squid_dedup.config import Config
from squid_dedup.main import Main

log = logging.getLogger('start')


if __name__ == '__main__':
    # add basedir to sys.path
    if Config.appdir not in sys.path:
        sys.path.insert(0, Config.appdir)

    # set C locale
    locale.setlocale(locale.LC_ALL, 'C')
    os.environ['LANG'] = 'C'

    # process command line options and load config file
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
