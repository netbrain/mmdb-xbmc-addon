from mymediadb.commonutils import debug,addon
try:
    from sqlite3 import dbapi2 as sqlite
    print "Loading sqlite3 as DB engine"
except:
    from pysqlite2 import dbapi2 as sqlite
    print "Loading pysqlite2 as DB engine"

class XBMCApp:

    def __init__(self,moviedb):
        self.moviedb = moviedb

    def getLocalMovieLibrary(self):
        result = []
        connection = sqlite.connect(self.moviedb)
        cursor = connection.cursor()
        cursor.execute( "select movie.idMovie,movie.idFile,movie.c09 as imdbId,movie.c00 as name, case when files.playCount > 0 then 1 else 0 end as watched from movie left join files on (movie.idFile = files.idFile)")
        for row in cursor:
            result.append(self.__createProperRowFromCursor(cursor,row))
        connection.close()
        return result

    def getLocalEpisodeLibrary(self):
        result = []
        connection = sqlite.connect(self.moviedb)
        cursor = connection.cursor()
        cursor.execute( "select episode.idEpisode, episode.idFile, episode.c00 as name, episode.c12 as season, episode.c13 as episode, tvshow.c12 as ttdbId, tvshow.c00 as seriesName, case when files.playCount > 0 then 1 else 0 end as watched from episode left join files on (episode.idFile = files.idFile) left join tvshowlinkepisode on (episode.idEpisode == tvshowlinkepisode.idEpisode) left join tvshow on (tvshow.idShow == tvshowlinkepisode.idShow)")
        for row in cursor:
            result.append(self.__createProperRowFromCursor(cursor,row))
        connection.close()
        return result

    def getLocalMovie(self,imdbId):
        if imdbId == None:
            raise RuntimeError("ImdbId cannot be None")
        connection = sqlite.connect(self.moviedb)
        cursor = connection.cursor()
        cursor.execute("select movie.idMovie,movie.idFile,movie.c09 as imdbId,movie.c00 as name, case when files.playCount > 0 then 1 else 0 end as watched from movie left join files on (movie.idFile = files.idFile) where imdbId=?",(imdbId,))    
        result = self.__createProperRowFromCursor(cursor,cursor.fetchone())
        connection.close()
        return result 

    def getLocalEpisode(self,ttdbId,season,episode):
        connection = sqlite.connect(self.moviedb)
        cursor = connection.cursor()
        cursor.execute( "select episode.idEpisode, episode.idFile, episode.c00 as name, episode.c12 as season, episode.c13 as episode, tvshow.c12 as ttdbId, tvshow.c00 as seriesName, case when files.playCount > 0 then 1 else 0 end as watched from episode left join files on (episode.idFile = files.idFile) left join tvshowlinkepisode on (episode.idEpisode == tvshowlinkepisode.idEpisode) left join tvshow on (tvshow.idShow == tvshowlinkepisode.idShow) where ttdbId=? and season=? and episode=?",(ttdbId,season,episode))
        result = self.__createProperRowFromCursor(cursor,cursor.fetchone())
        connection.close()
        return result

    def setLocalFileAsWatched(self,idFile):
        connection = sqlite.connect(self.moviedb)
        cursor = connection.cursor()
        cursor.execute("update files SET playCount=1 where idFile=?",(idFile,))
        connection.commit()
        totalChanges = connection.total_changes
        connection.close()
        if totalChanges == 0:
            raise RuntimeError('Expected 1 updated row, got 0')
    
    def __createProperRowFromCursor(self,cursor, row):
        if row is None:
            return None
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d