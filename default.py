"""
MyMediaDB XBMC Addon
Licensed under GPL3
"""

# Import statements
import sys
import os
import time
import xbmc
import xbmcaddon
import urllib2
import base64
import re
import thread
import simplejson as json
from mymediadb.mmdb import *

try:
    from sqlite3 import dbapi2 as sqlite
    print "Loading sqlite3 as DB engine"
except:
    from pysqlite2 import dbapi2 as sqlite
    print "Loading pysqlite2 as DB engine"

# Functions
def debug(txt):
    if(addon.getSetting('debug') == 'true'):
        try:
            print txt
        except:
            print "Unexpected error:", sys.exc_info()[0]
        
def sleeper(millis):
    while (not xbmc.abortRequested and millis > 0):
        xbmc.sleep(1000)
        millis -= 1000
       

def getLocalMovieLibrary():
    result = []
    connection = sqlite.connect(moviedb)
    cursor = connection.cursor()
    cursor.execute( "select distinct movie.idMovie,movie.idFile,movie.c09 as imdbId,movie.c00 as name, case when files.playCount > 0 then 1 else 0 end as watched from movie left join files on (movie.idFile = files.idFile)")    
    for row in cursor:
        result.append(createProperRowFromCursor(cursor,row))
    connection.close()
    return result

def getLocalMovie(imdbId):
    result = None
    connection = sqlite.connect(moviedb)
    cursor = connection.cursor()
    cursor.execute( "select movie.idMovie,movie.idFile,movie.c09 as imdbId,movie.c00 as name, case when files.playCount > 0 then 1 else 0 end as watched from movie left join files on (movie.idFile = files.idFile) where imdbId=?",(imdbId,))    
    result = createProperRowFromCursor(cursor,cursor.fetchone())
    connection.close()
    return result 

def createProperRowFromCursor(cursor, row):
    if(row == None):
        return None
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def setUpdatedMovies(imdbId):
    global updatedMovies
    if imdbId == 'reset':
        del updatedMovies[:]
    else:
        updatedMovies += [imdbId]
    
def remoteMovieExists(imdbId):
    for remoteMedia in mmdb_library:
        if(remoteMedia['imdbId'] == imdbId):
            return True
    return False

def setLocalMovieAsWatched(idFile):
    if(addon.getSetting('testmode') == 'false'):
        connection = sqlite.connect(moviedb)
        cursor = connection.cursor()
        cursor.execute("update files SET playCount=1 where idFile=?",(idFile,))    
        connection.commit()
        connection.close()
    else:
        debug('MMDB Testmode cancelled API request "setLocalMovieAsWatched"')

def movieUpdatedNotifications():
    if(addon.getSetting('shownotifications') == 'true'):
        moviesUpdatedCounter=0
        moviesUpdatedCounter= updatedMovies.__len__()
        setUpdatedMovies('reset')
        if(moviesUpdatedCounter > 0):
            xbmc.executebuiltin('Notification(%s,%s,%s,%s)' % (addon.getAddonInfo('name'),"%d movies updated on MMDB" % (moviesUpdatedCounter),7000,addon.getAddonInfo("icon")))
        debug('Notifications should be showing now"')
    else:
        debug('Notifications is disabled"')

#def periodicallyGetRemoteLibrary():
#    while (not xbmc.abortRequested):
#        sleeper(3600000) #1 hour
#        debug('perodically import of remote library initiated')
#        mmdb_library = getRemoteMovieLibrary()                 

def syncWithMMDB():
    #define global access
    global mmdb_library
    global mmdb

      #sync remote media with local db
    if(mmdb_library == None):
        debug("mmdb_library = None, is api down/changed?")
        return
    anyRemoteChanges = False
    for remoteMedia in mmdb_library:
        localMedia = getLocalMovie(remoteMedia['imdbId'])
        if (localMedia != None):
            debug('Media exists both locally and remotely - ('+remoteMedia['name']+')')
            if not remoteMedia['acquired']:
                debug('Setting remote media status to acquired')
                mmdb.setRemoteMovieTag(remoteMedia['imdbId'],{'acquired':True})
                anyRemoteChanges = True
            if(remoteMedia['experienced'] != localMedia['watched']):
                debug('watched status is not synchronized')
                if(addon.getSetting('dontsyncwatched') == 'false'):
                    if(remoteMedia['experienced']):
                        debug('setting local media to watched')
                        setLocalMovieAsWatched(localMedia['idFile'])
                    else:
                        debug ('setting remote media to watched')
                        mmdb.setRemoteMovieTag(localMedia['imdbId'],{'experienced':localMedia['watched'] == 1})
                        anyRemoteChanges = True
                else:
                    debug('Cancelled synchronize of watched status due to settings!')
        else:
            debug('Media ('+remoteMedia['name']+') exists only remotely')
            if(remoteMedia['acquired'] == True):
                if(addon.getSetting('dontdeleteacquired') == 'false'):
                    debug('Acquired flag was removed from mmdb')
                    mmdb.setRemoteMovieTag(remoteMedia['imdbId'],{'acquired':False})
                    anyRemoteChanges = True
                else:
                    debug('Acquired flag was not removed from mmdb due to settings!')
            
    #sync local media with remote db
    for localMedia in getLocalMovieLibrary():
        if(remoteMovieExists(localMedia['imdbId'])):
            continue
        debug('Media exists only locally - ('+localMedia['name']+')')
        mmdb.setRemoteMovieTag(localMedia['imdbId'],{'acquired': True, 'experienced':localMedia['watched'] == 1})
        anyRemoteChanges = True
    if(anyRemoteChanges):
        debug('--- SYNCED WITH MMDB ---')
        mmdb_library = mmdb.getRemoteMovieLibrary() #sync local copy with changes on remote
        debug(mmdb_library)
    else:
        debug('--- NO CHANGES DETECTED ---')

# Constants
addon = xbmcaddon.Addon(id='script.mymediadb')
mmdb = MMDB(addon.getSetting('username'),addon.getSetting('password'))
moviedb = xbmc.translatePath('special://database/%s' % addon.getSetting('database'))

# Globals
mmdb_library = []
updatedMovies = []

# autoexecute addon on startup for older xbmc versions, remove this when xbmc.service goes live
# Auto exec info
AUTOEXEC_PATH = xbmc.translatePath( 'special://home/userdata/autoexec.py' )
AUTOEXEC_FOLDER_PATH = xbmc.translatePath( 'special://home/userdata/' )
AUTOEXEC_SCRIPT = '\nimport time;time.sleep(5);xbmc.executebuiltin("XBMC.RunScript(special://home/addons/%s/default.py)")\n' % addon.getAddonInfo('id')
# See if the autoexec.py file exists
if (os.path.exists(AUTOEXEC_PATH)):
    debug('Found autoexec')
    
    # Var to check if we're in autoexec.py
    found = False
    autostart = addon.getSetting('autostart') == 'true'
    autoexecfile = file(AUTOEXEC_PATH, 'r')
    filecontents = autoexecfile.readlines()
    autoexecfile.close()
    
    # Check if we're in it
    for line in filecontents:
        if line.find(addon.getAddonInfo('id')) > 0:
            debug('Found ourselves in autoexec')
            found = True
    
    # If the autoexec.py file is found and we're not in it,
    if (not found and autostart):
        debug('Adding ourselves to autoexec.py')
        autoexecfile = file(AUTOEXEC_PATH, 'w')
        filecontents.append(AUTOEXEC_SCRIPT)
        autoexecfile.writelines(filecontents)            
        autoexecfile.close()
    
    # Found that we're in it and it's time to remove ourselves
    if (found and not autostart):
        debug('Removing ourselves from autoexec.py')
        autoexecfile = file(AUTOEXEC_PATH, 'w')
        for line in filecontents:
            if not line.find(addon.getAddonInfo('id')) > 0:
                autoexecfile.write(line)
        autoexecfile.close()

else:
    debug('autoexec.py doesnt exist')
    if (os.path.exists(AUTOEXEC_FOLDER_PATH)):
        debug('Creating autoexec.py with our autostart script')
        autoexecfile = file(AUTOEXEC_PATH, 'w')
        autoexecfile.write (AUTOEXEC_SCRIPT.strip())
        autoexecfile.close()
    else:
        debug('Scripts folder missing, creating autoexec.py in that new folder with our script')
        os.makedirs(AUTOEXEC_FOLDER_PATH)
        autoexecfile = file(AUTOEXEC_PATH, 'w')
        autoexecfile.write (AUTOEXEC_SCRIPT.strip())
        autoexecfile.close()

# Print addon information
print "[ADDON] '%s: version %s' initialized!" % (addon.getAddonInfo('name'), addon.getAddonInfo('version'))
if(addon.getSetting('shownotifications') == 'true'):
    xbmc.executebuiltin('Notification(%s,%s,%s,%s)' % (addon.getAddonInfo('name'),'is running!',3000,addon.getAddonInfo("icon")))

# Print debug info
if(addon.getSetting('debug') == 'true'):
    print '---- '+addon.getAddonInfo('name')+'- DEBUG ----'
    print 'username=%s' % addon.getSetting('username')
    print 'moviedb=%s' % moviedb
    print '---- '+addon.getAddonInfo('name')+'- DEBUG ----'

# Testmode
if(addon.getSetting('testmode') == 'true'):
    debug('Testmode activated')

# DontdeleteAqcuired
if(addon.getSetting('dontdeleteacquired') == 'true'):
    debug('Dont delete aqcuired activated')

# Dontsyncwatched
if(addon.getSetting('dontsyncwatched') == 'true'):
    debug('Synching of wathched disabled')
# Main logic
debug('initial import of mmdb library')
mmdb_library = mmdb.getRemoteMovieLibrary() #initial fetch
#thread.start_new_thread(periodicallyGetRemoteLibrary,())    Removed because python error
GRLCounter = 0



while (not xbmc.abortRequested):
    debug('Reinert START SYNC')
    syncWithMMDB()
    debug(updatedMovies)
    movieUpdatedNotifications()
    sleeper(300000) #5minutes
    GRLCounter += 1
    if(GRLCounter == 12): #60minutes
        mmdb_library = mmdb.getRemoteMovieLibrary()
        debug('Scheduled import of mmdb library')
        GRLCounter = 0
   