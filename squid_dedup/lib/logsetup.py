# -*- coding: utf-8 -*-

# Author: Hans-Peter Jansen <hpj@urpla.net>
# License: GNU GPL 2 - see http://www.gnu.org/licenses/gpl2.txt for details
# vim:set et ts=8 sw=4:

import logging
import logging.handlers
import collections

# add a new log level: trace
TRACE = 5
logging.addLevelName(TRACE, 'TRACE')

def trace(self, message, *args, **kws):
    self.log(TRACE, message, *args, **kws)

logging.Logger.trace = trace
logging.TRACE = TRACE

# ordered log level mapping
loglevel_map = collections.OrderedDict((
    ('CRITICAL', 50),
    ('ERROR', 40),
    ('WARNING', 30),
    ('INFO', 20),
    ('DEBUG', 10),
    ('TRACE', 5),
))

loglevel_list = loglevel_map.keys()

loglevel_nummap = dict([(v, k) for k, v in loglevel_map.items()])


def loglevel(value):
    """ log level value might be literal, numeric, or a numeric string """
    try:
        return loglevel_map[value]
    except KeyError:
        try:
            value = int(value)
        except (ValueError, TypeError):
            pass
        if value in loglevel_nummap:
            return value


def loglevel_str(value):
    ll = loglevel(value)
    if ll is not None:
        return loglevel_nummap[ll]


# logging optimizations
logging._srcfile = None
#logging.logThreads = 0
#logging.logProcesses = 0


def logsetup(loglevel=logging.WARN, logfile=None, sysloglevel=None):
    #print('logsetup(%s, %s, %s)' % (loglevel, logfile, sysloglevel))
    logformat = '%(asctime)s.%(msecs)03d %(levelname)5s: [%(name)s] %(message)s'
    syslogformat = '%(name)s[%(process)d]: %(levelname)s: %(message)s'
    dateformat = '%Y-%m-%d %H:%M:%S'

    # setup logging: revert any previous logging settings
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # basic logging setup
    logconfig = dict(
        level = loglevel,
        format = logformat,
        datefmt = dateformat,
    )

    if logfile not in (None, '-'):
        logconfig['filename'] = logfile
    logging.basicConfig(**logconfig)

    # log errors to syslog, if specified
    if sysloglevel:
        syslog = logging.handlers.SysLogHandler(address = '/dev/log')
        syslog.setLevel(sysloglevel)
        formatter = logging.Formatter(syslogformat)
        syslog.setFormatter(formatter)
        logging.getLogger().addHandler(syslog)

