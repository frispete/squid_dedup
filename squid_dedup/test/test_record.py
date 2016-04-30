# -*- coding: utf-8 -*-

# Author: Hans-Peter Jansen <hpj@urpla.net>
# License: GNU GPL 2 - see http://www.gnu.org/licenses/gpl2.txt for details
# vim:set et ts=8 sw=4:

import os
import sys

from unittest import TestCase

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from lib import record

class TestRecord(TestCase):

    def test(self):
        attribs = dict(one = 1, two = '2', three = (1, 2, 3.3), four = 123.456, five = 'bla', six = 'Hää?')
        rec = record.recordfactory('Rec', **attribs)
        self.assertEqual(rec.one, 1)
        self.assertEqual(rec.two, '2')
        self.assertEqual(rec.three, (1, 2, 3.3))
        self.assertEqual(rec.four, 123.456)
        self.assertEqual(rec.five, 'bla')
        self.assertEqual(rec.six, 'Hää?')

        self.assertEqual(str(rec), '''\
Rec(
 five: 'bla'
 four: 123.456
  one: 1
  six: 'Hää?'
three: (1, 2, 3.3)
  two: '2'
)''')

        self.assertEqual(rec.asdict(), attribs)
