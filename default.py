"""
MyMediaDB XBMC Addon
Licensed under GPL3
Author: netbrain
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

def makeRequest(url):
    request = urllib2.Request(url)
    #debug('remote url='+url)
    base64string = base64.encodestring('%s:%s' % (addon.getSetting('username'), addon.getSetting('password'))).replace('\n', '')
    request.add_header("Authorization", "Basic %s" % base64string)
    request.add_header("Content-Type","text/json")
    return request

def openRequest(request):
    opener = urllib2.build_opener()
    try:
        return opener.open(request)
    except urllib2.URLError, e:
        if(e.code == 401):
            xbmc.executebuiltin('Notification(%s,%s,%s,%s)' % (addon.getAddonInfo('name'),e,3000,addon.getAddonInfo("icon")))
    return None

   
def getRemoteMovieLibrary():
    request = makeRequest(apiurl+'/user')
    f = openRequest(request)
    if(f == None):
        return None
    library = json.load(f)['mediaLibrary']
    for i, media in enumerate(library):
        #=======================================================================
        # debug("MEDIA")
        # debug(media)
        #=======================================================================
        tags = getRemoteMovieTags(media['mediaId'])
        #=======================================================================
        # debug("TAGS")
        # debug(tags)
        #=======================================================================
        library[i].update(tags)
    return library

def getRemoteMovieTags(mediaId):
    request = makeRequest(apiurl+'/userMedia?mediaType=movie&idType=mmdb&id=%s' % mediaId)
    f = openRequest(request)
    if(f != None):
        return json.load(f)
    return None

def setRemoteMovieTag(imdbId,postdata):
    request = makeRequest(apiurl+'/userMedia?mediaType=movie&idType=imdb&id=%s' % imdbId)
    request.add_data(json.dumps(postdata))
    request.get_method = lambda: 'PUT'
    f = openRequest(request)
    if(f != None):
        json.load(f)

def getLocalMovieLibrary():
    result = []
    connection = sqlite.connect(moviedb)
    cursor = connection.cursor()
    cursor.execute( "select movie.idMovie,movie.idFile,movie.c09 as imdbId,movie.c00 as name, case when files.playCount > 0 then 1 else 0 end as watched from movie left join files on (movie.idFile = files.idFile)")    
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

def remoteMovieExists(imdbId):
    for remoteMedia in mmdb_library:
        if(remoteMedia['imdbId'] == imdbId):
            return True
    return False

def setLocalMovieAsWatched(idFile):
    connection = sqlite.connect(moviedb)
    cursor = connection.cursor()
    cursor.execute("update files SET playCount=1 where idFile=?",(idFile,))    
    connection.commit()
    connection.close()

def periodicallyGetRemoteLibrary():
    while (not xbmc.abortRequested):
        sleeper(3600000) #1 hour
        debug('perodically import of remote library initiated')
        mmdb_library = getRemoteMovieLibrary()                 

def syncWithMMDB():
    #define global access
    global mmdb_library
    #sync remote media with local db
    if(mmdb_library == None):
        debug("mmdb_library = None, is api down/changed?")
        return
    for remoteMedia in mmdb_library:
        anyRemoteChanges = False
        localMedia = getLocalMovie(remoteMedia['imdbId'])
        if (localMedia != None):
            debug('Media exists both locally and remotely - ('+remoteMedia['name']+')')
            if(remoteMedia['experienced'] != localMedia['watched']):
                debug('watched status is not synchronized')
                if(remoteMedia['experienced']):
                    debug('setting local media to watched')
                    setLocalMovieAsWatched(localMedia['idFile'])
                else:
                    debug ('setting remote media to watched')
                    setRemoteMovieTag(localMedia['imdbId'],{'experienced':localMedia['watched'] == 1})
                    anyRemoteChanges = True
        else:
            debug('Media ('+remoteMedia['name']+') exists only remotely')
            setRemoteMovieTag(remoteMedia['imdbId'],{'acquired':False})
            anyRemoteChanges = True
            
    #sync local media with remote db
    for localMedia in getLocalMovieLibrary():
        if(remoteMovieExists(localMedia['imdbId'])):
            continue
        debug('Media exists only locally - ('+localMedia['name']+')')
        setRemoteMovieTag(localMedia['imdbId'],{'acquired': True, 'experienced':localMedia['watched'] == 1})
        anyRemoteChanges = True
    if(anyRemoteChanges):
        debug('--- SYNCED WITH MMDB ---')
        mmdb_library = getRemoteMovieLibrary() #sync local copy with changes on remote
    else:
        debug('--- NO CHANGES DETECTED ---')

# Constants
addon = xbmcaddon.Addon(id='script.mymediadb')
apiurl = 'http://mymediadb.org/api/0.1'
moviedb = xbmc.translatePath('special://database/%s' % addon.getSetting('database'))

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


# Globals (let's hope this is thread safe)
mmdb_library = []

# Print addon information
print "[ADDON] '%s: version %s' initialized!" % (addon.getAddonInfo('name'), addon.getAddonInfo('version'))
xbmc.executebuiltin('Notification(%s,%s,%s,%s)' % (addon.getAddonInfo('name'),'is running!',3000,addon.getAddonInfo("icon")))

# Print debug info
if(addon.getSetting('debug') == 'true'):
    print '---- '+addon.getAddonInfo('name')+'- DEBUG ----'
    print 'username=%s' % addon.getSetting('username')
    print 'password=%s' % addon.getSetting('password')
    print 'moviedb=%s' % moviedb
    print '---- '+addon.getAddonInfo('name')+'- DEBUG ----'

# Main logic
debug('initiall import of mmdb library')
mmdb_library = getRemoteMovieLibrary() #initial fetch
thread.start_new_thread(periodicallyGetRemoteLibrary,())
while (not xbmc.abortRequested):
    syncWithMMDB()
    sleeper(300000) #5minutes



    
    