# -*- coding: utf-8 -*-
"""
    Skeleton test suite
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

import unittest

from mymediadb.mmdb import *

class UtilTest(unittest.TestCase):

    def test_create_instance(self):
        mmdb = MMDB('username','password')
        self.assertNotEquals(mmdb,None)
                
    