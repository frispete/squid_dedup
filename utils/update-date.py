#! /usr/bin/env python3
"""
Synopsis:
    update date in source file from last change in git tree

Usage: %(appname)s [-hVvs][-l logfile][-d datevar] sourcefile..
       -h, --help           this message
       -V, --version        print version and exit
       -v, --verbose        verbose mode (cumulative)
       -l, --logfile=fname  log to this file
       -s, --simulate       don't apply changes
       -d, --datevar=var    search for var = in source file
                            [default: %(datevar)s]

Description:
Search the given source files for a pattern like:
%(datevar)s = 'datestr'
where datestr consists of digits, - and . characters, and replaces it
with the date of the latest git commit (HEAD).

It will not change the file, if that line is unchanged.
"""
#
# vim:set et ts=8 sw=4:
#

__version__ = '0.1'
__author__ = 'Hans-Peter Jansen <hpj@urpla.net>'
__license__ = 'GNU GPL 2 - see http://www.gnu.org/licenses/gpl2.txt for details'


import os
import re
import sys
import getopt
import logging
import logging.handlers
import subprocess

class gpar:
    """ global parameter class """
    appdir, appname = os.path.split(sys.argv[0])
    if appdir == '.':
        appdir = os.getcwd()
    if appname.endswith('.py'):
        appname = appname[:-3]
    version = __version__
    author = __author__
    license = __license__
    loglevel = logging.INFO
    logfile = None
    simulate = False
    datevar = '__verdate__'
    # internal
    date_assign_re = '(%s = [\'"])[0-9-\.]+([\'"])'
    date_repl_re = '\\g<1>%s\\g<2>'
    git_last_change = ['git', 'show', '-s', '--format=%ci', 'HEAD']


log = logging.getLogger(gpar.appname)

stderr = lambda *s: print(*s, file = sys.stderr, flush = True)

def exit(ret = 0, msg = None, usage = False):
    """ terminate process with optional message and usage """
    if msg:
        stderr('%s: %s' % (gpar.appname, msg))
    if usage:
        stderr(__doc__ % gpar.__dict__)
    sys.exit(ret)


def setup_logging(logfile, loglevel):
    """ setup various aspects of logging facility """
    logconfig = dict(
        level = loglevel,
        format = '%(asctime)s %(levelname)5s: [%(name)s] %(message)s',
        datefmt = '%Y-%m-%d %H:%M:%S',
    )
    if logfile not in (None, '-'):
        logconfig['filename'] = logfile
    logging.basicConfig(**logconfig)


def git_changelog_date():
    try:
        datestr = subprocess.check_output(gpar.git_last_change)
    except subprocess.CalledProcessError:
        return None
    else:
        date = datestr.split()[0].decode('ascii')
        log.debug('git_changelog_date: %s', date)
        return date


def search_and_replace_date(lines, newdate):
    pattern = gpar.date_assign_re % gpar.datevar
    repl = gpar.date_repl_re % newdate
    log.debug('search_and_replace_date: pattern: %s', pattern)
    log.debug('search_and_replace_date: replace: %s', repl)
    for ln, line in enumerate(lines):
        newline, n = re.subn(pattern, repl, line)
        if n:
            if line != newline:
                # pattern matched and line changed
                log.debug('found pattern: %s', line[:-1])
                log.debug('  replacement: %s', newline[:-1])
                lines[ln] = newline
                return True
            else:
                # pattern matched, but not changed
                return False
    return False


def main(args):
    ret = 0
    if not args:
        exit(2, 'no source file specified')
    for arg in args:
        if os.path.exists(arg):
            newdate = git_changelog_date()
            if newdate:
                srclines = open(arg).readlines()
                if search_and_replace_date(srclines, newdate):
                    msg = 'update %s in %s to %s' % (gpar.datevar, arg, newdate)
                    if gpar.simulate:
                        msg = 'would %s' % msg
                    else:
                        open(arg, 'w').writelines(srclines)
                    #log.info(msg)
                    stderr(msg)
            else:
                log.error('no valid changelog date')
        else:
            log.error('source file <%s> not found', arg)
    return ret


if __name__ == '__main__':
    try:
        optlist, args = getopt.getopt(sys.argv[1:], 'hVvl:sd:',
            ('help', 'version', 'verbose', 'logfile=', 'simulate', 'datevar=', )
        )
    except getopt.error as msg:
        exit(1, msg, True)

    for opt, par in optlist:
        if opt in ('-h', '--help'):
            exit(usage = True)
        elif opt in ('-V', '--version'):
            exit(msg = 'version %s' % gpar.version)
        elif opt in ('-v', '--verbose'):
            if gpar.loglevel > logging.DEBUG:
                gpar.loglevel -= 10
        elif opt in ('-l', '--logfile'):
            gpar.logfile = par
        elif opt in ('-s', '--simulate'):
            gpar.simulate = True
        elif opt in ('-d', '--datevar'):
            gpar.datevar = par

    setup_logging(gpar.logfile, gpar.loglevel)

    sys.exit(main(args))
