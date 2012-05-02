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
        username = os.environ['mmdb.username']
        password = os.environ['mmdb.password']
        self.mmdb = MMDB(username,password)
        
    def test_create_instance(self):
        self.assertNotEquals(self.mmdb,None)
    
    def test_getRemoteMovieLibrary(self):
        library = self.mmdb.getRemoteMovieLibrary()
        self.assertNotEquals(library,None,"Library should not be None")
        self.assertTrue(library.__len__() > 0)
        libraryKeys = library[0].keys()
        for requiredKey in ['tags','media','type','lastUpdated']:
            self.assertTrue(requiredKey in libraryKeys, '%s key was missing in library keyset ' % (requiredKey))
            
    def test_setRemoteMovieTag(self):
        json = self.mmdb.addRemoteMediaTag('1', 'acquired')
        self.assertIn('acquired',json)
        #cleanup
        json = self.mmdb.removeRemoteMediaTag('1', 'acquired')
        self.assertNotIn('acquired',json)

    def test_searchForImdbId(self):
        json = self.mmdb.search('tt0499549')
        self.assertGreater(len(json),0)

    def test_getRemoteEpisodeLibrary(self):
        library = self.mmdb.getRemoteEpisodeLibrary()
        self.assertNotEquals(library,None,"Library should not be None")
        self.assertTrue(library.__len__() > 0)
        libraryKeys = library[0].keys()
        for requiredKey in ['tags','media','type','lastUpdated']:
            self.assertTrue(requiredKey in libraryKeys, '%s key was missing in library keyset ' % (requiredKey))
               
    