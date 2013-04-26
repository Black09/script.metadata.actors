import time
START_TIME = time.time()

import os
import re
import sys
import random
import urllib
from datetime import datetime

try:
    import xbmc, xbmcvfs
    from xbmcgui import Window
    from xbmcaddon import Addon
    Addon = Addon( "script.metadata.actors" )
    HOME_WINDOW = Window( 10000 )
    JSON_FILE   = xbmc.translatePath( Addon.getAddonInfo( "profile" ).rstrip( "/" ) + "/mostpopularpeopleborn.json" )
    import metautils
    from actorsdb import get_actors_for_backend
    metautils.xbmcvfs_makedirs( os.path.dirname( JSON_FILE ) )
    ACTORSDB = get_actors_for_backend()
    ACTORS   = metautils.getXBMCActors( busy=False )
    TBN      = metautils.Thumbnails()
    STR_ONLINE_INFO = metautils.Language( 32050 )
    clean_bio = metautils.clean_bio
except:
    # NOT RUNNING ON XBMC, ON DEV
    def clean_bio( bio ): return bio
    HOME_WINDOW = None
    JSON_FILE   = "mostpopularpeopleborn.json"
    ACTORSDB    = {}
    ACTORS      = []
    TBN         = None
    STR_ONLINE_INFO = 'Show Info on IMDB (require a web browser)'

try:
    import json
    # test json
    json.loads( "[null]" )
except:
    import simplejson as json

from htmldecode import *


BIRTH_MONTHDAY = datetime.today().strftime( "%m-%d" )


class _urlopener( urllib.FancyURLopener ):
    version = "Mozilla/5.0 (Windows NT 5.1; rv:10.0.2) Gecko/20100101 Firefox/10.0.2"
urllib._urlopener = _urlopener()


def get_html_source():
    try:
        query = { "birth_monthday": BIRTH_MONTHDAY, "refine": "birth_monthday", "sort": "starmeter", "count": 100 }
        f = urllib.urlopen( "http://www.imdb.com/search/name?" + urllib.urlencode( query ) )
        s = f.read()
        f.close()
        return s
    except:
        pass
    return ""


def getMostPopularPeopleBorn():
    results = []
    html = htmlentitydecode( get_html_source().decode( "utf-8" ) )

    for detailed in re.compile( '<tr class=".*? detailed">(.*?)</tr>', re.S ).findall( html ):
        urlinfo, name = re.findall( '<a href="(/name/.*?/)">(.*?)</a>', detailed )[ 0 ]
        results.append( ( name, "http://www.imdb.com" + urlinfo,
            "".join( re.findall( '<img src="(.*?)".*?></a>', detailed ) ),
            set_pretty_formatting( "".join( re.findall( '<span class="description">(.*?)</span>', detailed ) ) ),
            set_pretty_formatting( "".join( re.findall( '<span class="bio">(.*?)</span>', detailed ) ) ),
            ) )

    return BIRTH_MONTHDAY, results


def loadPeoples():
    try:
        s_json = open( JSON_FILE ).read()
        o_json = json.loads( s_json )
    except:
        o_json = [ "", [] ]

    if o_json[ 0 ] != BIRTH_MONTHDAY:
        o_json = getMostPopularPeopleBorn()
        s_json = json.dumps( o_json, indent=2 )
        file( JSON_FILE, "wb" ).write( s_json )

    return o_json[ 1 ]


def SetProperty( key, value="" ):
    if HOME_WINDOW:
        HOME_WINDOW.setProperty( key, value )
    else:
        # for test print
        print ( key, value )


def ClearProperties( limit ):
    for i in range( 1, limit+1 )[ ::-1 ]:
        b_prop = "peopleborntoday.%i." % i
        for prop in [ "name", "job", "bio", "urlinfo", "icon", "fanart", "extrafanart", "extrathumb" ]:
            SetProperty( b_prop + prop )

            for i in range( 1, limit+1 )[ ::-1 ]:
                m_prop = b_prop + "media.%i." % ( i + 1 )
                for prop in [ "title", "icon", "fanart", "file", "type", "folder", "isplayable", "library" ]:
                    SetProperty( m_prop + prop )


def setImages( b_prop, name ):
    if not TBN: return
    SetProperty( b_prop + "fanart", "" )
    for fanart in TBN.get_fanart( name ):
        if xbmcvfs.exists( fanart ):
            SetProperty( b_prop + "fanart", fanart )
            break
    # check exist to prevent multiple ERROR: XFILE::CDirectory::GetDirectory - Error getting special://thumbnails/Actors/[ACTOR NAME]/foo/
    cached_actor_thumb = "special://thumbnails/Actors/" + name + "/"
    for extra in [ "extrafanart", "extrathumb" ]:
        #SetProperty( b_prop + extra, "" )
        #if xbmcvfs.exists( cached_actor_thumb + extra ):
        SetProperty( b_prop + extra, cached_actor_thumb + extra )
    # set icon and return true if exists
    icon = "".join( TBN.get_cached_actor_thumb( name ) )
    if not xbmcvfs.exists( icon ):
        icon = "".join( TBN.get_cached_artist_thumb( name ) )
    if xbmcvfs.exists( icon ):
        SetProperty( b_prop + "icon", icon )
        return True


def Main():
    try: limit = int( sys.argv[ 2 ] )
    except: limit = 10
    if limit > 100: limit = 100
    ClearProperties( limit )

    peoples = loadPeoples()
    if "".join( sys.argv[ 3: ] ).lower() == "random":
        random.shuffle( peoples )
        peoples = random.sample( peoples, limit )
    else:
        peoples = peoples[ :limit ]

    for i, people in enumerate( peoples ):
        b_prop = "peopleborntoday.%i." % ( i + 1 )
        SetProperty( b_prop + "name",    people[ 0 ] )
        SetProperty( b_prop + "job",     people[ 3 ] )
        bio = people[ 4 ]
        indb = ACTORSDB.get( people[ 0 ] )
        if not bio and indb: bio = clean_bio( indb[ 3 ] or "" )
        SetProperty( b_prop + "bio", bio )
        #print ( bio, indb )

        if not setImages( b_prop, people[ 0 ] ):
            SetProperty( b_prop + "icon", "" )
            icon = people[ 2 ].split( "," )[ 0 ]
            if not icon.endswith( "name.gif" ):
                SetProperty( b_prop + "icon", icon )

        urlinfo = [ people[ 0 ] ]
        if ACTORS:
            #get actor paths and list movies
            paths = metautils.getActorPaths( people[ 0 ], ACTORS )
            if paths:
                urlinfo += paths
                # for fmronan
                count = 0
                for txt, dir in paths:
                    # enum medias
                    for media in ( metautils.get_directory( dir, '"properties":["fanart", "thumbnail"],' ).get( "files" ) or [] ):
                        count += 1
                        m_prop = b_prop + "media.%i." % count
                        SetProperty( m_prop + "title",  media[ "label" ] )
                        SetProperty( m_prop + "icon",   media[ "thumbnail" ] )
                        SetProperty( m_prop + "fanart", media[ "fanart" ] )
                        SetProperty( m_prop + "file",   media[ "file" ] )
                        SetProperty( m_prop + "folder", os.path.dirname( media[ "file" ] ) )
                        SetProperty( m_prop + "type",   media[ "type" ] )
                        if media.get( "filetype" ) == "file":
                            SetProperty( m_prop + "isplayable", "true" )
                            SetProperty( m_prop + "library", dir )
                        else:
                            library = ""
                            # library path
                            if "videodb://1/4/" in dir or "videodb://1/5/" in dir:
                                library = "videodb://1/2/"
                            elif "videodb://2/4/" in dir:
                                library = "videodb://2/2/%s/" % str( media[ "id"] )
                            elif "videodb://3/4/" in dir:
                                library = "videodb://3/2/%s/" % str( media[ "id"] )
                            elif "musicdb://2/" in dir:
                                library = "musicdb://2/%s/" % str( media[ "id"] )
                            else:
                                print dir
                            SetProperty( m_prop + "library", library )

                        if limit <= count <= 25: break
            
        urlinfo.append( [ STR_ONLINE_INFO, people[ 1 ] ] )
        SetProperty( b_prop + "urlinfo", repr( urlinfo ) )

        #print "-"*100



if __name__ == "__main__":
    #sys.argv.append( "25" )
    #sys.argv.append( "random" )
    Main()
    print time.time() - START_TIME
