#!/usr/bin/env python3

from lxml import etree

filename = 'all.html'
page = open(filename).read()
root = etree.HTML(page)
table = root.find('.//table[@summary]')
if table is not None:
    print('''#
# this file was automatically generated based on
# http://mirrors.opensuse.org/list/all.html, timestamp 2016-04-18 06:00:03.964503840 +0200
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
''')
    replacement = 'http://download.opensuse.org/\\1'
    country = None
    for e in table.iter('a', 'td'):
        #print(e, e.text, e.tail, e.text == 'HTTP')
        if e.tag == 'td':
            cc = None
            for se in e:
                if se.tag == 'img':
                    cc = se.get('alt')
                    break
            if cc:
                c = '# %s (%s)' % (e.xpath('string()').strip(), cc)
                if c != country:
                    country = c
                    print(c)
        elif e.tag == 'a':
            if e.text == 'HTTP':
                url = e.get('href')
                if not url.endswith('/'):
                    url += '/'
                print('regexi ^%s(.*)$ %s' % (url, replacement))
