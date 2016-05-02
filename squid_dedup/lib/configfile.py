# -*- coding: utf-8 -*-

# Author: Hans-Peter Jansen <hpj@urpla.net>
# License: GNU GPL 2 - see http://www.gnu.org/licenses/gpl2.txt for details
# vim:set et ts=8 sw=4:

import io
import configparser

class ConfigFileError(Exception):
    pass

class ConfigFile(configparser.ConfigParser):
    """A ConfigParser featuring a few convenient conversions
     * no section name mangling
     * strict parsing: check section and option duplicates
     * basic interpolation: replace %(var)s style vars from defaults
       Note: ConfigParser allows for string based replacement values
             only, therefor we're cleaning up the defaults mapping
    """
    ENCODING = 'utf8'

    # don't mangle section names
    optionxform = str

    def __init__(self, defaults = None, filename = None):
        self.filename = filename
        super().__init__(defaults = self._cleanup_defaults(defaults), strict = True)
        if filename is not None:
            self.read(filename)

    def read(self, filename, encoding = ENCODING, errors = 'replace'):
        try:
            fd = open(filename, encoding = encoding, errors = errors)
        except OSError as e:
            raise ConfigFileError('open failed: %s' % (e))
        self.filename = filename
        self.read_file(fd, filename)

    def read_file(self, fd, filename = None):
        try:
            super().read_file(fd, filename)
        except configparser.Error as e:
            raise ConfigFileError('read failed: %s' % (e))

    def read_string(self, string, filename = '<string>'):
        fd = io.StringIO(string)
        self.read_file(fd, filename)

    def get(self, section, option, default = None, allowed = None, **kwargs):
        value = default
        if self.has_option(section, option):
            value = super().get(section, option, **kwargs)
            if allowed is not None and value not in allowed:
                raise ConfigFileError('invalid value <%s> for %s:%s (allowed: %s)' % (
                                      value, section, option, ', '.join(map(str, allowed))))
        return value

    def getlist(self, section, option, default = None, splitter = ',', **kwargs):
        """ convert a splitter separated option value to a list """
        if default is None:
            default = []
        value = default
        if self.has_option(section, option):
            value = super().get(section, option, **kwargs)
            # special case: split on newlines: remove any carriage returns
            if splitter == '\n':
                value = value.replace('\r', '')
            value = value.split(splitter)
            # strip result and eliminate empty values
            value = [v for v in map(lambda v: v.strip(), value) if v]
        return value

    def getbool(self, section, option, default = None, **kwargs):
        value = default
        if self.has_option(section, option):
            value = super().getboolean(section, option, **kwargs)
        return value
    getboolean = getbool

    def getint(self, section, option, default = None, **kwargs):
        value = default
        if self.has_option(section, option):
            # convert int values with automatic base selection
            value = int(super().get(section, option, **kwargs), 0)
        return value

    def getfloat(self, section, option, default = None, **kwargs):
        value = default
        if self.has_option(section, option):
            # convert float values
            value = float(super().get(section, option, **kwargs))
        return value

    def _cleanup_defaults(self, defaults):
        """ConfigParser doesn't allow non string defaults mapping values"""
        if defaults is not None:
            d = dict()
            for k, v in defaults.items():
                if isinstance(v, str):
                    d[k] = v
            defaults = d
        return defaults
