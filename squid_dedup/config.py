#!/usr/bin/env python3
# -*- coding: utf8 -*
"""
Synopsis:
%(appname)s

Usage: %(appname)s [-%(cmdlin_options)s]%(cmdlin_parmsg)s
       -h, --help           this text
       -V, --version        print version and exit
       -v, --verbose        raises loglevel
                            [by default, only errors and warnings are logged]
                            -v:   informal messages
                            -vv:  debugging
       -c, --cfgfile=file   specify config file, builtin defaults are used
                            otherwise
       -l, --logfile=file   specify log file, '-' for console.
                            [default: %(logfile)s]
       -p, --profile        enable profiling code, pstats files are saved to
                            %(profiledir)s
       -x, --extract        extract built-in config file to current directory
                            if a filename is given, only that one is extracted

You can generate an example config file in current directory with the option -x.

Command line parameter take precedence over config file parameter.

Copyright: %(copyright)s
License: %(license)s.
"""

__version__ = '0.0.1'
__verdate__ = '20160420'
__author__ = 'Hans-Peter Jansen <hpj@urpla.net>'
__copyright__ = '(c)2016 ' + __author__
__license__ = 'GNU GPL 2 - see http://www.gnu.org/licenses/gpl2.txt for details'


__builtincfg__ = """\
# %(cfgfile)s: config file for %(appname)s V.[%(version)s/%(verdate)s]

[global]

# comma separated list of allowed IPv4 addresses in CIDR notation
validaddrs: %(validaddrs_csv)s

# additional config files
include: %(include)s

# log level
# 50: critical errors only
# 40: errors
# 30: warnings
# 20: info
# 10: debug
loglevel: %(loglevel)s

# Log to this file (or - to log to console)
logfile: %(logfile)s

# profiling
profile: %(profile)s
profiledir: %(profiledir)s

# Copyright: %(copyright)s
# License: %(license)s
# end of %(cfgfile)s
"""

import os
import sys
import getopt
import socket
import logging
import netaddr
import traceback

from configparser import ConfigParser
from collections import OrderedDict

# add project basedir to sys.path, if this module is executed standalone
# in order to avoid relative paths
if __name__ == '__main__':
    basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if basedir not in sys.path:
        sys.path.insert(0, basedir)

import lib.asciify


# setup  logging
log = logging.getLogger('config')

TRACE = 5       # add a new debug level
logging.addLevelName(TRACE, 'TRACE')

def trace(self, message, *args, **kws):
    self.log(TRACE, message, *args, **kws)
logging.Logger.trace = trace
logging.TRACE = TRACE
#some logging optimizations
logging._srcfile = None
#logging.logThreads = 0
#logging.logProcesses = 0


def out(arg):
    err(arg, sys.stdout)


def err(arg, ch = sys.stderr):
    if arg:
        ch.write(arg)
        if arg[-1] != '\n':
            ch.write('\n')
    else:
        ch.write('\n')
    ch.flush()


def exit(ret = 0, msg = None):
    if msg:
        err(msg)
    sys.exit(ret)


def splitstr(msg, splitter = ','):
    return [s for s in map(lambda s: s.strip(), msg.split(splitter)) if s]


class ConfigBaseError(Exception):
    pass

# derive from ConfigParser in order to avoid issues with values
# containing % due to the magical interpolation feature
# note: ConfigParser is not a new style class
class ConfigBase(ConfigParser):
    """A ConfigParser implementation, that keeps the section order intact"""
    def __init__(self):
        ConfigParser.__init__(self, dict_type = OrderedDict)

    def get(self, section, option, default = None, allowed = None):
        if ConfigParser.has_option(self, section, option):
            value = ConfigParser.get(self, section, option)
            if allowed is not None:
                if value in allowed:
                    default = value
                else:
                    raise ConfigBaseError('invalid value \'%s\' for %s:%s (allowed: %s)' % (
                                                     value, section, option, ', '.join(allowed)))
            else:
                default = value
        return default

    def getlist(self, section, option, default = None, splitter = ','):
        """ convert a splitter separated option value to a list """
        if default is None:
            default = []
        if ConfigParser.has_option(self, section, option):
            default = ConfigParser.get(self, section, option).strip()
            # special case: split on newlines: remove any carriage returns
            if splitter == '\n':
                default = default.replace('\r', '')
            default = default.split(splitter)
            # eliminate empty values
            default = [val for val in map(lambda v: v.strip(), default) if val]
        return default

    def getbin(self, section, option, default = None):
        if ConfigParser.has_option(self, section, option):
            default = ConfigParser.get(self, section, option).decode('string_escape')
        return default

    def getbool(self, section, option, default = None):
        """ short version of getboolean """
        if ConfigParser.has_option(self, section, option):
            default = ConfigParser.getboolean(self, section, option)
        return default
    getboolean = getbool

    def getint(self, section, option, default = None):
        if ConfigParser.has_option(self, section, option):
            # convert int values with automatic base selection
            default = int(ConfigParser.get(self, section, option), 0)
        return default


class ConfigError(ConfigBaseError):
    pass

class Config(ConfigBase):
    """Central configuration class"""
    # internal
    if __name__ == '__main__':
        # for testing purposes
        appdir, appname = '.', 'dcc'
    else:
        appdir, appname = os.path.split(sys.argv[0])
    if appdir in ('', '.'):
        appdir = os.getcwd()
    if appname.endswith('.py'):
        appname = appname[:-3]
    version = __version__
    verdate = __verdate__
    author = __author__
    copyright = __copyright__
    license = __license__

    pid = os.getpid()
    hostname = socket.getfqdn()
    if hostname.endswith('.lisa.loc'):
        TESTING = True
    else:
        TESTING = False
    PRODUCTION = not TESTING

    # network parameter
    validaddrs = ['0/0']

    # config files and logging parameter
    cfgfile = '%s.conf' % appname
    if TESTING:
        logfile = '-'
        loglevel = logging.INFO
    else:
        logfile = 'logs/%s.log' % appname
        loglevel = logging.INFO
    db_loglevel = loglevel

    # internal
    include = []

    # profiling
    profile = False
    profiledir = os.path.join(appdir, 'profiles')

    # command line parameter
    cmdlin_options = 'hVvxps'
    cmdlin_paropt = 'a:c:l:t:u:g:m:d:'
    cmdlin_parmsg = '[-c cfg][-l log][-t timeout][-u uid][-g gid][-m umask][-d dir]'
    cmdlin_longopt = ('help', 'version', 'verbose', 'extract', 'profile',
                      'action', 'simulate', 'cfgfile=', 'logfile=', 'timeout=',
                      'uid=', 'gid=', 'umask=', 'chdir=',
                     )

    def __init__(self):
        """load config file and process command line parameter"""
        ConfigBase.__init__(self)
        # transfer class vars to instance __dict__
        for attr, value in Config.__dict__.items():
            if not attr.startswith('__') and not callable(value):
                self.__dict__[attr] = value

        # process command line
        try:
            optlist, args = getopt.getopt(sys.argv[1:],
                self.cmdlin_options + self.cmdlin_paropt, self.cmdlin_longopt)
        except getopt.error as msg:
            exit(1, '%s: %s' % (self.appname, msg))

        #err('optlist: %s\nargs: %s\n' % (optlist, args))

        self.setuplog()

        # process exiting command line parameter
        for opt, par in optlist:
            if opt in ('-h', '--help'):
                exit(0, self.usage())
            elif opt in ('-V', '--version'):
                exit(0, 'version: %s/%s' % (self.version, self.verdate))
            elif opt in ('-x', '--extract'):
                if args:
                    cfgfile = args.pop(0)
                else:
                    cfgfile = None
                if cfgfile == self.cfgfile:
                    self.write_cfgfile(self.cfgfile, self.builtin_cfg())
                self.write_cfgfiles(cfgfile)
                exit(0)
            # non default cfgfile given?
            elif opt in ('-c', '--cfgfile'):
                if not os.access(par, os.R_OK):
                    exit(1, '%s: cannot read config file \'%s\'' % (self.appname, par))
                self.cfgfile = par

        # load primary config file
        try:
            self.load(self.cfgfile)
        except Exception as e:
            exc_type, exc_value, tb = sys.exc_info()
            log.error('load: %s', ''.join(traceback.format_exception(exc_type, exc_value, tb)))
            exit(2, '%s: %s' % (self.appname, e))

        # process command line parameter
        for opt, par in optlist:
            if opt in ('-v', '--verbose'):
                if self.loglevel > logging.DEBUG:
                    self.loglevel -= 10
                else:
                    if self.loglevel == logging.DEBUG:
                        # global log level: TRACE
                        self.loglevel = logging.TRACE
            elif opt in ('-l', '--logfile'):
                self.logfile = par
            elif opt in ('-p', '--profile'):
                self.profile = True

        # static options processed, setup config and logging
        self.setup()

        # load auxilliary config files
        for include in self.include:
            #log.trace('__init__(include: %s)', include)
            try:
                self.load_include(include)
            except Exception as e:
                #exc_type, exc_value, tb = sys.exc_info()
                #log.error('load_include: %s',
                #          ''.join(traceback.format_exception(exc_type, exc_value, tb)))
                exit(3, '%s: %s' % (self.appname, e))

        # process sections of objects
        try:
            self.process_sections()
        except Exception as e:
            exit(4, '%s: %s' % (self.appname, e))


    def load(self, cfgfile):
        """read main config file"""
        log.debug('load(%s)', cfgfile)
        if not self.read(cfgfile):
            log.error('config file %s not found', cfgfile)
            exit(3)

        # process global section

        self.validaddrs = map(netaddr.IPNetwork, self.getlist('global', 'validaddrs', self.validaddrs))

        # loglevel and file
        self.loglevel = self.getint('global', 'loglevel', self.loglevel)
        self.logfile = self.get('global', 'logfile', self.logfile)
        self.setuplog()

        # profiling
        self.profile = self.getbool('global', 'profile', self.profile)
        self.profiledir = self.get('global', 'profiledir', self.profiledir)

        # fetch includes
        for section in self.sections():
            for include in self.getlist(section, 'include'):
                log.trace('load(include: %s)', include)
                self.include.append(include)

        # check mandatory parameter
        for var, msg in (
            ('validaddrs', 'no valid addresses defined'),
        ):
            if not getattr(self, var):
                exit(2, '%s: %s' % (self.appname, msg))

    def load_include(self, cfgfile):
        """read auxilliary config files"""
        log.debug('load_include(%s)', cfgfile)
        if not self.read(cfgfile):
            log.error('config file %s not found', cfgfile)
            exit(3)

    def process_sections(self):
        # process object sections
        for section in self.sections():
            for prefix, (objdict, handler, _) in self._include_dispatch.items():
                done = False
                if section.startswith('%s_' % prefix):
                    obj = handler(self, section)
                    other = objdict.get(section)
                    if other:
                        raise ConfigError('invalid attempt to replace exisiting section %s:[%s] (line %s) with %s:[%s] (line %s)' % (
                                           other.__file__, other.name, other.__line__,  obj.__file__, obj.name, obj.__line__))
                    else:
                        log.trace('process_sections(%s)', obj)
                        objdict[section] = obj
                        done = True
                        break
            if done is False and section not in ('global', ):
                sdict = self._sections[section]
                raise ConfigError('invalid section %s:[%s] (line %s)' % (
                                   sdict['__file__'], section, sdict['__line__']))

    def setup(self):

        if self.profile and not os.path.exists(self.profiledir):
            os.makedirs(self.profiledir)

        self.setuplog()

        log.trace('setup(uid: %s, gid: %s, umask: %s, chdir: %s, loglevel: %s, logfile: %s)',
                  self.uid, self.gid, self.umask, self.chdir, self.loglevel, self.logfile)

    def setuplog(self):
        # setup logging: revert any previous logging settings
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        logcfg = dict(
            level = self.loglevel,
            format = '%(asctime)s %(levelname)5s: [%(name)s] %(message)s',
            #datefmt = '%Y-%m-%d %H:%M:%S',
            encoding = 'utf-8'
        )
        if self.logfile != '-':
            logcfg['filename'] = self.logfile
        logging.basicConfig(**logcfg)
        if self.logfile != '-':
            # log errors to console
            console = logging.StreamHandler()
            console.setLevel(logging.ERROR)
            formatter = logging.Formatter(logcfg['format'])
            console.setFormatter(formatter)
            logging.getLogger().addHandler(console)

    def builtin_cfg(self):
        # return built-in config file data with current settings adopted

        self.validaddrs_csv = ', '.join(map(str, self.validaddrs))
        self.include_csv = ', '.join(['%s.conf' % key for key in self._include_dispatch.keys()])
        return __builtincfg__ % self.__dict__

    def write_cfgfiles(self, cfgfile = None):
        for prefix, (_, _, cfg) in self._include_dispatch.items():
            self.prefix = prefix
            if cfgfile and cfgfile != '%s.conf' % prefix:
                continue
            self.write_cfgfile('%s.conf' % prefix, cfg % self.__dict__)

    def write_cfgfile(self, cfgfile, cfg):
        if os.path.exists(cfgfile):
            os.rename(cfgfile, cfgfile + '~')
            err('keep old %s as %s~' % (cfgfile, cfgfile))
        open(cfgfile, 'w').write(cfg)
        err('config written to: %s' % cfgfile)

    def usage(self):
        return __doc__ % self.__dict__

    def __repr__(self):
        return u'%s(\n%s\n)' % (self.__class__.__name__, lib.asciify.frec(self.__dict__, withunderscores = False))


# main section, only for config debugging purposes
if __name__ == '__main__':
    #Config.loglevel = logging.TRACE
    Config.loglevel = logging.DEBUG
    Config.logfile = '-'
    config = Config()
    log.debug(config)
