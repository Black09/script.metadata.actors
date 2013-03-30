
# Modules General
import Queue
from random import shuffle
from threading import Timer
from collections import deque
from datetime import datetime
from traceback import print_exc

# Modules XBMC
import xbmc
import xbmcgui
import xbmcvfs
from xbmcaddon import Addon

# Modules Custom
import common
metautils = common.metautils
actorsdb  = common.actorsdb
import tmdbAPI
import dialogs


# Constants
ADDON    = metautils.ADDON
Language = metautils.Language  # ADDON strings
LangXBMC = metautils.LangXBMC  # XBMC strings
ACTORS   = metautils.getXBMCActors()
TBN      = metautils.Thumbnails()
CONTAINER_REFRESH     = False
RELOAD_ACTORS_BACKEND = False
BIRTH_MONTHDAY        = datetime.today().strftime( "%m-%d" )


class Stack( Queue.Queue ):
    "Thread-safe stack"
    # method aliases
    push = Queue.Queue.put
    pop  = Queue.Queue.get
    pop_nowait = Queue.Queue.get_nowait
    def _get( self ):
        return self.queue.pop()
    def _put( self, item ):
        # add at the end, if not exists
        #if item not in self.queue:
        self.queue.append( item )
    def add( self, items ):
        for item in items:
            self.push( item )
PARENT_DIR = Stack( 0 )


class ActorInfo( xbmcgui.WindowXMLDialog ):
    def __init__( self, *args, **kwargs ):
        self.tbn_added = False
        self.multiimage_thread = None
        # get configuration: images path and sizes
        self.config = tmdbAPI.configuration()
        # set our person image path
        self.profile_path = self.config[ "base_url" ] + self.config[ "profile_sizes" ][ 2 ]
        # set our movie image path
        self.poster_path  = self.config[ "base_url" ] + self.config[ "poster_sizes" ][ 2 ]

        self.videodb = kwargs.get( "videodb" )
        # set our person name
        self.actor_name = kwargs.get( "actor_name" ) or ""

        # fix name if called from dialogvideoinfo.xml actor and role
        _as_ = " %s " % LangXBMC( 20347 )
        try: actor, role = self.actor_name.split( _as_.encode( "utf-8" ) )
        except:
            try: actor, role = self.actor_name.split( _as_ )
            except:
                _as_ = metautils.re.search( "(.*?)%s(.*?)" % _as_, self.actor_name )
                if _as_: actor, role = _as_.groups()
                else: actor, role = "", ""
        #xbmcgui.Dialog().ok( LangXBMC( 20347 ), actor, role )
        self.actor_name = actor or self.actor_name

        # if not name, show keyboard
        self.actor_search = self.actor_name or metautils.select_actor_from_xbmc( ACTORS )
        # Manque un actor_search = "manual"
        if self.actor_search == "manual":
            self.actor_search = metautils.keyboard()
        self.actor_search = self.actor_search

        # if not again name, call error
        if not self.actor_search:
            raise Exception( "No search person: Canceled..." )

        # search in database
        con, cur = actorsdb.getConnection()
        if self.actor_search.isdigit():
            self.actor = actorsdb.getActor( cur, idTMDB=self.actor_search )
        else:
            self.actor = actorsdb.getActor( cur, strActor=self.actor_search )
        con.close()
        OK = bool( self.actor )

        if not OK:
            # if not actor, select choices
            self.actor = dialogs.select( self )
            OK = bool( self.actor )

        # if not again name, call error
        if not OK:
            raise Exception( "No search person name %r" % self.actor_search )

        self.timeperimage = int( float( ADDON.getSetting( "timeperimage" ) ) )

    def copyThumb( self, tbn2="", ignore_errors=0, force=False ):
        ok = False
        try:
            tbn1 = "".join( TBN.get_thumb( self.actor[ "name" ] ) )
            tbn2 = tbn2 or TBN.BASE_THUMB_PATH + self.actor[ "thumbs" ][ 0 ]
            force = force or ( not xbmcvfs.exists( tbn1 ) )
            if tbn1 and force and xbmcvfs.exists( tbn2 ):
                ok = xbmcvfs.copy( tbn2, tbn1 )
                print "%r xbmcvfs.copy( %r, %r )" % ( ok, tbn2, tbn1 )
        except:
            if not ignore_errors:
                print_exc()
        if ok: globals().update( { "CONTAINER_REFRESH": True } )
        return ok

    def onInit( self ):
        xbmc.executebuiltin( "ClearProperty(actorsselect)" )
        if PARENT_DIR.qsize():
            self.setProperty( "ParentDir", "true" )
        try: self.button_filmo_bio = self.getControl( 5 )
        except: self.button_filmo_bio = None
        self.setContainer()

    def multiimage( self ):
        try:
            self.listitem.setIconImage( self.profile_path + self.multiimages[ 0 ] )
            self.multiimages.rotate( -1 )

            self._stop_multiimage_thread()
            self.multiimage_thread = Timer( self.timeperimage, self.multiimage, () )
            self.multiimage_thread.start()
        except:
            print_exc()

    def _stop_multiimage_thread( self ):
        try: self.multiimage_thread.cancel()
        except: pass

    def setContainer( self, refresh=False ):
        try:
            self.videodb = metautils.getActorPaths( self.actor[ "name" ], ACTORS )
            self.getControl( 8 ).setEnabled( bool( self.videodb ) )

            # actor key: ( "idactor", "id", "name", "biography", "biooutline", "birthday", "deathday", "place_of_birth", "also_known_as", "homepage", "adult", "cachedthumb" )
            # actor.thumbs list: [ cachedUrl, strUrl, strThumb=json_string ]
            # actor.castandcrew list: [ strCast=json_string, strCrew=json_string ]

            self.actor[ "castandcrew" ] = map( metautils.load_db_json_string, self.actor[ "castandcrew" ] )
            try: self.images = metautils.load_db_json_string( self.actor[ "thumbs" ][ 2 ] )
            except: self.images = []
            # Shuffle items in place
            if ADDON.getSetting( "randomize" ) == "true": shuffle( self.images )
            self.multiimages = deque( a[ "file_path" ] for a in self.images )
            try: self.timeperimage = int( ADDON.getSetting( "timeperimage" ) )
            except: self.timeperimage = 10

            listitem = xbmcgui.ListItem( self.actor[ "name" ], "", "DefaultActor.png" )
            for fanart in TBN.get_fanarts( self.actor[ "name" ] ):
                if xbmcvfs.exists( fanart ):
                    listitem.setProperty( "Fanart_Image", fanart )
                    break

            cached_actor_thumb = "special://thumbnails/Actors/" + self.actor[ "name" ] + "/"
            for extra in [ "extrafanart", "extrathumb" ]:
                if xbmcvfs.exists( cached_actor_thumb + extra ):
                    listitem.setProperty( extra, cached_actor_thumb + extra )

            self.tbn_added = False
            if self.actor[ "thumbs" ]:
                icon = self.actor[ "thumbs" ][ 1 ]
                if icon:
                    listitem.setIconImage( self.profile_path + icon )
                    self.tbn_added = True
                    self.copyThumb()

                if ADDON.getSetting( "usemultiimage" ) == "true" and len( self.multiimages ) > 1:
                    # active multiimage thread
                    self.multiimage_thread = Timer( self.timeperimage, self.multiimage, () )
                    self.multiimage_thread.start()
                    self.tbn_added = True

            if not self.tbn_added:
                cachedthumb = "".join( TBN.get_thumb( self.actor[ "name" ] ) )
                if xbmcvfs.exists( cachedthumb ): listitem.setIconImage( cachedthumb )

            #
            self.actor[ "biography" ] = metautils.clean_bio( self.actor[ "biography" ] or "" )
            listitem.setInfo( "video", { "title": self.actor[ "name" ], "plot": self.actor[ "biography" ] } )
            listitem = common.setActorProperties( listitem, self.actor )

            self.listitem = listitem
            self.clearList()
            self.addItem( self.listitem )
            self.getControl( 50 ).setVisible( 0 )

            self.setContainer150()
            self.setContainer250()

        except:
            print_exc()
            self._close_dialog()
        xbmc.executebuiltin( "ClearProperty(actorsselect)" )

    def setContainer150( self ):
        TotalMovies = 0
        try:
            if self.button_filmo_bio:
                self.getControl( 150 ).setVisible( 0 )

            pretty_movie = {}
            non_dated = {}
            movies_library = metautils.get_movies_library()
            for movie in self.actor[ "castandcrew" ][ 0 ] + self.actor[ "castandcrew" ][ 1 ]:
                # set our year
                year = str( movie[ "release_date" ] or "0" )[ :4 ]
                # get current dict
                curdict = ( pretty_movie, non_dated )[ year == "0" ]
                # set our listitem
                li = curdict.get( movie[ "id" ] ) or xbmcgui.ListItem( movie[ "title" ], "", "DefaultVideo.png" )
                # set our icon
                if movie[ "poster_path" ]:
                    li.setIconImage( self.poster_path + movie[ "poster_path" ] )
                # set our movie id
                li.setProperty( "id", str( movie[ "id" ] ) )
                # set our roles
                if movie.get( "character" ):
                    role = li.getProperty( "role" ).split( " / " ) + [ movie[ "character" ] ]
                    li.setProperty( "role", " / ".join( role ).strip( " / " ) )
                # set our job
                if movie.get( "job" ):
                    job = li.getProperty( "job" ).split( " / " ) + [ movie[ "job" ] ]
                    li.setProperty( "job", " / ".join( job ).strip( " / " ) )
                # set our release date
                li.setProperty( "releasedate", movie[ "release_date" ] or "" )
                # set our info
                year2 = li.getProperty( "year" )
                if year2: year = year2
                li.setProperty( "year", year )
                li.setInfo( "video", { "title": movie[ "title" ], "originaltitle": ( movie[ "original_title" ] or movie[ "title" ] ).strip(), "year": int( year ) } )
                # set our local movie properties
                LibraryHasMovie = metautils.library_has_movie( movies_library, movie[ "title" ], movie[ "original_title" ], year )
                if LibraryHasMovie:
                    li.setProperty( "LibraryHasMovie", "1" )
                    li.setProperty( "movieid", str( LibraryHasMovie.get( "movieid" ) or "" ) )
                    li.setProperty( "PlayCount", str( LibraryHasMovie.get( "playcount" ) or "0" ) )
                    li.setProperty( "file", LibraryHasMovie.get( "file" ) or "" )

                curdict[ movie[ "id" ] ] = li

            ksort = lambda i: i.getProperty( "releasedate" )
            listitems  = sorted( pretty_movie.values(), key=ksort, reverse=True )
            listitems += sorted( non_dated.values(), key=ksort )

            self.getControl( 150 ).reset()
            self.getControl( 150 ).addItems( listitems )
            TotalMovies = len( listitems )
        except:
            print_exc()
            if self.button_filmo_bio:
                self.button_filmo_bio.setEnabled( 0 )

        self.listitem.setProperty( "TotalMovies",  str( TotalMovies ) )
        if self.button_filmo_bio:
            self.button_filmo_bio.setEnabled( TotalMovies > 0 )
            self.button_filmo_bio.setLabel( Language( 32010 ) )

    def setContainer250( self ):
        try:
            listitems = []
            for img in self.images:
                label = "%ix%i" % ( img[ "width" ], img[ "height" ], )
                li = xbmcgui.ListItem( label, "", self.profile_path + img[ "file_path" ] )
                li.setProperty( "aspect_ratio", "%.2f" % img[ "aspect_ratio" ] )
                listitems.append( li )
            self.getControl( 250 ).reset()
            self.getControl( 250 ).addItems( listitems )
        except:
            print_exc()

    def onFocus( self, controlID ):
        pass

    def getLabelImageSize( self, w, h, to ):
        if   to[ 0 ] == "h": size = "%ix%s" % ( round( int( w ) * int( to[ 1: ] ) / int( h ) ), to[ 1: ] )
        elif to[ 0 ] == "w": size = "%sx%i" % ( to[ 1: ], round( int( h ) * int( to[ 1: ] ) / int( w ) ) )
        else: size = w + "x" + h
        return "%s  (%s)" % ( to.title(), size )

    def onClick( self, controlID ):
        try:
            if controlID == 250:
                icon = xbmc.getInfoLabel( "Container(250).ListItem.Icon" )
                w, h = xbmc.getInfoLabel( "Container(250).ListItem.Label" ).split( "x" )
                choices = [ self.getLabelImageSize( w, h, to ) for to in self.config[ "profile_sizes" ][ ::-1 ] ] + [ LangXBMC( 21452 ), LangXBMC( 222 ) ]
                selected = xbmcgui.Dialog().select( Language( 32040 ), choices )
                if selected > -1:
                    if choices[ selected ] == LangXBMC( 21452 ):
                        #browse thumb
                        if dialogs.browser( search_name=self.actor_search, type="thumb" ):
                            globals().update( { "CONTAINER_REFRESH": True } )
                            self.setContainer()

                    elif choices[ selected ] != LangXBMC( 222 ):
                        icon = icon.split( "/" )
                        icon[ icon.index( self.config[ "profile_sizes" ][ 2 ] ) ] = self.config[ "profile_sizes" ][ ::-1 ][ selected ]
                        new_icon = tmdbAPI.download( "/".join( icon ), xbmc.translatePath( "special://temp" ) )
                        ok = False
                        if new_icon:
                            ok = self.copyThumb( new_icon, force=True )
                            if not ok:
                                import shutil
                                try: shutil.copy( new_icon, xbmc.translatePath( "".join( TBN.get_thumb( self.actor[ "name" ] ) ) ) )
                                except: pass
                                else: ok = True
                                del shutil
                        if ok:
                            self.tbn_added = False
                            msg = Language( 32041 )
                            globals().update( { "CONTAINER_REFRESH": True } )
                        else:
                            msg = Language( 32042 )
                        xbmcgui.Dialog().ok( xbmc.getInfoLabel( "ListItem.Title" ), msg )

            elif controlID == 150:
                listitem = self.getControl( 150 ).getSelectedItem()
                movie_id = listitem.getProperty( "id" )
                if not movie_id: return
                LibraryHasMovie = listitem.getProperty( "LibraryHasMovie" ) == "1"
                HasMovieJson = xbmcvfs.exists( ADDON.getAddonInfo( "profile" ) + "movies/%s.json" % movie_id )

                listitem.select( 1 )
                buttons = []
                if LibraryHasMovie:
                    buttons.append( LangXBMC( 208 ) )
                if HasMovieJson:
                    buttons.append( Language( 32051 ) )
                buttons += [ LangXBMC( 13346 ), Language( 32050 ) ]

                # show context menu
                selected = dialogs.contextmenu( buttons )
                listitem.select( 0 )

                if selected == 0 and LibraryHasMovie:
                    file = listitem.getProperty( "file" )
                    if file: xbmc.executebuiltin( "PlayMedia(%s)" % file )
                    return

                if LibraryHasMovie:
                    selected -= 1

                if not HasMovieJson:
                    selected += 1

                if selected == 0 and HasMovieJson:
                    # get trailers from movie cache
                    trailers = tmdbAPI.load_movie_info( movie_id ).get( "trailers" ) or [{}]
                    trailers = trailers[ 0 ].get( "youtube" )
                    if trailers:
                        selected = -1
                        if len( trailers ) == 1: selected = 0
                        else: selected = xbmcgui.Dialog().select( "%s [%s]" % ( Language( 32051 ), lang.upper() ), [ "%s (%s)" % ( trailer[ "name" ], trailer[ "size" ] ) for trailer in trailers ] )
                        if selected > -1:
                            url = "plugin://plugin.video.youtube/?action=play_video&videoid=%s" % trailers[ selected ][ "source" ]
                            self._close_dialog()
                            xbmc.executebuiltin( "ClearProperty(script.metadata.actors.isactive)" )
                            xbmc.executebuiltin( 'Dialog.Close(all,true)' )
                            xbmc.Player().play( url, listitem )
                    else:
                        #no trailers found
                        metautils.notification( listitem.getLabel(), Language( 32052 ).encode( "utf-8" ) )

                elif selected == 1:
                    self.movie_info()

                elif selected == 2:
                    import webbrowser
                    url = "http://www.themoviedb.org/movie/%s?language=%s" % ( movie_id, ADDON.getSetting( "language" ).lower() )
                    webbrowser.open( url )
                    del webbrowser

            elif self.button_filmo_bio and controlID == 5:
                # toggle button Filmography/Biography
                if self.button_filmo_bio.getLabel() == LangXBMC( 21887 ):
                    label, visible = Language( 32010 ), 0
                else:
                    label, visible = LangXBMC( 21887 ), 1
                self.button_filmo_bio.setLabel( label )
                self.getControl( 150 ).setVisible( visible )

            elif controlID == 6:
                # refresh button
                actor = dialogs.select( self, True )
                if actor:
                    self.actor = actor
                    self.setContainer( True )

            elif controlID == 8:
                # show user movies acting, tvshows acting, movies directing, discography
                if self.videodb:
                    if len( self.videodb ) == 1:
                        selected = 0
                    else:
                        selected = xbmcgui.Dialog().select( self.actor[ "name" ], [ i[ 0 ] for i in self.videodb ] )

                    if selected > -1:
                        path_db = self.videodb[ selected ][ 1 ]
                        if metautils.LIBRARY_TYPE:
                            command = "Container.Update(%s,replace)" % path_db
                        else:
                            window = ( "Videos", "MusicLibrary" ) [ "musicdb" in path_db ]
                            command = "ActivateWindow(%s,%s,return)" % ( window, path_db )
                        if xbmc.getCondVisibility( "Window.IsVisible(12003)" ):
                            xbmc.executebuiltin( 'Dialog.Close(12003,true)' )
                        self._close_dialog()
                        xbmc.executebuiltin( command )

            elif controlID == 11:
                #  edit profile from site
                if xbmcgui.Dialog().yesno( "themoviedb.org", Language( 32035 ), Language( 32036 ), "", LangXBMC( 222 ), LangXBMC( 21435 ).strip( "- " ) ):
                    import webbrowser
                    webbrowser.open( "http://www.themoviedb.org/person/%i" % self.actor[ "id" ] )
                    del webbrowser

            elif controlID in [ 10, 20 ]:
                #browse fanart or thumb
                type = ( "thumb", "fanart" )[ controlID == 20 ]
                if type == "thumb" and self.getControl( 250 ).size():
                    self.setFocusId( 250 )

                elif dialogs.browser( search_name=self.actor_search, type=type ):
                    globals().update( { "CONTAINER_REFRESH": True } )
                    self.setContainer()

            elif controlID == 25:
                globals().update( { "PARENT_DIR": Stack( 0 ) } )
                # show addon settings
                self._close_dialog()
                ADDON.openSettings()
                from sys import argv
                xbmc.executebuiltin( 'RunScript(%s)' % ",".join( argv ) )
        except:
            print_exc()

    def movie_info( self ):
        try:
            listitem = self.getControl( 150 ).getSelectedItem()
            movieid = listitem.getProperty( "movieid" )
            if not movieid:
                movieid = listitem.getProperty( "id" )
                if movieid: movieid = "idTMDB=" + movieid
            if movieid:
                PARENT_DIR.push( ( "ActorInfo", self.actor_search ) )
                PARENT_DIR.push( ( "MovieInfo", movieid ) )
                self._close_dialog()
            else:
                xbmcgui.Dialog().ok( metautils.ADDON.getAddonInfo( "name" ), "Coming Soon!" )
        except:
            print_exc()

    def onAction( self, action ):
        if action == metautils.ACTION_CONTEXT_MENU and xbmc.getCondVisibility( "Control.HasFocus(150)" ):
            try: self.onClick( 150 )
            except: pass

        elif action == metautils.ACTION_SHOW_INFO and xbmc.getCondVisibility( "Control.HasFocus(150)" ):
            self.movie_info()

        elif action == metautils.ACTION_NAV_BACK:
            self._close_dialog()

        elif action in metautils.CLOSE_DIALOG:
            globals().update( { "PARENT_DIR": Stack( 0 ) } )
            self._close_dialog()

    def _close_dialog( self ):
        self._stop_multiimage_thread()
        if self.tbn_added:
            self.copyThumb( ignore_errors=1 )
        xbmc.executebuiltin( "ClearProperty(actorsselect)" )
        self.close()
        xbmc.sleep( 500 )


class MovieInfo( xbmcgui.WindowXMLDialog ):
    def __init__( self, *args, **kwargs ):
        # get configuration: images path and sizes
        self.config = tmdbAPI.configuration()
        # set our person image path
        self.profile_path = self.config[ "base_url" ] + self.config[ "profile_sizes" ][ 2 ]
        #
        self.movieid = kwargs[ "movieid" ]
        self.allow_refresh = False
        self.getMovieInfo()

    def getMovieInfo( self, refresh=False ):
        try:
            if "idTMDB" in self.movieid:
                self.allow_refresh = True
                movieid = self.movieid.replace( "idTMDB=", "" )
                self.movie = tmdbAPI.load_movie_info( movieid )
                if refresh or not self.movie:
                    xbmc.executebuiltin( 'ActivateWindow(busydialog)' )
                    js, lang = tmdbAPI.get_movie( movieid, ADDON.getSetting( "language" ).lower() )
                    self.movie = tmdbAPI.save_movie_info( js )
                    xbmc.executebuiltin( 'Dialog.Close(busydialog,true)' )
                self.online_info = "http://www.themoviedb.org/movie/%s?language=%s" % ( movieid, ADDON.getSetting( "language" ).lower() )
            else:
                self.movie = metautils.get_library_movie_details( self.movieid )
                self.online_info = ""
            #print self.movie
            #s_json = metautils.json.dumps( details, sort_keys=True, indent=2 )
        except:
            xbmc.executebuiltin( 'Dialog.Close(busydialog,true)' )
            print_exc()
            raise

    def onInit( self ):
        if PARENT_DIR.qsize():
            self.setProperty( "ParentDir", "true" )
        self.setContainer()

    def setContainer( self ):
        try:
            try:
                self.getControl( 6 ).setEnabled( self.allow_refresh )
                self.getControl( 8 ).setEnabled( not self.allow_refresh )
                self.getControl( 10 ).setEnabled( 0 )
            except:
                pass
            #
            listitem = xbmcgui.ListItem( self.movie[ "title" ], "", "DefaultVideo.png", self.movie[ "thumbnail" ], self.movie[ "file" ] )
            if self.movie[ "thumbnail" ]: listitem.setIconImage( self.movie[ "thumbnail" ] ) # fix eden to show icon
            listitem.setProperty( "Fanart_Image", self.movie[ "fanart" ] )
            listitem.setProperty( "country", self.movie[ "country" ] )
            listitem.setProperty( "releasedate", self.movie.get( "releasedate" ) or "" )
            listitem.setProperty( "lastupdated", self.movie.get( "lastupdated" ) or "" )
            listitem.setProperty( "Homepage",    self.movie.get( "homepage" )    or "" )
            listitem.setProperty( "onlineinfo",  self.online_info )
            try: listitem.setProperty( "set", " / ".join( self.movie[ "set" ] ) )
            except: pass
            infoLabels = {
                "title":         self.movie[ "title" ],
                "year":          self.movie[ "year" ],
                "plot":          self.movie[ "plot" ],
                "originaltitle": self.movie[ "originaltitle" ],
                "director":      self.movie[ "director" ],
                "trailer":       self.movie[ "trailer" ],
                "genre":         self.movie[ "genre" ],
                "mpaa":          self.movie[ "mpaa" ],
                "playcount":     self.movie[ "playcount" ],
                "plotoutline":   self.movie[ "plotoutline" ],
                "rating":        self.movie[ "rating" ],
                "duration":      self.movie[ "runtime" ],
                "studio":        self.movie[ "studio" ],
                "tagline":       self.movie[ "tagline" ],
                "top250":        self.movie[ "top250" ],
                "votes":         self.movie[ "votes" ],
                "writer":        self.movie[ "writer" ],
                "lastplayed":    self.movie[ "lastplayed" ],
                "date":          self.movie.get( "date" ) or "",
                }
            if self.movie.get( "trailers" ):
                trailers = ( self.movie[ "trailers" ][ 0 ] or {} ).get( "youtube" )
                if trailers: infoLabels.update( { "trailer": "plugin://plugin.video.youtube/?action=play_video&videoid=%s" % trailers[ 0 ][ "source" ] } )
            listitem.setInfo( "video", infoLabels )
            #
            self.listitem = listitem
            self.clearList()
            self.addItem( self.listitem )
            #
            if hasattr( self.listitem, "addStreamInfo" ):
                self.add_stream_info( self.listitem ) #work only on plugin view
            #
            self.setContainer150()
        except:
            print_exc()
            self._close_dialog()

    def setContainer150( self ):
        # open db
        con, cur = actorsdb.getConnection()
        try:
            #set cast and role
            listitems = []
            for cast in self.movie[ "cast" ]:
                listitem = xbmcgui.ListItem( cast[ "name" ], cast[ "role" ], "DefaultActor.png" )
                cachedthumb = ( cast.get( "thumbnail" ) or "" )
                if cachedthumb: listitem.setIconImage( cachedthumb )
                try:
                    actor = actorsdb.getActor( cur, ustrActor=cast[ "name" ] )
                    bio   = metautils.clean_bio( actor.get( "biography" ) or "" )
                    listitem.setInfo( "video", { "title": actor.get( "name" ) or cast[ "name" ], "plot": bio } )
                    if actor:
                        actor[ "biography" ] = bio
                        listitem = common.setActorProperties( listitem, actor )
                        if not cachedthumb and actor.get( "thumbs" ):
                            if actor[ "thumbs" ][ 1 ]: listitem.setIconImage( self.profile_path + actor[ "thumbs" ][ 1 ] )
                except:
                    print_exc()
                listitems.append( listitem )
            #
            self.getControl( 150 ).reset()
            self.getControl( 150 ).addItems( listitems )
        except:
            print_exc()
        #close db
        con.close()

    def add_stream_info( self, listitem ):
        """ addStreamInfo(type, values) -- Add a stream with details.

            type              : string - type of stream(video/audio/subtitle).
            values            : dictionary - pairs of { label: value }.

            Video Values:
                codec         : string (h264)
                aspect        : float (1.78)
                width         : integer (1280)
                height        : integer (720)
                duration      : integer (seconds)

            Audio Values:
                codec         : string (dts)
                language      : string (en)
                channels      : integer (2)

            Subtitle Values:
                language      : string (en)

            example:
              - self.list.getSelectedItem().addStreamInfo('video', { 'Codec': 'h264', 'Width' : 1280 })
        """
        try:
            for key, value in self.movie[ "streamdetails" ].items():
                try: listitem.addStreamInfo( key, value[ 0 ] )
                except: print_exc()
        except TypeError: pass
        except:
            print_exc()
        return listitem

    def onFocus( self, controlID ):
        pass

    def onClick( self, controlID ):
        try:
            if controlID == 150:
                actor = xbmc.getInfoLabel( "Container(150).ListItem.Label" )
                if actor:
                    PARENT_DIR.push( ( "MovieInfo", self.movieid ) )
                    PARENT_DIR.push( ( "ActorInfo", actor ) )
                    self._close_dialog()

            elif controlID == 6:
                # refresh non local movie
                self.clearList()
                self.getControl( 150 ).reset()
                self.getMovieInfo( True )
                self.setContainer()
        except:
            print_exc()

    def onAction( self, action ):
        if action == metautils.ACTION_NAV_BACK:
            self._close_dialog()

        elif action in metautils.CLOSE_DIALOG:
            globals().update( { "PARENT_DIR": Stack( 0 ) } )
            self._close_dialog()

    def _close_dialog( self ):
        self.close()
        xbmc.sleep( 500 )


def Main( actor_name="" ):
    PARENT_DIR.push( ( "ActorInfo", actor_name ) )
    try:
        while PARENT_DIR.qsize():
            pardir = PARENT_DIR.pop()
            w = None
            if pardir[ 0 ] == "ActorInfo":
                try: w = ActorInfo( "script-Actors-DialogInfo.xml", metautils.ADDON_DIR, actor_name=pardir[ 1 ] )
                except: print_exc()

            elif pardir[ 0 ] == "MovieInfo":
                try: w = MovieInfo( "script-Actors-DialogVideoInfo.xml", metautils.ADDON_DIR, movieid=pardir[ 1 ] )
                except: print_exc()

            else: print pardir

            if w is not None:
                try: w.doModal()
                except: print_exc()
            del w
    except Queue.Empty: pass
    except: print_exc()

    if CONTAINER_REFRESH:
        if xbmc.getCondVisibility( "![Window.IsVisible(movieinformation) | Window.IsVisible(musicinformation)]" ):
            xbmc.executebuiltin( "ClearProperty(script.metadata.actors.isactive)" )
            xbmc.executebuiltin( 'Container.Refresh' )

    if dialogs.RELOAD_ACTORS_BACKEND or CONTAINER_REFRESH:
        # send message to backend for reload actors
        xbmcgui.Window( 10025 ).setProperty( "reload.actors.backend", "1" )
        # refresh home cache
        from os.path import join
        xbmc.executebuiltin( "RunScript(%s)" % join( metautils.ADDON_DIR, "resources", "lib", "service.py" ) )


if __name__=="__main__":
    Main()
