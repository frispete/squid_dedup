# -*- coding: utf-8 -*-

# Author: Hans-Peter Jansen <hpj@urpla.net>
# License: GNU GPL 2 - see http://www.gnu.org/licenses/gpl2.txt for details
# vim:set et ts=8 sw=4:

from lib import frec

def recordfactory(classname, **kwargs):
    """record factory, returning a class name classname,
       and keyword args assigned as class members
    """
    class Record(object):
        """represent a Record, carrying its attributes as class members"""
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

        def asdict(self):
            """return instance values as dict"""
            d = dict()
            for k, v in self.__dict__.items():
                if not k.startswith('__'):
                    d[k] = v
            return d

        def __repr__(self):
            return '%s(\n%s\n)' % (self.__class__.__name__, frec.frec(self.asdict()))

    record = Record(**kwargs)
    record.__class__.__name__ = classname
    return record
