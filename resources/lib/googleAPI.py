
import os
import sys
import time
import urllib

try:
    import json
    # test json
    json.loads( "[null]" )
except:
    import simplejson as json

if sys.version >= "2.5":
    from hashlib import md5 as _hash
else:
    from md5 import new as _hash

try:
    import xbmc
    from xbmcaddon import Addon
    ADDON       = Addon( "script.metadata.actors" )
    ADDON_CACHE = xbmc.translatePath( "%scache/" % ADDON.getAddonInfo( "profile" ) )
    from metautils import xbmcvfs_makedirs
    xbmcvfs_makedirs( ADDON_CACHE )
except:
    ADDON_CACHE = "ADDON_CACHE"
    if not os.path.exists( ADDON_CACHE ):
        os.makedirs( ADDON_CACHE )

BASE_URL = "http://ajax.googleapis.com/ajax/services/search/images?"

USER_AGENT = "Mozilla/5.0 (Windows NT 5.1; rv:10.0.2) Gecko/20100101 Firefox/10.0.2"

class _urlopener( urllib.FancyURLopener ):
    version = os.environ.get( "HTTP_USER_AGENT" ) or USER_AGENT
urllib._urlopener = _urlopener()


def is_expired( lastUpdate, hrs=24 ):
    expired = time.time() >= ( lastUpdate + ( hrs * 60**2 ) )
    return expired


def get_cached_filename( fpath ):
    c_filename = "%s.json" % _hash( repr( fpath ) ).hexdigest()
    return os.path.join( ADDON_CACHE, c_filename )


def _get_json_string( url ):
    try:
        search_results = urllib.urlopen( url )
        s_json = search_results.read()
        search_results.close()
        return s_json
    except:
        pass
    return ""


def getImages( **kwargs ):
    query = { "v": "1.0", "rsz": 8, "safe": "off", "imgsz": "xxlarge" }
    query.update( kwargs )
    url = BASE_URL + urllib.urlencode( query )
    results = []
    # set cached filename
    c_filename = get_cached_filename( url )
    if os.path.exists( c_filename ):
        if not is_expired( os.path.getmtime( c_filename ) ):
            try:
                results = json.loads( open( c_filename ).read() )
                # return immediately results
                #yield results
            except:
                try: os.remove( c_filename )
                except: pass
                results = []

    if not bool( results ):
        #fetch first page
        s_json = _get_json_string( url + "&start=0" )
        o_json = json.loads( s_json )
        results = o_json[ "responseData" ][ "results" ]
        # return immediately results
        #yield results

        try: pages = o_json[ "responseData" ][ "cursor" ][ "pages" ][ 1: ]
        except: pages = []

        # fetch others pages
        for page in pages:
            s_json = _get_json_string( url + "&start=" + page[ "start" ] )
            o_json = json.loads( s_json )
            results += o_json[ "responseData" ][ "results" ]
            # return immediately results
            #yield results

        # save results
        try:
            s_json = json.dumps( results, sort_keys=True, indent=2 )
            file( c_filename, "w" ).write( s_json )
        except:
            try: os.remove( c_filename )
            except: pass
    return results
    """
    [
      "GsearchResultClass",
      "content",
      "contentNoFormatting",
      "height",
      "imageId",
      "originalContextUrl",
      "tbHeight",
      "tbUrl",
      "tbWidth",
      "title",
      "titleNoFormatting",
      "unescapedUrl",
      "url",
      "visibleUrl",
      "width"
    ]
    """



if __name__=="__main__":
    for images in getImages( q="Tatjana Simić wallpaper" ):
        for image in images:
            print json.dumps( image, sort_keys=True, indent=2 )
            print "-"*100