import urllib2
import base64
import simplejson as json

class MMDB: 
    
    apiurl = 'http://mymediadb.org/api/0.1'
    session_cookie = None
    
    def __init__(self,username,password):
        self.username = username;
        self.password = password;
        
    def makeRequest(self,url):
        request = urllib2.Request(url)
        #debug('remote url='+url)    
        if(self.session_cookie != None):
            request.add_header("Cookie", self.session_cookie)
            
        base64string = base64.encodestring('%s:%s' % (self.username, self.password)).replace('\n', '')            
        request.add_header("Authorization", "Basic %s" % base64string)
        request.add_header("Content-Type","text/json")
        return request
    
    def openRequest(self,request):
        opener = urllib2.build_opener()
        response = None
    #    try:
        response = opener.open(request)
        headers = response.info()
        if('set-cookie' in headers):
            self.session_cookie = headers['set-cookie']
    #    except urllib2.URLError, e:
    #        if(e.code == 401):
    #            xbmc.executebuiltin('Notification(%s,%s,%s,%s)' % (addon.getAddonInfo('name'),e,3000,addon.getAddonInfo("icon")))
        return response
    
       
    def getRemoteMovieLibrary(self):
        request = self.makeRequest(self.apiurl+'/user')
        f = self.openRequest(request)
        if(f == None):
            return None
        library = json.load(f)['mediaLibrary']
        for i, media in enumerate(library):
            tags = self.getRemoteMovieTags(media['mediaId'])
            library[i].update(tags)
        return library
    
    def getRemoteMovieTags(self,mediaId):
        request = self.makeRequest(self.apiurl+'/userMedia?mediaType=movie&idType=mmdb&id=%s' % mediaId)
        f = self.openRequest(request)
        if(f != None):
            return json.load(f)
        return None
    
    def setRemoteMovieTag(self,imdbId,postdata):
    #    if(addon.getSetting('testmode') == 'false'):
    #        self.setUpdatedMovies(imdbId)            
            request = self.makeRequest(self.apiurl+'/userMedia?mediaType=movie&idType=imdb&id=%s' % imdbId)
            request.add_data(json.dumps(postdata))
            request.get_method = lambda: 'PUT'
            f = self.openRequest(request)
            if(f != None):
                json.load(f)
    #    else:
    #        debug('MMDB Testmode cancelled API request "setRemoteMovieTag"')
            
    
        