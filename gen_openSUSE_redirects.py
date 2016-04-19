#! /usr/bin/env python3
"""
Description:
    generate openSUSE redirects suitable for squid redirector jesred
    from the webpage at http://mirrors.opensuse.org/list/all.html

Usage: %(appname)s [-hVvsf][-l log][-u url][-d dest][-r repl]
       -h, --help           this message
       -V, --version        print version and exit
       -v, --verbose        verbose mode (cumulative)
       -s, --syslog         log errors to syslog
       -l, --logfile=fname  log to this file
       -f, --force          force operation (download and replacement)
       -u, --url=URL        fetch mirrors from this page
                            [default: %(url)s]
       -d, --dest=fname     generate jesred redirects with fname
                            [default: %(dest)s]
       -r, --repl=regexp    replacement clause
                            [default: %(repl)s]

The fetched page is stored in the path, that TMPDIR, TEMP or TMP
environment variables point to, and limits access to the user itself.

Copyright:
(c)2016 by %(author)s

License:
%(license)s
"""
#
# Changelog:
# 2016-04-18    hp  0.1  initial version
#
# vim:set et ts=8 sw=4:
#
# TODO:
#       error handling
#       logging

__version__ = '0.1'
__author__ = 'Hans-Peter Jansen <hpj@urpla.net>'
__license__ = 'GNU GPL 2 - see http://www.gnu.org/licenses/gpl2.txt for details'


import os
import sys
import getopt
import logging
import logging.handlers
import tempfile
import posixpath
import email.utils
import urllib.parse
import urllib.error
import urllib.request

from lxml import etree


class gpar:
    """ global parameter class """
    appdir, appname = os.path.split(sys.argv[0])
    if appdir == '.':
        appdir = os.getcwd()
    version = __version__
    author = __author__
    license = __license__
    loglevel = logging.WARNING
    syslog = False
    logfile = None
    force = False
    url = 'http://mirrors.opensuse.org/list/all.html'
    dest = 'opensuse-redirect.rules'
    repl = 'http://download.opensuse.org/\\1'


log = logging.getLogger(gpar.appname)

stderr = lambda *s: print(*s, file = sys.stderr, flush = True)

def exit(ret = 0, msg = None, usage = False):
    """ terminate process with optional message and usage """
    if msg:
        stderr('%s: %s' % (gpar.appname, msg))
    if usage:
        stderr(__doc__ % gpar.__dict__)
    sys.exit(ret)


def setup_logging(loglevel, logfile, syslog_errors):
    """ setup various aspects of logging facility """
    logcfg = dict(
        level = loglevel,
        format = '%(asctime)s %(levelname)5s: [%(name)s] %(message)s',
        datefmt = '%Y-%m-%d %H:%M:%S',
    )
    if logfile is not None:
        logcfg['filename'] = logfile
    logging.basicConfig(**logcfg)
    if syslog_errors:
        syslog = logging.handlers.SysLogHandler(address = '/dev/log')
        syslog.setLevel(logging.ERROR)
        formatter = logging.Formatter('%(name)s[%(process)d]: %(levelname)s: %(message)s')
        syslog.setFormatter(formatter)
        logging.getLogger().addHandler(syslog)


def fetch(url, fname, force):
    """ fetch page from url, if newer
        returns data, if successful or None
    """
    log.info('fetch(url: "%s", fname: "%s")', url, mtime, fname)

    # timestamp of local page
    mtime = None
    if os.path.exists(fname):
        mtime = os.stat(fname).st_mtime



    try:
        response = urllib.request.urlopen(url)
    except urllib.error.URLError as e:
        log.error('open("%s") failed: %s', url, e)
    else:
        lm = email.utils.parsedate_tz(response.info()['Last-Modified'])
        ts = email.utils.mktime_tz(lm)

        if mtime is not None and ts <= mtime:
            log.info('file "%s" is unchanged', fname)
            return open(fname, 'r').read()

        if mtime is None or ts > mtime or force:
            log.info('read("%s", ts: %s)',url, ts)
            try:
                data = response.read()
            except Exception as e:
                log.error('read("%s") failed: %s', url, e)
            else:
                log.info('write("%s")', fname)
                try:
                    open(fname, 'wb').write(data)
                except IOError as e:
                    log.error('write("%s") failed: %s', fname, e)
                else:
                    atime = os.stat(fname).st_atime
                    os.utime(fname, times = (atime, ts))
                    return data


def generate(url, page, fname, mtime, destname, repl):
    log.info('generate("%s" from "%s")', destname, fname)
    try:
        root = etree.HTML(page)
    except etree.LxmlError as e:
        log.error('%s malformed: %s', fname, e)

    table = root.find('.//table[@summary]')
    if table is None:
        log.error('%s malformed: summary table not found', fname)
        return 1

    try:
        fd = open(destname, 'w')
    except Exception as e:
        log.error('%s: %s', destname, e)
    else:
        fd.write('''#
# this file was automatically generated based on
# %s from %s
#
#abort   .html
#abort   .jpg
#abort   .png
#abort   .jpeg
#abort   .gif
#abort   .html
#abort   .shtml
#abort   .java
#abort   .jar
#abort   .htm

''' % (url, email.utils.formatdate(mtime, localtime = True)))
        country = None
        for e in table.iter('a', 'td'):
            if e.tag == 'td':
                cc = None
                for se in e:
                    if se.tag == 'img':
                        cc = se.get('alt')
                        break
                if cc:
                    c = '# %s (%s)\n' % (e.xpath('string()').strip(), cc)
                    if c != country:
                        country = c
                        fd.write(c)
            elif e.tag == 'a':
                if e.text == 'HTTP':
                    url = e.get('href')
                    if not url.endswith('/'):
                        url += '/'
                    fd.write('regexi ^%s(.*)$ %s\n' % (url, repl))
        fd.write('\n')
        fd.close()
    return 0


def main():
    # get filename from URL
    url = gpar.url
    path = urllib.parse.urlparse(url).path
    fname = os.path.join(tempfile.gettempdir(), posixpath.basename(path))

    ret = 0
    page = fetch(url, mtime, fname, gpar.force)
    if page:
        mtime = os.stat(fname).st_mtime
        ret = generate(url, page, fname, mtime, gpar.dest, gpar.repl)
    return ret

if __name__ == '__main__':
    try:
        optlist, args = getopt.getopt(sys.argv[1:], 'hVvsfl:u:d:r:',
            ('help', 'version', 'verbose', 'syslog', 'logfile',
             'force', 'url=', 'dest=', 'repl=')
        )
    except getopt.error as msg:
        exit(1, msg, True)

    for opt, par in optlist:
        if opt in ('-h', '--help'):
            exit(usage = True)
        elif opt in ('-V', '--version'):
            exit(msg = 'version: %s' % gpar.version)
        elif opt in ('-v', '--verbose'):
            if gpar.loglevel > logging.DEBUG:
                gpar.loglevel -= 10
        elif opt in ('-s', '--syslog'):
            gpar.syslog = True
        elif opt in ('-l', '--logfile'):
            gpar.logfile = par
        elif opt in ('-f', '--force'):
            gpar.force = True
        elif opt in ('-u', '--url'):
            gpar.url = par
        elif opt in ('-d', '--dest'):
            gpar.dest = par
        elif opt in ('-r', '--repl'):
            gpar.repl = par

    setup_logging(gpar.loglevel, gpar.logfile, gpar.syslog)
    logcfg = dict(
        level = gpar.loglevel,
        format = '%(asctime)s %(levelname)5s: [%(name)s] %(message)s',
        datefmt = '%Y-%m-%d %H:%M:%S',
    )
    if gpar.logfile is not None:
        logcfg['filename'] = gpar.logfile
    logging.basicConfig(**logcfg)
    if gpar.syslog:
        syslog = logging.handlers.SysLogHandler(address='/dev/log')
        syslog.setLevel(logging.ERROR)
        formatter = logging.Formatter('%(name)s[%(process)d]: %(levelname)s: %(message)s')
        syslog.setFormatter(formatter)
        logging.getLogger().addHandler(syslog)

    sys.exit(main())
