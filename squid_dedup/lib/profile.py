# -*- coding: utf-8 -*-

# Author: Hans-Peter Jansen <hpj@urpla.net>
# License: GNU GPL 2 - see http://www.gnu.org/licenses/gpl2.txt for details
# vim:set et ts=8 sw=4:

# profile data might processed/visualized with:
# kcachegrind: pyprof2calltree -i profile.pstats -o profile.kgrind
# or directly: pyprof2calltree -ki profile.pstats
# gprof2dot: gprof2dot -f pstats profile.pstats | dot -Tsvg -o profile.svn
# note: zypper install python-pyprof2calltree python-gprof2dot

import os
import datetime
import cProfile
from string import Template


def profile(fn = None, sorting = 'cumulative'):
    """conditional profiling decorator function
       this is testing for a self._config.profile attribute of the wrapped method,
       most useful for Process.run methods, as those cannot be profiled easily, otherwise.
       fn is a filename or None for printing stats to stdout, it will be saved to config.profiledir
       fn may contain $date and $time macros, and will have .pstats extension appended, if missing
       sorting specifies the sorting method, when fn is None
    """
    def wrapper(f):
        def wrapped_f(*args, **kwargs):
            config = args[0]._config
            if config.profile:
                pr = cProfile.Profile()
                pr.enable()
                pr.runcall(f, *args, **kwargs)
                pr.disable()
                pr.create_stats()
                if fn is None:
                    pr.print_stats(sorting)
                else:
                    # this is a bit subtile: because fn is a non mutable string,
                    # reassigning fn in this scope would lead to masking fn from
                    # the outer scope, resulting in:
                    # UnboundLocalError: local variable 'fn' referenced before assignment
                    # solution: assign to a local var
                    # see: http://stackoverflow.com/questions/8447947
                    _fn = fn
                    now = datetime.datetime.now()
                    d = dict(date = now.strftime(config.dateformat),
                             time = now.strftime(config.timeformat))
                    _fn = Template(_fn).safe_substitute(d)
                    if not _fn.endswith('.pstats'):
                        _fn += '.pstats'
                    pr.dump_stats(os.path.join(config.profiledir, _fn))
            else:
                f(*args, **kwargs)
        return wrapped_f
    return wrapper
