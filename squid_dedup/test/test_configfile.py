# -*- coding: utf-8 -*-

# Author: Hans-Peter Jansen <hpj@urpla.net>
# License: GNU GPL 2 - see http://www.gnu.org/licenses/gpl2.txt for details
# vim:set et ts=8 sw=4:

import os
import sys

from unittest import TestCase

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from lib import configfile

class TestConfigFile(TestCase):

    def test(self):
        cfdata = '''
# Config file

[global]

# delay (in seconds)
delay: 2

# Comma separated list of additional config file patterns
include: ./conf/*.conf, /etc/cfgfile/*.conf

# Log level (one of: CRITICAL, ERROR, WARNING, INFO, DEBUG, TRACE)
loglevel: TRACE

# Log to this file (or to console, if unset or '-')
logfile: -

# utf-8 stuff
utf8: äöüÄÖÜß

bool_true: true
bool_false: false
bool_yes: Yes
bool_no: No
bool_on: oN
bool_off: oFF
bool_1: 1
bool_0: 0

fail_int: 1.1
fail_float: 1f6

multiline:
    first
    second
    third
'''
        cf = configfile.ConfigFile()
        cf.read_string(cfdata, 'test_configfile')
        rval = cf.getint('global', 'delay')
        self.assertEqual(rval, 2)
        rval = cf.getlist('global', 'include')
        self.assertEqual(rval, ['./conf/*.conf', '/etc/cfgfile/*.conf'])
        rval = cf.get('global', 'loglevel')
        self.assertEqual(rval, 'TRACE')
        rval = cf.get('global', 'logfile')
        self.assertEqual(rval, '-')
        rval = cf.get('global', 'utf8')
        self.assertEqual(rval, 'äöüÄÖÜß')

        # test exceptions
        self.assertRaises(configfile.ConfigFileError,
                          configfile.ConfigFile, filename = 'notexistent.conf')
        self.assertRaises(configfile.ConfigFileError,
                          cf.read, 'notexitent.conf')
        self.assertRaises(configfile.ConfigFileError,
                          cf.get, 'global', 'delay', allowed = (1, 3, 5))
        self.assertRaises(ValueError,
                          cf.getint, 'global', 'fail_int')
        self.assertRaises(ValueError,
                          cf.getfloat, 'global', 'fail_float')

        # test bool values
        rval = cf.getbool('global', 'bool_true')
        self.assertEqual(rval, True)
        rval = cf.getbool('global', 'bool_false')
        self.assertEqual(rval, False)
        rval = cf.getbool('global', 'bool_yes')
        self.assertEqual(rval, True)
        rval = cf.getbool('global', 'bool_no')
        self.assertEqual(rval, False)
        rval = cf.getbool('global', 'bool_on')
        self.assertEqual(rval, True)
        rval = cf.getbool('global', 'bool_off')
        self.assertEqual(rval, False)
        rval = cf.getbool('global', 'bool_1')
        self.assertEqual(rval, True)
        rval = cf.getbool('global', 'bool_0')
        self.assertEqual(rval, False)

        # test list values
        rval = cf.getlist('global', 'multiline', splitter = '\n')
        self.assertEqual(rval, ['first', 'second', 'third'])

        # test default values
        rval = cf.get('global', 'undefined')
        self.assertEqual(rval, None)
        rval = cf.get('global', 'undefined', 'default')
        self.assertEqual(rval, 'default')
        rval = cf.getbool('global', 'undefined', False)
        self.assertEqual(rval, False)
        rval = cf.getbool('global', 'undefined', True)
        self.assertEqual(rval, True)
