# -*- coding: utf-8 -*-
"""
    Skeleton test suite
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

import unittest
import os

from mymediadb.xbmcapp import XBMCApp

class XBMCAppTest(unittest.TestCase):
    
    def setUp(self):        
        moviedb = os.path.realpath(os.curdir+"/resources/test-database.db")
        self.xbmcApp = XBMCApp(moviedb)
        
    def test_create_instance(self):
        self.assertNotEquals(self.xbmcApp,None)
        
    def test_getLocalMovieLibrary(self):
        library = self.xbmcApp.getLocalMovieLibrary()
        self.assertNotEquals(library,None,"Library should not be None")
        self.assertTrue(library.__len__() > 0,"Size should be greater than zero")
    