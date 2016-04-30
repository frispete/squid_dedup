# -*- coding: utf-8 -*-

# Author: Hans-Peter Jansen <hpj@urpla.net>
# License: GNU GPL 2 - see http://www.gnu.org/licenses/gpl2.txt for details
# vim:set et ts=8 sw=4:

def frec(rec, withunderscores = True, indent = None):
    '''format a dict in a sorted, easy to read record presentation
    Note: only string types are allowed as keys
    eg.:
    def __repr__(self):
        return "%s(\n%s\n)" % (self.__class__.__name__, frec(self.__dict__))
    '''
    __ret = []
    if withunderscores:
        keys = [key for key in rec]
    else:
        keys = [key for key in rec if not key.startswith('_')]
    maxklen = len(keys) and max([len(key) for key in keys]) or 0
    if indent is not None:
        maxklen = max(maxklen, indent)
    for key in sorted(keys):
        __ret.append('%*s: %r' % (maxklen, key, rec[key]))
    return '\n'.join(__ret)


