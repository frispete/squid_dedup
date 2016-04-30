# -*- coding: utf-8 -*-

# Author: Hans-Peter Jansen <hpj@urpla.net>
# License: GNU GPL 2 - see http://www.gnu.org/licenses/gpl2.txt for details
# vim:set et ts=8 sw=4:

import os
import sys

from unittest import TestCase

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from lib import frec

class Testfrec(TestCase):

    def test_simple_rec(self):
        rec = dict(label1 = 'eins', label2 = 'zwo', label3 = 'trois')
        rval = frec.frec(rec)
        self.assertEqual(rval, '''\
label1: 'eins'
label2: 'zwo'
label3: 'trois\'''')

        rec = {'1': 'eins', 'zwei': 2, '_3': 'trois'}
        rval = frec.frec(rec)
        self.assertEqual(rval, '''\
   1: 'eins'
  _3: 'trois'
zwei: 2''')

    def test_simple_rec_without_underscores(self):
        rec = {'1': 'eins', 'zwei': 2, '_3': 'trois'}
        rval = frec.frec(rec, withunderscores = False)
        self.assertEqual(rval, '''\
   1: 'eins'
zwei: 2''')

    def test_different_types(self):
        rec = dict(one = 1, two = '2', three = (1, 2, 3.3), four = 123.456, five = 'bla', six = 'Hää?')
        rval = frec.frec(rec)
        self.assertEqual(rval, '''\
 five: 'bla'
 four: 123.456
  one: 1
  six: 'Hää?'
three: (1, 2, 3.3)
  two: '2\'''')
