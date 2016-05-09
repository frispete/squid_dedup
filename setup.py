# -*- coding: utf-8 -*-

# Author: Hans-Peter Jansen <hpj@urpla.net>
# License: GNU GPL 2 - see http://www.gnu.org/licenses/gpl2.txt for details
# vim:set et ts=8 sw=4:

import os
import re
import sys

from setuptools import setup, find_packages

pkgname = 'squid_dedup'
version = None

min_python = (3, 1)
my_python = sys.version_info

if my_python < min_python:
    print('{} requires Python {}.{} or later'.format(pkgname, *min_python))
    sys.exit(1)

for line in open(os.path.join(pkgname, 'config.py')):
    m = re.search('__version__\s*=\s*(.*)', line)
    if m:
        version = m.group(1).strip()[1:-1]  # quotes
        break
assert version

with open('README.rst', 'r') as fd:
    long_description = fd.read()

setup(
    name = pkgname,
    version = version,
    description = 'A squid 3 proxy helper for deduplicating CDN accesses',
    long_description = long_description,
    author = 'Hans-Peter Jansen',
    author_email = 'hpj@urpla.net',
    url = 'https://github.com/frispete/squid_dedup',
    license = 'GPLv2',
    packages = find_packages(),
    entry_points = {
        'console_scripts': [
            'squid_dedup = squid_dedup.main:main',
            'gen_openSUSE_dedups = squid_dedup.utils.gen_openSUSE_dedups:main',
        ],
    },
    include_package_data = True,
    install_requires = [],
    tests_require = [],
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
    ],
)
