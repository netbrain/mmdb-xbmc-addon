"""
MyMediaDB XBMC Addon
Licensed under GPL3
"""

# Import statements
import sys
import re
import xbmc
import urllib2
from mymediadb.mmdb import MMDB
from mymediadb.xbmcapp import XBMCApp
from mymediadb.commonutils import debug,sleeper,addon

#TAG CONSTANTS
WATCHED = 'watched'
ACQUIRED = 'acquired'

def remoteMovieExists(imdbId):
    for remoteMedia in mmdb_library:
        if remoteMedia['media']['imdbId'] == imdbId:
            return True
    return False

def movieUpdatedNotifications():
    global updatedMovies
    if addon.getSetting('shownotifications') == 'true':
        moviesUpdatedCounter= updatedMovies.__len__()
        del updatedMovies[:]
        if moviesUpdatedCounter > 0:
            xbmc.executebuiltin('Notification(%s,%s,%s,%s)' % (addon.getAddonInfo('name'),"%d movies updated on MMDB" % (moviesUpdatedCounter),7000,addon.getAddonInfo("icon")))

def getRemoteLibrary():
    global mmdb_library
    mmdb_library = []
    mmdb_library.extend(mmdb.getRemoteMovieLibrary())
    mmdb_library.extend(mmdb.getRemoteEpisodeLibrary())

def syncWithMMDB():
    #define global access
    global mmdb_library
    #sync remote media with local db
    if mmdb_library is None:
        debug("mmdb_library = None, is api down/changed?")
        return
    anyRemoteChanges = False
    anyLocalChanges = False
    for remoteData in mmdb_library:
        remoteMedia = remoteData['media']
        remoteTags = remoteData['tags']
        if remoteData['type'] == 'movie':
            if remoteMedia['imdbId'] is not None:
                localMedia = xbmcApp.getLocalMovie(remoteMedia['imdbId'])
                if localMedia is not None:
                    debug('Media exists both locally and remotely - ('+remoteMedia['name']+')')
                    if ACQUIRED not in remoteTags:
                        debug('Setting remote media status to acquired ('+remoteMedia['name']+'['+localMedia['imdbId']+','+remoteMedia['id']+']).')
                        mmdb.addRemoteMediaTag(remoteMedia['id'],ACQUIRED)
                        anyRemoteChanges = True
                    if (WATCHED in remoteTags) != localMedia[WATCHED]:
                        debug('watched status is not synchronized')
                        if addon.getSetting('dontsyncwatched') == 'false':
                            if WATCHED in remoteTags:
                                debug('setting local media to watched')
                                xbmcApp.setLocalFileAsWatched(localMedia['idFile'])
                                anyLocalChanges = True
                            else:
                                debug ('setting remote media to watched ('+remoteMedia['name']+'['+localMedia['imdbId']+','+remoteMedia['id']+']).')
                                mmdb.addRemoteMediaTag(remoteMedia['id'],WATCHED)
                                anyRemoteChanges = True
                        else:
                            debug('Cancelled synchronize of watched status due to settings!')
                else:
                    debug('Media ('+remoteMedia['name']+') exists only remotely')
                    if ACQUIRED in remoteTags:
                        if(addon.getSetting('dontdeleteacquired') == 'false'):
                            debug('Acquired flag was removed from mmdb ('+remoteMedia['name']+'['+remoteMedia['imdbId']+']).')
                            mmdb.removeRemoteMediaTag(remoteMedia['id'],ACQUIRED)
                            anyRemoteChanges = True
                        else:
                            debug('Acquired flag was not removed from mmdb due to settings!')

        elif remoteData['type'] == 'episode':
            if remoteMedia['ttdbId'] is not None:
                localMedia = xbmcApp.getLocalEpisode(remoteMedia['ttdbId'],remoteMedia['season'],remoteMedia['episodeNumber'])
                if localMedia is not None:
                    debug('Media exists both locally and remotely - ('+remoteMedia['name']+')')
                    if ACQUIRED not in remoteTags:
                        debug('Setting remote media status to acquired ('+remoteMedia['name']+'['+localMedia['ttdbId']+','+remoteMedia['id']+']).')
                        mmdb.addRemoteMediaTag(remoteMedia['id'],ACQUIRED)
                        anyRemoteChanges = True
                    if (WATCHED in remoteTags) != localMedia[WATCHED]:
                        debug('watched status is not synchronized')
                        if addon.getSetting('dontsyncwatched') == 'false':
                            if WATCHED in remoteTags:
                                debug('setting local media to watched')
                                xbmcApp.setLocalFileAsWatched(localMedia['idFile'])
                                anyLocalChanges = True
                            else:
                                debug ('setting remote media to watched ('+remoteMedia['name']+'['+localMedia['ttdbId']+','+remoteMedia['id']+']).')
                                mmdb.addRemoteMediaTag(remoteMedia['id'],WATCHED)
                                anyRemoteChanges = True
                        else:
                            debug('Cancelled synchronize of watched status due to settings!')
                else:
                    debug('Media ('+remoteMedia['name']+') exists only remotely')
                    if ACQUIRED in remoteTags:
                        if(addon.getSetting('dontdeleteacquired') == 'false'):
                            debug('Acquired flag was removed from mmdb ('+remoteMedia['name']+'['+remoteMedia['id']+']).')
                            mmdb.removeRemoteMediaTag(remoteMedia['id'],ACQUIRED)
                            anyRemoteChanges = True
                        else:
                            debug('Acquired flag was not removed from mmdb due to settings!')
        else:
            raise RuntimeError('type matched nothing?')

    #sync local media with remote db
    localLibrary = []
    localLibrary.extend(xbmcApp.getLocalEpisodeLibrary())
    localLibrary.extend(xbmcApp.getLocalMovieLibrary())

    for localMedia in localLibrary:
        if 'seriesName' in localMedia:
            #is series/episode
            debug('Episode exists only locally - ('+localMedia['seriesName']+' - ['+localMedia['season']+'x'+localMedia['episode']+'] '+' - '+localMedia['name']+')')
            # TODO should cache the mmdb id <-> imdb id connection found in this search to prevent uneccesary load on
            # mymediadb.org
            result = mmdb.search(localMedia['ttdbId'])
            if 'series' in result and len(result['series']) >= 1:
                #Might be several results, however picking the first should suffice.
                seriesId = result['series'][0]['id']
                episodes = mmdb.getRemoteSeriesEpisodes(seriesId)
                for episode in episodes:
                    if str(episode['season']) == str(localMedia['season']) and str(episode['episodeNumber']) == str(localMedia['episode']):
                        mmdbId = episode['id']
                        mmdb.addRemoteMediaTag(mmdbId,ACQUIRED)
                        if localMedia[WATCHED] == 1:
                            mmdb.addRemoteMediaTag(mmdbId,WATCHED)
                        break
        else:
            #is movie
            if remoteMovieExists(localMedia['imdbId']):
                continue
            debug('Movie exists only locally - ('+localMedia['name']+')')
            # TODO should cache the mmdb id <-> imdb id connection found in this search to prevent uneccesary load on
            # mymediadb.org
            result = mmdb.search(localMedia['imdbId'])
            if 'movie' in result and len(result['movie']) >= 1:
                #Might be several results, however picking the first should suffice.
                mmdbId = result['movie'][0]['id']
                mmdb.addRemoteMediaTag(mmdbId,ACQUIRED)
                if localMedia[WATCHED] == 1:
                    mmdb.addRemoteMediaTag(mmdbId,WATCHED)
                anyRemoteChanges = True

    
    
    movieUpdatedNotifications()     
    if anyRemoteChanges:
        debug('--- MADE REMOTE UPDATE(S) ---')
        getRemoteLibrary()
    elif anyLocalChanges:
        debug('--- MADE LOCAL CHANGE(S)  ---')
    else:
        debug('--- NO CHANGES DETECTED ---')


#Main method
try:
    # Initial validation / first time run?
    if len(addon.getSetting('username')) == 0:
        raise RuntimeWarning('Addon not configured yet! please add your user-details.')

    # Constants
    mmdb = MMDB(addon.getSetting('username'),addon.getSetting('password'))
    xbmcApp = XBMCApp(xbmc.translatePath('special://database/%s' % addon.getSetting('database')))

    # Globals
    mmdb_library = []
    recentlyFailedMedia = []
    updatedMovies = []

    # Print addon information
    print "[ADDON] '%s: version %s' initialized!" % (addon.getAddonInfo('name'), addon.getAddonInfo('version'))
    if(addon.getSetting('shownotifications') == 'true'):
        xbmc.executebuiltin('Notification(%s,%s,%s,%s)' % (addon.getAddonInfo('name'),'is running!',3000,addon.getAddonInfo("icon")))
    
    # Main logic
    debug('initial import of mmdb library')
    getRemoteLibrary() #initial fetch
            
    syncWithMmdbRunsCounter= 0
    
    while not xbmc.abortRequested:
        debug('Syncing local library with mmdb')
        syncWithMMDB()       
        sleeper(300000) #5minutes
        syncWithMmdbRunsCounter += 1
        if syncWithMmdbRunsCounter % 12 == 0: #60minutes
            del recentlyFailedMedia[:]   # Will clear the failedmovies list, since we now got a newer remote medialibrary
            getRemoteLibrary()
            debug('Scheduled import of mmdb library')

except RuntimeWarning as e:
    xbmc.executebuiltin('Notification(%s,%s,%s,%s)' % (addon.getAddonInfo('name'),'%s' % e,5000,addon.getAddonInfo("icon")))
    debug(e)
    sleeper(5000)
    sys.exit(1)

except Exception as e:
    xbmc.executebuiltin('Notification(%s,%s,%s,%s)' % (addon.getAddonInfo('name'),'Error: %s' % e,5000,addon.getAddonInfo("icon")))
    debug(e)
    sleeper(5000)
    raise
