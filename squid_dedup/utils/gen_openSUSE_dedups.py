#! /usr/bin/env python3
"""
Description:
    generate openSUSE redirects suitable for squid_dedup
    fetched from %(url)s

Usage: %(appname)s [-hVvsf][-l log][-u url][-p page][-d dedup][-r repl]
       -h, --help           this message
       -V, --version        print version and exit
       -v, --verbose        verbose mode (cumulative)
       -s, --syslog         log errors to syslog
       -l, --logfile=fname  log to this file
       -f, --force          force operation (download and replacement)
       -u, --url=URL        fetch mirrors from this URL
                            [default: %(url)s]
       -p, --page=fname     save webpage with this name
                            [default: %(page)s]
       -d, --dedup=fname    generate dedup redirects with fname
                            [default: %(dedup)s]
       -r, --repl=repl      matched URLs replacement argument
                            [default: %(replace)s]

The fetched page is stored in the path, that TMPDIR, TEMP or TMP
environment variables point to, and limits access to the user itself.

The usual way to run this script is by crontab -e. Add a line similar to:
0 6 * * * /path/to/this/script/%(appname)s -vs

Remember to create the file %(dedup)s beforehand,
writable for the user running the crontab, with decent permissions, e.g.:
$ touch %(dedup)s
$ chown user:group %(dedup)s
$ chmod 644 %(dedup)s
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
    page = 'openSUSE-mirrors.html'
    dedup = '/etc/squid/dedup/opensuse.conf'
    replace = 'http://download.opensuse.org.%(intdomain)s/\\1'
    # internal
    url_timestamp = None

# exit codes
NO_ERR, OPTION_ERR, FETCH_ERR, PARSE_ERR, WRITE_ERR = range(5)

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
    logconfig = dict(
        level = loglevel,
        format = '%(asctime)s %(levelname)5s: [%(name)s] %(message)s',
        datefmt = '%Y-%m-%d %H:%M:%S',
    )
    if logfile is not None:
        logconfig['filename'] = logfile
    logging.basicConfig(**logconfig)
    if syslog_errors:
        syslog = logging.handlers.SysLogHandler(address = '/dev/log')
        syslog.setLevel(logging.ERROR)
        formatter = logging.Formatter('%(name)s[%(process)d]: %(levelname)s: %(message)s')
        syslog.setFormatter(formatter)
        logging.getLogger().addHandler(syslog)


def fetch(url, pagefile, force):
    """ fetch page from url as pagefile, if newer
        adjust permissions and mtime of pagefile
        return data, if successful or None
    """
    log.info('fetch %s', url)

    mtime = None
    if os.path.exists(pagefile):
        mtime = os.stat(pagefile).st_mtime

    try:
        response = urllib.request.urlopen(url)
    except urllib.error.URLError as e:
        log.error('open (%s failed: %s', url, e)
        return FETCH_ERR, None
    else:
        log.debug('http header\n%s', response.info())
        # last modification as unix timestamp
        lm = email.utils.parsedate_tz(response.info()['Last-Modified'])
        ts = email.utils.mktime_tz(lm)

        if force or mtime is None or ts > mtime:
            log.debug('read %s', url)
            try:
                data = response.read()
            except Exception as e:
                log.error('read %s failed: %s', url, e)
            else:
                log.debug('write %s', pagefile)
                try:
                    open(pagefile, 'wb').write(data)
                except IOError as e:
                    log.error('write %s failed: %s', pagefile, e)
                else:
                    atime = os.stat(pagefile).st_atime
                    os.utime(pagefile, times = (atime, ts))
                    os.chmod(pagefile, 0o600)
                    return NO_ERR, data

        elif mtime is not None and ts <= mtime:
            log.info('<%s> unchanged', pagefile)
            #return NO_ERR, open(pagefile, 'r').read()
            return NO_ERR, None


def extract(pagedata, pagefile):
    ret = []
    try:
        root = etree.HTML(pagedata)
    except etree.LxmlError as e:
        log.error('<%s> malformed: %s', pagefile, e)
        return ret

    table = root.find('.//table[@summary]')
    if table is None:
        log.error('<%s> malformed: summary table not found', pagefile)
        return ret

    country = None
    for e in table.iter('a', 'td'):
        if e.tag == 'td':
            cc = None
            for se in e:
                if se.tag == 'img':
                    cc = se.get('alt')
                    break
            if cc:
                country = '%s (%s)' % (e.xpath('string()').strip(), cc)
        elif e.tag == 'a':
            if e.text == 'HTTP':
                url = e.get('href')
                if not url.endswith('/'):
                    url += '/'
                ret.append((url, country))
    return ret


def generate(pagedata, pagefile, dedupfile, vars):
    log.info('generate %s', dedupfile)
    urls = extract(pagedata, pagefile)
    if not urls:
        return PARSE_ERR
    data = ['''\
#
# this file was generated by %(appname)s
# from %(url)s
# with timestamp %(url_timestamp)s
#
[openSUSE]
match:
    # openSUSE Headquarter
    http\:\/\/[a-z0-9]+\.opensuse\.org\/(.*)''' % vars]
    country = None
    for url, cc in urls:
        if cc != country:
            data.append('    # %s' % cc)
            country = cc
        data.append('    %s(.*)' % re.escape(url))
    data.append('''\
replace: %(replace)s
# fetch all redirected objects explicitly
fetch: true

''' % vars)
    # open, write and close the dedup config file in one go
    try:
        open(dedupfile, 'w').write('\n'.join(data))
    except Exception as e:
        log.error(e)
        return WRITE_ERR
    return NO_ERR


def gen_openSUSE_dedups():
    ret = NO_ERR
    if gpar.page:
        fname = gpar.page
    else:
        path = urllib.parse.urlparse(gpar.url).path
        fname = posixpath.basename(path)
    pagefile = os.path.join(tempfile.gettempdir(), fname)
    ret, pagedata = fetch(gpar.url, pagefile, gpar.force)
    if pagedata:
        mtime = os.stat(pagefile).st_mtime
        gpar.url_timestamp = email.utils.formatdate(mtime, localtime = True)
        ret = generate(pagedata, pagefile, gpar.dedup, gpar.__dict__)
    return ret


if __name__ == '__main__':
    try:
        optlist, args = getopt.getopt(sys.argv[1:], 'hVvsfl:u:p:d:r:',
            ('help', 'version', 'verbose', 'syslog', 'logfile',
             'force', 'url=', 'page=', 'dedup=', 'repl=')
        )
    except getopt.error as msg:
        exit(OPTION_ERR, msg, True)

    for opt, par in optlist:
        if opt in ('-h', '--help'):
            exit(usage = True)
        elif opt in ('-V', '--version'):
            exit(msg = 'version %s' % gpar.version)
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
        elif opt in ('-p', '--page'):
            gpar.page = par
        elif opt in ('-d', '--dedup'):
            gpar.dedup = par
        elif opt in ('-r', '--repl'):
            gpar.replace = par

    if not os.path.exists(gpar.dedup):
        gpar.force = True

    setup_logging(gpar.loglevel, gpar.logfile, gpar.syslog)

    sys.exit(gen_openSUSE_dedups())
