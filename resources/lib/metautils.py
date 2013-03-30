
import os
import re
import time
import datetime
import unicodedata
from traceback import print_exc

import xbmc
import xbmcgui
import xbmcvfs
from xbmcaddon import Addon

try:
    import json
    # test json
    json.loads( "[null]" )
except:
    print_exc()
    import simplejson as json
#if json.decoder.c_scanstring is not None:
#    print "[Actors] Yes, json use speedup ;)"
#else:
#    print "[Actors] No, json don't use speedup :("

# constants
ADDON      = Addon( "script.metadata.actors" )
ADDON_DIR  = ADDON.getAddonInfo( "path" )
ADDON_DATA = ADDON.getAddonInfo( "profile" )

Language   = ADDON.getLocalizedString # ADDON strings
LangXBMC   = xbmc.getLocalizedString  # XBMC strings

IS_MUSIC_LIBRARY  = xbmc.getCondVisibility( "Window.IsVisible(MusicLibrary)" )
IS_VIDEO_LIBRARY  = xbmc.getCondVisibility( "Window.IsVisible(Videos)" )
LIBRARY_TYPE = ( ( "", "artist" )[ IS_MUSIC_LIBRARY ], "actor" )[ IS_VIDEO_LIBRARY ]

# https://raw.github.com/xbmc/xbmc/master/xbmc/guilib/Key.h
ACTION_PARENT_DIR    =   9
ACTION_PREVIOUS_MENU =  10
ACTION_SHOW_INFO     =  11
ACTION_NAV_BACK      =  92
ACTION_CONTEXT_MENU  = 117
CLOSE_DIALOG         = [ ACTION_PARENT_DIR, ACTION_PREVIOUS_MENU, ACTION_NAV_BACK ]
CLOSE_SUB_DIALOG     = [ ACTION_CONTEXT_MENU ] + CLOSE_DIALOG

day_month_id_long = {
    "Monday":    11,
    "Tuesday":   12,
    "Wednesday": 13,
    "Thursday":  14,
    "Friday":    15,
    "Saturday":  16,
    "Sunday":    17,
    "January":   21,
    "February":  22,
    "March":     23,
    "April":     24,
    "May":       25,
    "June":      26,
    "July":      27,
    "August":    28,
    "September": 29,
    "October":   30,
    "November":  31,
    "December":  32,
    }

day_month_id_short = {
    "Monday":    41,
    "Tuesday":   42,
    "Wednesday": 43,
    "Thursday":  44,
    "Friday":    45,
    "Saturday":  46,
    "Sunday":    47,
    "January":   51,
    "February":  52,
    "March":     53,
    "April":     54,
    "May":       55,
    "June":      56,
    "July":      57,
    "August":    58,
    "September": 59,
    "October":   60,
    "November":  61,
    "December":  62,
    }


STR_JSONRPC = '{"jsonrpc":"2.0", "id":"1", "method":"Files.GetDirectory", "params":{"directory":"%s", %s"sort":{"method":"label", "order":"ascending"}}}'


def xbmcvfs_makedirs( name, ok=0 ):
    """xbmcvfs_makedirs(path)

    Super-mkdir; create a leaf directory and all intermediate ones.
    Works like mkdir, except that any intermediate path segment (not
    just the rightmost) will be created if it does not exist.  This is
    recursive.

    """
    head, tail = os.path.split( name )
    if not tail:
        head, tail = os.path.split( head )
    if head and tail and not xbmcvfs.exists( head ):
        ok = xbmcvfs_makedirs( head, ok )
        # xxx/newdir/. exists if xxx/newdir exists
        if tail == os.curdir:
            return ok
    ok = xbmcvfs.mkdir( name )
    return ok


def notification( header="", message="", sleep=5000, icon=ADDON.getAddonInfo( "icon" ) ):
    """ Will display a notification dialog with the specified header and message,
        in addition you can set the length of time it displays in milliseconds and a icon image.
    """
    icon = ( "DefaultIconInfo.png", icon )[ os.path.isfile( icon ) ]
    xbmc.executebuiltin( "XBMC.Notification(%s,%s,%i,%s)" % ( header, message, sleep, icon ) )


def keyboard( text="", heading=Language( 32033 ) ):
    kb = xbmc.Keyboard( text, heading, False )
    kb.doModal()
    if kb.isConfirmed():
        return kb.getText()
    return ""


def get_library_movie_details( movieid ):
    props = '["title", "genre", "year", "rating", "director", "trailer", "tagline", "plot", "plotoutline", "originaltitle", "lastplayed", "playcount", "writer", "studio", "mpaa", "cast", "country", "imdbnumber", "premiered", "productioncode", "runtime", "set", "showlink", "top250", "votes", "streamdetails", "fanart", "thumbnail", "file", "resume"]'
    json_string = xbmc.executeJSONRPC( '{"jsonrpc": "2.0", "id":"1", "method":"VideoLibrary.GetMovieDetails", "params": {"movieid": %s, "properties": %s}}' % ( movieid, props ) )
    json_string = unicode( json_string, 'utf-8', errors='ignore' )
    result = ( json.loads( json_string ).get( "result" ) or {} )
    return result.get( "moviedetails" ) or {}


def get_movies_library():
    json_string = xbmc.executeJSONRPC( '{"jsonrpc": "2.0", "id":"1", "method":"VideoLibrary.GetMovies", "params": {"properties":["originaltitle", "playcount", "file", "year"]}}' )
    json_string = unicode( json_string, 'utf-8', errors='ignore' )
    result = ( json.loads( json_string ).get( "result" ) or {} )
    return result.get( "movies" ) or []


def library_has_movie( movies_library, title, original_title, year ):
    OK = None
    title = ( title or "" ).lower()
    original_title = ( original_title or "" ).lower()
    year = int( year )
    for movie in movies_library:
        if year != movie[ "year" ]: continue
        match = original_title and ( movie[ "originaltitle" ].lower() == title or movie[ "originaltitle" ].lower() == original_title )
        match = match or ( title and ( movie[ "label" ].lower() == title or movie[ "label" ].lower() == original_title ) )
        if match:
            OK = movie
            break
    return OK


def load_db_json_string( json_string ):
    if json_string:
        try: return json.loads( json_string )
        except TypeError: pass
        except: print_exc()
    return []


def get_directory( directory, properties='' ):
    json_string = xbmc.executeJSONRPC( STR_JSONRPC % ( directory, properties ) )
    #json_string = unicode( json_string, 'utf-8', errors='ignore' )
    o_json = json.loads( json_string )
    return o_json.get( "result" ) or {}


def getXBMCActors( where=LIBRARY_TYPE, busy=True ):
    directories = []
    if not where or where == "actor":
        directories += [ "videodb://1/4/", "videodb://1/5/" ] # actors, director movies
        directories += [ "videodb://2/4/" ]                   # actros tvshows
        directories += [ "videodb://3/4/" ]                   # artists musicvideo
    if not where or where == "artist":
        directories += [ "musicdb://2/" ]                     # artists music
    #Actors = []
    prt = "library.actors." + ( where or "" )
    Actors = load_db_json_string( unicode( xbmc.getInfoLabel( "Window(10000).Property(%s)" % prt ), "utf-8" ) )
    if not Actors:
        if busy: xbmc.executebuiltin( 'ActivateWindow(busydialog)' )
        for directory in directories:
            Actors += get_directory( directory ).get( "files" ) or []
        if busy: xbmc.executebuiltin( 'Dialog.Close(busydialog,true)' )
        # Test: add Actors GetDirectory to home property for increase speed on next launch
        xbmcgui.Window( 10000 ).setProperty( prt, json.dumps( Actors ) )
    return Actors


def normalize_string( text ):
    try: text = unicodedata.normalize( 'NFKD', text ).encode( 'ascii', 'ignore' )
    except: pass
    return text


def getActorPaths( actor, actors ):
    # get db path for this actor
    videodb = []
    get_actor = normalize_string( actor )
    for actor in actors:
        if normalize_string( actor[ 'label' ] ) == get_actor:
            vdb = actor[ 'file' ]
            if "videodb://1/4/" in vdb:
                item = Language( 32030 )
            elif "videodb://2/4/" in vdb:
                item = Language( 32031 )
            elif "videodb://1/5/" in vdb:
                item = Language( 32032 )
            elif "videodb://3/4/" in vdb:
                item = LangXBMC( 20389 )
            elif "musicdb://2/" in vdb:
                item = LangXBMC( 21888 )
            else:
                continue
            item = "[%i] %s" % ( len( get_directory( vdb ).get( "files" ) or [] ), item )
            videodb.append( [ item, vdb ] )
    return videodb


def clean_bio( bio ):
    if not bio: return bio
    bio = re.sub( '(From Wikipedia, the free encyclopedia)|(Description above from the Wikipedia.*?Wikipedia)', '', bio )
    while True:
        s = bio[ 0 ]
        e = bio[ -1 ]
        if   s == u'\u200b': bio = bio[ 1: ]
        if   e == u'\u200b': bio = bio[ :-1 ]
        if   s == " "  or e == " ":  bio = bio.strip()
        elif s == "."  or e == ".":  bio = bio.strip( "." )
        elif s == "\n" or e == "\n": bio = bio.strip( "\n" )
        else: break
    #print repr( bio )
    return bio.strip() + "."


def get_ages( birthday, deathday ):
    y, m, d = time.strftime( "%Y %m %d", time.localtime( time.time() ) ).split()
    now_in_secs = ( int( y ) * 31556930.0 ) + ( int( m ) * 2551443.84 ) + ( int( d ) * 86400.0 )

    birthday_in_secs = 0
    try:
        y, m, d = birthday.split( "-" )
        birthday_in_secs += ( int( y ) * 31556930.0 ) + ( int( m ) * 2551443.84 ) + ( int( d ) * 86400.0 )
    except:
        birthday_in_secs = 0

    if birthday_in_secs:
        age = int( ( now_in_secs - birthday_in_secs ) / 31536000.0 )
    else:
        birthday_in_secs = now_in_secs
        age = 0

    deathday_in_secs = 0
    try:
        y, m, d = deathday.split( "-" )
        deathday_in_secs += ( int( y ) * 31556930.0 ) + ( int( m ) * 2551443.84 ) + ( int( d ) * 86400.0 )
        deathday_in_secs -= birthday_in_secs
    except:
        deathday_in_secs = 0

    dead_age = int( deathday_in_secs / 31536000.0 )
    dead_since = ""
    if dead_age < 0:
        dead_since = str( dead_age ).strip( "-" )
        dead_age = 0

    if dead_age:
        age = 0

    return str( age or "" ), str( dead_age or "" ), dead_since


def translate_date( str_date, format="long" ):
    dict = ( day_month_id_short, day_month_id_long )[ format == "long" ]
    def lang( s ):
        s = s.group( 1 )
        id = dict.get( s )
        if id: s = LangXBMC( id )
        return s
    try: return re.sub( '(%s)' % '|'.join( dict ), lambda s: lang( s ), str_date )
    except: print_exc()
    return str_date


def get_user_date_format( str_date, format="datelong" ):
    try:
        y, m, d = str_date.split( "-" )
        str_date = datetime.date( int( y ), int( m ), int( d ) )
        if format: #datelong, dateshort
            return str_date.strftime( xbmc.getRegion( format ) )
    except ValueError:
        pass
    except:
        print_exc()
    return str_date


def select_actor_from_xbmc( actors ):
    # used only if used is launched from programs or missing actor_name
    selected_actor = ""
    choices = [
        "%s - %s" % ( LangXBMC( 20342 ), LangXBMC( 344 ) ),   #movies actors
        "%s - %s" % ( LangXBMC( 20342 ), LangXBMC( 20348 ) ), #movies director
        "%s - %s" % ( LangXBMC( 20343 ), LangXBMC( 344 ) ),   #tvshows actors
        LangXBMC( 133 ), # artists
        LangXBMC( 137 )  # search
        ]
    while True:
        # select category
        selected = xbmcgui.Dialog().select( ADDON.getAddonInfo( "name" ), choices )
        # if esc dialog or searching stop while
        selected_actor = ( "", "manual" )[ selected == 4 ]
        if selected in [ -1, 4 ]: break
        # get db path for get actors
        adb = ( "videodb://1/4/", "videodb://1/5/", "videodb://2/4/", "musicdb://2/" )[ selected ]
        # match actors by db path
        choices2 = [ a[ 'label' ] for a in actors if adb in a[ 'file' ] ]
        # selct actor
        selected = xbmcgui.Dialog().select( choices[ selected ], choices2 )
        if selected > -1:
            # if not esc dialog, get our actor name
            selected_actor = choices2[ selected ].encode( 'utf-8' )
            break
    return selected_actor


def flip_fanart( fanart, PIL_Image, quality=85 ):
    if PIL_Image is not None:
        #NB: the EXIF infos is not preserved :(
        try: quality = int( float( quality ) )
        except:
            quality = 85
            print_exc()
        try:
            im = PIL_Image.open( fanart )
            im = im.transpose( PIL_Image.FLIP_LEFT_RIGHT )
            format = ( im.format or "JPEG" )
            #PIL ignore param exif= in save
            try: im.save( fanart, format, quality=quality, dpi=im.info.get( "dpi", ( 0, 0 ) ), exif=im.info.get( "exif", "" ) )
            except: im.save( fanart, "PNG" )
            print "flip_fanart: Success! Quality: %r" % quality
        except:
            print "flip_fanart: Error!"
            print_exc()
    return fanart


def load_trailers():
    trailers = {}
    try:
        f = xbmc.translatePath( ADDON_DATA + "trailers.json" )
        trailers = json.loads( open( f ).read() )
    except:
        pass
    return trailers


def save_trailers( trailer, lang ):
    trailers = load_trailers()
    try:
        trailers[ trailer[ "id" ] ] = trailer, lang
        f = xbmc.translatePath( ADDON_DATA + "trailers.json" )
        file( f, "w" ).write( json.dumps( trailers ) )
    except:
        pass
    return trailers

    
class Thumbnails:
    BASE_THUMB_PATH   = "special://thumbnails/"
    VIDEO_THUMB_PATH  = BASE_THUMB_PATH + "Video/"
    ARTIST_THUMB_PATH = BASE_THUMB_PATH + "Music/Artists/"

    def __init__( self, library_type=LIBRARY_TYPE ):
        self.library_type = library_type

    def get_cached_thumb( self, path1, path2, SPLIT=False, SET_EXT=False ):
        # get the locally cached thumb
        filename = xbmc.getCacheThumbName( path1 )
        if SPLIT:
            thumb = "%s/%s" % ( filename[ 0 ], filename )
        else:
            thumb = filename
        if SET_EXT:
            thumb = os.path.splitext( thumb )[ 0 ] + os.path.splitext( path1 )[ 1 ]
        return [ path2, thumb ]

    def get_cached_actor_fanart( self, strLabel ):
        return self.get_cached_thumb( strLabel, self.VIDEO_THUMB_PATH + "Fanart/" )

    def get_cached_actor_thumb( self, strLabel ):
        return self.get_cached_thumb( "actor" + strLabel, self.VIDEO_THUMB_PATH, True )

    def get_cached_artist_fanart( self, strLabel ):
        return self.get_cached_thumb( strLabel, self.ARTIST_THUMB_PATH.replace( "Artists", "Fanart" ) )

    def get_cached_artist_thumb( self, strLabel ):
        return self.get_cached_thumb( "artist" + strLabel, self.ARTIST_THUMB_PATH )

    def get_cached_url_thumb( self, strPath ):
        return self.get_cached_thumb( strPath, self.BASE_THUMB_PATH, True, True )

    def get_fanarts( self, strLabel ):
        fanart = xbmc.getCacheThumbName( strLabel )
        actor_fanart  = self.VIDEO_THUMB_PATH + "Fanart/" + fanart
        artist_fanart = self.ARTIST_THUMB_PATH.replace( "Artists", "Fanart" ) + fanart
        if self.library_type == "artist":
            return  artist_fanart, actor_fanart
        else:
            return  actor_fanart, artist_fanart

    def get_thumb( self, strPath ):
        if self.library_type == "artist":
            return self.get_cached_artist_thumb( strPath  )

        elif self.library_type == "actor":
            return self.get_cached_actor_thumb( strPath  )

        else:
            #selected = xbmcgui.Dialog().yesno( "Thumbnails!", "Please select appropriate type of person!", "", "", "Actor", "Artist" )
            #self.get_thumb( strPath, ( "actor", "artist" )[ selected ] )
            return [ "", "" ]
