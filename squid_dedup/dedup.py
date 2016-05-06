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
        self._protocol = config.protocol

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
                for match, regexp in section.match:
                    newurl, n = regexp.subn(section.replace, url)
                    if n:
                        #log.trace('parse matched: %s: replacement: %s', match, newurl)
                        self._cache[url] = (section, newurl)
                        return (section, newurl), False

    def process(self, channel, url, options):
        #log.trace('process: channel %s, url: %s, options: %s', channel, url, options)
        args = []
        if channel is not None:
            args.append(channel)
        try:
            (section, newurl), cached = self.parse(url)
        except TypeError:
            newurl = None
        if newurl:
            # rewrite URL
            args.extend(('OK', 'store-id=' + newurl))
        else:
            # no error: just no rewrite
            args.append('ERR')
        # get the reply out of the door as quickly as possible
        self.stdout(*args)
        log.trace('out: %s', ' '.join(args))
        # optional processing and logging
        if log.isEnabledFor(logging.INFO):
            msg = []
            if channel is not None:
                msg.append('channel ' + channel)
            if newurl is not None:
                msg.append('URL <%s> replaced with <%s>' % (url, newurl))
                _log = log.info
            else:
                msg.append('URL <%s> unchanged' % url)
                _log = log.debug
            if options:
                msg.append('options <' + ' '.join(options) + '>')
            _log(', '.join(msg))
        # delay feeding the fetcher up to this point
        if newurl is not None and not cached and section.fetch:
            self._config.fetch_queue.put((newurl, url), block = False)
        return args

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
                    #log.trace('in: %s', options)
                    try:
                        # pull out a decimal channel-ID, if available
                        if options[0].isdigit():
                            channel = options.pop(0)
                        # an URL must be available for a valid request
                        url = options.pop(0)
                    except IndexError:
                        args = ['ERR']
                        if channel is not None:
                            args.insert(0, channel)
                            log.error('channel %s, invalid input <%s>', channel, line)
                        else:
                            log.error('invalid input <%s>', line)
                        self.stdout(*args)
                    else:
                        # process tokens
                        args = self.process(channel, url, options)
                    if self._protocol:
                        try:
                            open(self._protocol, 'a').write(line + '\n' + ' '.join(args) + '\n')
                        except IOError as e:
                            log.error('protocol logging error: %s', e)
        log.debug('finished')
