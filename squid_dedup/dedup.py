# -*- coding: utf-8 -*-

# Author: Hans-Peter Jansen <hpj@urpla.net>
# License: GNU GPL 2 - see http://www.gnu.org/licenses/gpl2.txt for details
# vim:set et ts=8 sw=4:

# StoreID redirector, see http://wiki.squid-cache.org/Features/StoreID

import sys
import select
import logging

log = logging.getLogger('dedup')

DEDUP_TIMEOUT = 0.5

class Dedup:
    """ deduplicate squid proxy urls """
    def __init__(self, config):
        self._config = config
        self._exiting = False
        self._cache = {}

    def exit(self):
        self._exiting = True

    def stdout(self, *args):
        print(*args, sep = ' ', flush = True)

    def parse(self, url):
        #log.trace('parse: <%s>', url)
        try:
            return self._cache[url], True
        except KeyError:
            for name, section in self._config.section_dict.items():
                #log.trace('parse: match: %s', section.match)
                for match, regexp in section.match:
                    repurl, n = regexp.subn(section.replace, url)
                    if n:
                        #log.trace('parse: %s matched: %s', match, repl)
                        self._cache[url] = (section, repurl)
                        return (section, repurl), False

    def process(self, channel, url, options):
        args = []
        if channel is not None:
            args.append(channel)
        try:
            (section, repurl), cached = self.parse(url)
        except TypeError:
            repurl = None
        if repurl:
            # rewrite URL
            args.extend(('OK', 'store-id=' + repurl))
        else:
            # no error: just no rewrite
            args.append('ERR')
        # get the reply out of the door as quickly as possible
        self.stdout(*args)
        # optional processing and logging
        msg = []
        if channel is not None:
            msg.append('channel ' + channel)
        if repurl:
            msg.append('URL <%s> replaced with <%s>' % (url, repurl))
            _log = log.info
            # delay feeding the fetcher up to this point
            if not cached and section.fetch:
                self._config.fetch_queue.put(url)
        else:
            msg.append('URL <%s> ignored' % url)
            _log = log.debug
        if options:
            msg.append('options <' + ' '.join(options)) + '>'
        _log(', '.join(msg))

    def run(self):
        log.debug('running')
        while not self._exiting:
            if sys.stdin in select.select([sys.stdin], [], [], DEDUP_TIMEOUT)[0]:
                # we're explicitly using readline here, because
                # that gives us the desired line buffered input
                line = sys.stdin.readline()
                if line:
                    if line[-1] == '\n':
                        line = line[:-1]
                    url = None
                    channel = None
                    options = line.split()
                    #log.trace('input: %s', options)
                    try:
                        if options[0].isdigit():
                            channel = options.pop(0)
                        url = options.pop(0)
                    except IndexError:
                        if channel is not None:
                            self.stdout(channel, 'ERR')
                            log.error('invalid input <%s>', line)
                        else:
                            self.stdout('ERR')
                            log.error('invalid input <%s>', line)
                    else:
                        self.process(channel, url, options)
        log.debug('finished')
