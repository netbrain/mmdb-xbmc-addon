import os
import urllib
import urllib2
import simplejson as json
from mymediadb.commonutils import debug,addon

class MMDB:
    cache_path = os.path.dirname(os.path.abspath(__file__))+'/../.cache'
    access_token_file = cache_path+'/mmdb_access_token-%s'
    apiurl = 'http://mymediadb.org/api/0.2'
    client_id = '3c1228f58a86d4c51d81'
    client_secret = '9de2c82a5ffa445b03c67d8220480dca02d14176'
    
    def __init__(self,username,password):
        self.access_token_file = self.access_token_file % username
        self.username = username

        if not os.path.exists(self.cache_path):
            os.makedirs(self.cache_path)

        try:
            f = None
            if os.path.exists(self.access_token_file) and os.path.getsize(self.access_token_file) > 0:
                f = open(self.access_token_file,'r')
                self.access_token = f.readline()
            else:
                f = open(self.access_token_file,'w')
                self.access_token = self.__getToken(username,password)
                f.write(self.access_token)
        except Exception:
            print 'Something wen\'t wrong when handling token creation or read!'
            raise
        finally:
            f.close()

    def getRemoteMovieLibrary(self):
        return self.__getRemoteLibrary('movie')

    def getRemoteEpisodeLibrary(self):
        return self.__getRemoteLibrary('episode')

    def getRemoteSeriesEpisodes(self,id):
        library = []
        offset = 0
        while True:
            request = self.__makeRequest(self.apiurl + '/' + self.access_token + '/series/'+str(id)+'/episodes?offset=' + str(offset))
            f = self.__openRequest(request)
            data = json.load(f)
            library.extend(data)
            if len(data) != 100:
                break
            else:
                offset += 100
        return library

    def addRemoteMediaTag(self,mmdbId,tag):
        request = self.__getTagEndpoint(mmdbId,tag)
        request.get_method = lambda: 'POST'
        f = self.__openRequest(request)
        return json.load(f)

    def removeRemoteMediaTag(self,mmdbId,tag):
        request = self.__getTagEndpoint(mmdbId, tag)
        request.get_method = lambda: 'DELETE'
        f = self.__openRequest(request)
        return json.load(f)

    def search(self, query):
        request = self.__makeRequest('%s/%s/search/%s?advanced=true&reload=false' % (self.apiurl,self.access_token,query))
        response = self.__openRequest(request)
        return json.load(response)

    def __makeRequest(self,url,data = None):
        request = urllib2.Request(url)
        request.add_header("Accept","application/json")
        if data is not None:
                request.add_data(urllib.urlencode(data))

        return request
    
    def __openRequest(self,request):
        if addon.getSetting('debug') == 'true':
            opener = urllib2.build_opener(urllib2.HTTPHandler(debuglevel=1))
        else:
            opener = urllib2.build_opener()

        response = opener.open(request)
        headers = response.info()
        return response

    def __getToken(self,username, password):
        data = {
            'client_id':self.client_id,
            'client_secret':self.client_secret,
            'grant_type':'password',
            'username':username,
            'password':password
        }
        request = self.__makeRequest('%s/oauth/token' % self.apiurl,data)
        response = self.__openRequest(request)
        return json.load(response)['access_token']

    def __getTagEndpoint(self, mmdbId, tag):
        request = self.__makeRequest('%s/%s/user/%s/library/%s/tags/%s' % (self.apiurl,self.access_token,self.username,mmdbId,tag))
        return request

    def __getRemoteLibrary(self,type):
        library = []
        offset = 0
        while True:
            request = self.__makeRequest(
                self.apiurl + '/' + self.access_token + '/user/' + self.username + '/library/'+type+'/list?offset=' + str(
                    offset))
            f = self.__openRequest(request)
            data = json.load(f)
            library.extend(data)
            if len(data) != 100:
                break
            else:
                offset += 100
        return library