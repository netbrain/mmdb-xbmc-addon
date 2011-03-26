# -*- coding: utf-8 -*-
"""
    Skeleton test suite
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

import unittest
import os


from mymediadb.mmdb import MMDB
from urllib2 import HTTPError
import urllib2

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
            self.assertTrue(requiredKey in libraryKeys, '%s key was missing in library keyset ' % (requiredKey))
            
    def test_setRemoteMovieTag(self):
        postdata = {'acquired':True}
        self.mmdb.setRemoteMovieTag('tt1301990', postdata)
        movie = self.mmdb._getRemoteMovieTags(32754)
        self.assertEqual(movie['acquired'], True, 'Movie was not acquired')
        #cleanup
        postdata = {'acquired':False}
        self.mmdb.setRemoteMovieTag('tt1301990', postdata)
        movie = self.mmdb._getRemoteMovieTags(32754)
        self.assertEqual(movie['acquired'], False, 'Movie was acquired')
        
    def test_SetRemoteMovieTagOnNonePostdata(self):
        try:
            self.mmdb.setRemoteMovieTag('tt1301990', None)
            self.assertTrue(False, 'Should not reach this point')
        except urllib2.URLError,e:
            self.assertEqual(e.code, 500, 'urlib2 url error')
            
        
    def test_setRemoteMovieOnWrongImdbId(self):
        postdata = {'acquired':False}
        try:
            self.mmdb.setRemoteMovieTag('tt13019sdfsdfs90', postdata)
            self.assertTrue(False, 'Should not reach this point')
        except urllib2.URLError,e:
            self.assertEqual(e.code, 404, 'urlib2 url error')
               