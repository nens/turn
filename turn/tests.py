# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

import unittest
import sys

from turn import console
from turn import tools
from turn import core


class TestTools(unittest.TestCase):
    def test_follow(self):
        pass

class TestConsole(unittest.TestCase):
    def test_console(self):
        argv = sys.argv
        connection = ['--host', 'localhost', '--port', '6379', '--db', '0']
        sys.argv = [''] + connection + ['test']
        status = console.main()
        self.assertFalse(status)
        sys.argv = argv
