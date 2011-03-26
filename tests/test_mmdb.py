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
    
    def test_getRemoteLibrary(self):
        library = self.mmdb.getRemoteMovieLibrary()
        self.assertNotEquals(library,None,"Library should not be None")
        self.assertTrue(library.__len__() > 0)
        libraryKeys = library[0].keys()
        for requiredKey in ['emotion','wishlisted','experienced','mediaId','name','acquired','imdbId','tmdbId']:
            self.assertTrue(requiredKey in libraryKeys)