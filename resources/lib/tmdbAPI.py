
DEBUG = 0

import os
import sys
import urllib
import urllib2
from datetime import datetime
from traceback import print_exc

try:
    import json
    # test json
    json.loads( "[null]" )
except:
    import simplejson as json


USER_AGENT = "XBMC Metadata Actors/Dev"
try:
    import xbmc, xbmcvfs
    from xbmcaddon import Addon
    ADDON = Addon( "script.metadata.actors" )
    USER_AGENT = USER_AGENT.replace( "Dev", ADDON.getAddonInfo( "version" ), 1 )
    USER_AGENT += " (XBMC for %s %s; %s)" % ( sys.platform, xbmc.getInfoLabel( "System.BuildVersion" ), xbmc.getInfoLabel( "System.BuildDate" ) )
    ADDON_CACHE = xbmc.translatePath( "%smovies/" % ADDON.getAddonInfo( "profile" ) )
    from metautils import xbmcvfs_makedirs
    xbmcvfs_makedirs( ADDON_CACHE )
    USER_TIME_FORMAT  = xbmc.getRegion( "time" ).replace( ':%S', '', 1 )
    DATE_SHORT_FORMAT = xbmc.getRegion( "dateshort" )
except:
    USER_AGENT += " (Python %s on %s)" % ( sys.version, sys.platform )
    ADDON_CACHE = "movies"
    if not os.path.exists( ADDON_CACHE ): os.makedirs( ADDON_CACHE )
    USER_TIME_FORMAT  = '%H:%M'
    DATE_SHORT_FORMAT = '%Y-%m-%d'


class _urlopener( urllib.FancyURLopener ):
    version = os.environ.get( "HTTP_USER_AGENT" ) or USER_AGENT
urllib._urlopener = _urlopener()


# http://help.themoviedb.org/kb/api/about-3 and/or http://api.themoviedb.org/2.1/
# The API key we supplied you with for your account.
APIKEY  = "d12bf766b6df5b909eedeaf2ba0d3429"
# basic Authentication
HEADERS = { "Accept": "application/json", "User-Agent": USER_AGENT }


# Retrieve JSON data from site
def _get_json_new( url, params={} ):
    parsed_json = {}
    try:
        params.update( { "api_key": APIKEY } )
        url += "?" + urllib.urlencode( params )
        request = urllib2.Request( url, headers=HEADERS )

        req = urllib2.urlopen( request )
        json_string = req.read()
        req.close()

        json_string = unicode( json_string, 'utf-8', errors='ignore' )
        parsed_json = json.loads( json_string )
    except:
        print_exc()
    return parsed_json


def search_person( person="", page=1, include_adult="false" ):
    """ This is a good starting point to start finding peoples on TMDb.
        The idea is to be a quick and light method so you can iterate through peoples quickly.
        This method is purposefully lighter than the 2.1 search. It searches. That’s all.
    """
    if not person: return {}
    url = "http://api.themoviedb.org/3/search/person"
    js  = _get_json_new( url, { "query": person, "page": str( page ), "include_adult": include_adult } )
    if DEBUG:
        #print js
        print json.dumps( js, sort_keys=True, indent=2 )
    return js


def person_info( person_id=19429 ):
    """ This method is used to retrieve all of the basic person information.
        It will return the single highest rated profile image.
    """
    url = "http://api.themoviedb.org/3/person/" + str( person_id )
    js  = _get_json_new( url )
    if DEBUG:
        #print js
        print json.dumps( js, sort_keys=True, indent=2 )
    return js


def person_credits( person_id=19429, language="en" ):
    """ This method is used to retrieve all of the cast & crew information for the person.
        It will return the single highest rated poster for each movie record.

        language : "da|fi|nl|de|it|es|fr|pl|hu|el|tr|ru|he|ja|pt|zh|cs|sl|hr|ko|en|sv|no"
    """
    url = "http://api.themoviedb.org/3/person/%s/credits" % str( person_id )
    js  = _get_json_new( url, { "language": language } )
    if DEBUG:
        #print js
        print json.dumps( js, sort_keys=True, indent=2 )
    return js


def person_images( person_id=19429 ):
    """ This method is used to retrieve all of the profile images for a person.
    """
    url = "http://api.themoviedb.org/3/person/%s/images" % str( person_id )
    js  = _get_json_new( url )
    if DEBUG:
        #print js
        print json.dumps( js, sort_keys=True, indent=2 )
    return js


def get_movie_trailers( movie_id=72545, language="en" ):
    """ This method is used to retrieve all of the trailers for a particular movie.
        Supported sites are YouTube and QuickTime.
    """
    url = "http://api.themoviedb.org/3/movie/%s/trailers"  % str( movie_id )
    js  = _get_json_new( url, { "language": language } )
    if DEBUG:
        #print js
        print json.dumps( js, sort_keys=True, indent=2 )
    # if not trailer in language user. try english
    if not js.get( "youtube" ) and language.lower() != "en":
        return get_movie_trailers( movie_id, "en" )
    return js, language


def get_movie( movie_id=72545, language="en" ):
    """ This method is used to retrieve all of the basic movie information.
        It will return the single highest rated poster and backdrop.
        And is used to retrieve all of the movie cast information.
        The results are split into separate cast and crew arrays.
    """
    url = "http://api.themoviedb.org/3/movie/%s" % str( movie_id )
    try:
        js  = _get_json_new( url, { "language": language } )
        js.update( _get_json_new( url + "/casts" ) )
        js.update( _get_json_new( url + "/releases" ) )
        js[ "trailers" ] = get_movie_trailers( movie_id, language )
    except HTTPError:
        pass

    if DEBUG:
        #print js
        print json.dumps( js, sort_keys=True, indent=2 )

    return js, language


def full_person_info( person_id=19429, language="en" ):
    infos = {}
    infos.update( person_info( person_id ) )
    infos.update( person_credits( person_id, language ) )
    infos.update( person_images( person_id ) )

    if DEBUG:
        print json.dumps( infos, sort_keys=True, indent=2 )

    return infos


def configuration( refresh=False ):
    """ Some elements of the API require some knowledge of the configuration data which can be found here.
        The purpose of this is to try and keep the actual API responses as light as possible.
        That is, by not repeating a bunch of data like image URLs or sizes.
    """
    js = {u'images': {u'poster_sizes': [u'w92', u'w154', u'w185', u'w342', u'w500', u'original'], u'profile_sizes': [u'w45', u'w185', u'h632', u'original'], u'backdrop_sizes': [u'w300', u'w780', u'w1280', u'original'], u'base_url': u'http://cf2.imgobject.com/t/p/'}}
    if refresh: js = _get_json_new( "http://api.themoviedb.org/3/configuration" )
    if DEBUG:
        #print js
        print json.dumps( js, sort_keys=True, indent=2 )
    return js[ 'images' ]



def download( url, destination ):
    OK, dl_path = False, ""
    try:
        destination = destination + os.path.basename( url )
        try:
            fp, h = urllib.urlretrieve( url, destination )
            #try:
            #    print "%r" % fp
            #    print str( h ).replace( "\r", "" )
            #except:
            #    pass
            OK = xbmcvfs.exists( destination )
            dl_path = destination
        except:
            xbmcvfs.delete( destination )
            print "%r xbmcvfs.delete(%r)" % ( not xbmcvfs.exists( destination ), destination )
    except:
        print_exc()
    return OK and dl_path


def trim_time( str_time ):
    if str_time.startswith( "0" ):
        str_time = str_time[ 1: ]
    return str_time


from locale import getdefaultlocale
try: LOC_ISO = getdefaultlocale()[ 0 ].split( "_" )[ -1 ]
except: LOC_ISO = "US"
def save_movie_info( movie ):
    #save info to xbmc json format
    x_json = {
      "cast": [],
      "country": "",
      "director": "",
      "fanart": "",
      "file": "",
      "genre": "",
      "imdbnumber": "",
      "label": "",
      "lastplayed": "",
      "movieid": -1,
      "mpaa": "",
      "originaltitle": "",
      "playcount": 0,
      "plot": "",
      "plotoutline": "",
      "premiered": "",
      "productioncode": "",
      "rating": 0.0,
      "resume": {
        "position": 0,
        "total": 0
      },
      "runtime": "",
      "set": [],
      "showlink": "",
      "streamdetails": {},
      "studio": "",
      "tagline": "",
      "thumbnail": "",
      "title": "",
      "top250": 0,
      "trailer": "",
      "votes": "",
      "writer": "",
      "year": 0
    }
    # get configuration: images path and sizes
    config = configuration()
    # set our person image path
    profile_path = config[ "base_url" ] + config[ "profile_sizes" ][ 2 ]
    # set our movie image path
    poster_path  = config[ "base_url" ] + config[ "poster_sizes" ][ 5 ]
    # set our fanart image path
    backdrop_path = config[ "base_url" ] + config[ "backdrop_sizes" ][ 3 ]

    # set our fanart
    if movie[ "poster_path" ]:
        x_json[ "thumbnail" ] = poster_path + movie[ "poster_path" ]
    # set our fanart
    if movie[ "backdrop_path" ]:
        x_json[ "fanart" ] = backdrop_path + movie[ "backdrop_path" ]
    # set out country
    if movie[ "production_countries" ]:
        x_json[ "country" ] = " / ".join( [ c[ "name" ] for c in movie[ "production_countries" ] ] )
    # set our genres
    if movie[ "genres" ]:
        x_json[ "genre" ] = " / ".join( [ g[ "name" ] for g in movie[ "genres" ] ] )
    # set our imdbnumber
    x_json[ "imdbnumber" ] = movie[ "imdb_id" ] or ""
    # set our label and title
    x_json[ "label" ] = x_json[ "title" ] = movie[ "title" ] or ""
    # set our movieid
    x_json[ "movieid" ] = movie[ "id" ] or ""
    # set our originaltitle
    x_json[ "originaltitle" ] = movie[ "original_title" ] or ""
    # set our plot
    x_json[ "plotoutline" ] = x_json[ "plot" ] = movie[ "overview" ] or ""
    # set our release date
    x_json[ "releasedate" ] = movie[ "release_date" ] or ""
    # set our lastupdated
    x_json[ "lastupdated" ] = datetime.now().strftime( DATE_SHORT_FORMAT ) + " " + trim_time( datetime.now().strftime( USER_TIME_FORMAT ) )
    # set our rating
    x_json[ "rating" ] = movie[ "vote_average" ] or 0.0
    # set our runtime
    x_json[ "runtime" ] = str( movie[ "runtime" ] or "0" )
    # set our movie set
    if movie[ "belongs_to_collection" ]:
        x_json[ "set" ] = [ movie[ "belongs_to_collection" ][ "name" ] ]
    # set out production_companies
    if movie[ "production_companies" ]:
        x_json[ "studio" ] = " / ".join( [ s[ "name" ] for s in movie[ "production_companies" ] ] )
    # set our tagline
    x_json[ "tagline" ] = movie[ "tagline" ] or ""
    # set our votes
    x_json[ "votes" ] = str( movie[ "vote_count" ] or "" )
    # set our trailers
    x_json[ "trailers" ] = movie[ "trailers" ] or ""
    # set cast and role
    x_cast = []
    for c in sorted( movie[ "cast" ], key=lambda c: c.get( "order" ) ):
        cast = { "name": c[ "name" ], "role": c[ "character" ] }
        if c[ "profile_path" ]:
            cast[ "thumbnail" ] = profile_path + c[ "profile_path" ]
        x_cast.append( cast )

    director, writer = [], []
    # set extra crew to cast
    for c in movie[ "crew" ]:
        crew = { "name": c[ "name" ], "role": c[ "job" ] }
        if c[ "profile_path" ]:
            crew[ "thumbnail" ] = profile_path + c[ "profile_path" ]
        x_cast.append( crew )
        if c[ "department" ].lower() == "directing":
            director.append( c[ "name" ] )
        else:
            writer.append( c[ "name" ] )
    x_json[ "cast" ] = x_cast

    # set director and writer
    x_json[ "director" ] = " / ".join( director )
    x_json[ "writer" ]   = " / ".join( writer )

    # set our home page of movie
    if movie.get( "homepage" ):
        x_json[ "homepage" ] = movie[ "homepage" ]

    # set our mpaa and release date based on user locale info ( default: USA )
    if movie.get( "countries" ):
        for country in movie[ "countries" ]:
            if not x_json[ "mpaa" ] and country[ "iso_3166_1" ] == "US":
                x_json[ "mpaa" ] = country[ "certification" ]
                x_json[ "releasedate" ] = country[ "release_date" ]

            elif country[ "iso_3166_1" ] == LOC_ISO:
                x_json[ "mpaa" ] = country[ "certification" ]
                x_json[ "releasedate" ] = country[ "release_date" ]
                if x_json[ "mpaa" ]: break

        if x_json[ "mpaa" ]:
            x_json[ "mpaa" ] = "Rated " + x_json[ "mpaa" ]

    if movie[ "release_date" ]:
        y, m, d = movie[ "release_date" ].split( "-" )
        dt = datetime( int( y ), int( m ), int( d ) )
        # set our year
        x_json[ "year" ] = dt.year
        # set our date
        x_json[ "date" ] = dt.strftime( '%d.%m.%Y' )
        # reset our release date to date format %d.%m.%Y
        x_json[ "releasedate" ] = dt.strftime( DATE_SHORT_FORMAT )

    f = os.path.join( ADDON_CACHE, "%s.json" % str( x_json[ "movieid" ] ) )
    file( f, "w" ).write( json.dumps( x_json, indent=2 ) )
    return x_json


def load_movie_info( movieid ):
    info = {}
    try:
        f = os.path.join( ADDON_CACHE, "%s.json" % str( movieid ) )
        info = json.loads( open( f ).read() )
    except:
        pass
    return info



if __name__=="__main__":
    import time
    t1 = time.time()

    #js = configuration()
    #print "-"*100
    DEBUG = 1

    movieid, lang = 10138, "fr"
    movie = load_movie_info( movieid )
    if not movie:
        js, lang = get_movie( movieid, lang )
        movie = save_movie_info( js )
    #print json.dumps( movie, sort_keys=True, indent=2 )
    
    #js = get_movie_trailers()
    #js = search_person( "Bruce Lee" )
    #print "-"*100

    #js = full_person_info( 19429, "fr" )
    #print "-"*100

    print time.time() - t1
