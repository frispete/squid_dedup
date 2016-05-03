# -*- coding: utf-8 -*-

# Author: Hans-Peter Jansen <hpj@urpla.net>
# License: GNU GPL 2 - see http://www.gnu.org/licenses/gpl2.txt for details
# vim:set et ts=8 sw=4:

# StoreID redirector, see http://wiki.squid-cache.org/Features/StoreID

import sys
import select
import logging

log = logging.getLogger('dedup')

DEDUP_TIMEOUT = 0.3

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
        # note: side effect of caching: the url isn't put into the fetch queue
        try:
            return self._cache[url]
        except KeyError:
            for name, section in self._config.section_dict.items():
                #log.trace('parse: match: %s', section.match)
                for match, regexp in section.match:
                    repl, n = regexp.subn(section.replace, url)
                    if n:
                        #log.trace('parse: %s matched: %s', match, repl)
                        self._cache[url] = repl
                        if section.fetch:
                            self._config.fetch_queue.put(url)
                        return repl

    def process(self, url, channel = None):
        args = []
        if channel is not None:
            args.append(channel)
        newurl = self.parse(url)
        if newurl:
            # rewrite URL
            args.extend(('OK', 'store-id=' + newurl))
        else:
            # no error: just no rewrite
            args.append('ERR')
        self.stdout(*args)
        if newurl:
            if channel is None:
                log.info('URL <%s> rewritten: <%s>', url, newurl)
            else:
                log.info('URL <%s> rewritten: <%s> (ch: %s)', url, newurl, channel)
        else:
            if channel is None:
                log.debug('URL <%s> ignored', url)
            else:
                log.debug('URL <%s> ignored (ch: %s)', url, channel)

    def serial(self, line):
        try:
            url, options = line.split(maxsplit = 1)
        except ValueError:
            self.stdout('ERR')
            log.error('invalid input <%s>', line)
        else:
            self.process(url)

    def concurrent(self, line):
        try:
            channel, url, options = line.split(maxsplit = 2)
        except ValueError:
            channel = []
            for c in line:
                if c.isdigit():
                    channel.append(c)
                else:
                    break
            channel = ''.join(channel)
            self.stdout(channel, 'ERR')
            log.error('invalid input <%s>', line)
        else:
            self.process(url, channel)

    def run(self):
        log.debug('running')
        while not self._exiting:
            if sys.stdin in select.select([sys.stdin], [], [], DEDUP_TIMEOUT)[0]:
                # we're explicitly using readline here,
                # since it gives us line buffered input
                line = sys.stdin.readline()
                if line:
                    if line[-1] == '\n':
                        line = line[:-1]
                    if line and line[0].isdigit():
                        self.concurrent(line)
                    else:
                        self.serial(line)
        log.debug('finished')
