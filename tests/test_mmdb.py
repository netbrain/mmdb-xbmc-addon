# -*- coding: utf-8 -*-
"""
    Skeleton test suite
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

import unittest
import os


from mymediadb.mmdb import MMDB

class MMDBApiTest(unittest.TestCase):
    
    def setUp(self):        
        username = os.environ['python_test_mmdb_username']
        password = os.environ['python_test_mmdb_password']
        self.mmdb = MMDB(username,password)
        
    def test_create_instance(self):
        self.assertNotEquals(self.mmdb,None)    