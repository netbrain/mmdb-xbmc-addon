# -*- coding: utf-8 -*-
"""
    Skeleton test suite
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

import unittest
import os

from mymediadb.xbmcapp import XBMCApp

try:
    from sqlite3 import dbapi2 as sqlite
    print "Loading sqlite3 as DB engine"
except:
    from pysqlite2 import dbapi2 as sqlite
    print "Loading pysqlite2 as DB engine"


class XBMCAppTest(unittest.TestCase):
    
    def setUp(self):        
        moviedb = os.path.dirname(os.path.abspath(__file__))+"/resources/test-database.db"
        self.xbmcApp = XBMCApp(moviedb)
        
    def test_create_instance(self):
        self.assertNotEquals(self.xbmcApp,None)
        
    def test_getLocalMovieLibrary(self):
        library = self.xbmcApp.getLocalMovieLibrary()
        self.assertNotEquals(library,None,"Library should not be None")
        self.assertTrue(library.__len__() > 0,"Size should be greater than zero")
    
    def test_getLocalMovie(self):
        movie = self.xbmcApp.getLocalMovie('tt0970452')
        self.assertNotEquals(movie, None, 'Did not find movie as expected')
        self.assertEqual(movie['name'], 'Solomon Kane', 'Found wrong movie')
    
    def test_getLocalMovieWhereIdNotExists(self):
        movie = self.xbmcApp.getLocalMovie('tt4253668')
        self.assertEqual(movie, None, 'Found movie when not supposed to,')
        
    def test_getLocalMovieWhereIdIsNone(self):
        self.assertRaises(RuntimeError, self.xbmcApp.getLocalMovie,None)
    
    def __setLocalMovieAsNotWatched(self,idFile):
        connection = sqlite.connect(self.xbmcApp.moviedb)
        cursor = connection.cursor()
        cursor.execute("update files SET playCount=0 where idFile=?",(idFile,))    
        connection.commit()
        connection.close()
         
    def test_setLocalMovieAsWatched(self):        
        movie = self.xbmcApp.getLocalMovie('tt0892769')
        self.assertEqual(movie['watched'], 0, 'Movie was set as watched Before test start')
        self.xbmcApp.setLocalFileAsWatched(movie['idFile'])
        movie = self.xbmcApp.getLocalMovie(movie['imdbId'])
        self.assertEqual(movie['watched'], 1, 'Movie was not set as watched')
        #Cleanup after test
        self.__setLocalMovieAsNotWatched(movie['idFile'])
        
    def test_setLocalMovieAsWatchedWhereNonExists(self):
           self.assertRaises(RuntimeError,self.xbmcApp.setLocalFileAsWatched,5) #5 doesnt exists
    
    def test_setLocalMovieAsWatchedWhereNone(self):
           self.assertRaises(RuntimeError,self.xbmcApp.setLocalFileAsWatched,None)
        
        