
#Modules General
import sys
import time
import threading
from datetime import datetime
from traceback import print_exc

import xbmc
import xbmcgui
import xbmcvfs

# Modules Custom
import metautils
from actorsdb import get_actors_for_backend


STR_AGE_LONG       = metautils.Language( 32020 )
STR_DEAD_SINCE     = metautils.Language( 32021 )
STR_DEATH_AGE_LONG = metautils.Language( 32020 )
TBN                = metautils.Thumbnails()
BIRTH_MONTHDAY     = datetime.today().strftime( "%m-%d" )


class Backend( threading.Thread ):
    def __init__( self ):
        threading.Thread.__init__( self )
        self._stop = False
        self.current_actor = None

    def clearProperties( self ):
        window = xbmcgui.Window( self.windowID )
        for prt in [ "name", "biography", "biooutline", "birthday", "deathday", "placeofbirth", "alsoknownas", "homepage", "adult", "age", "deathage", "agelong", "deathagelong", "fanart", "icon", "extrafanart", "extrathumb", "happybirthday" ][ ::-1  ]:
            window.clearProperty( "current.actor." + prt )

    def setProperties( self ):
        self.clearProperties()
        if not self.current_actor: return
        #( "idactor", "id", "name", "biography", "biooutline", "birthday", "deathday", "placeofbirth", "alsoknownas", "homepage", "adult", "cachedthumb" )
        window = xbmcgui.Window( self.windowID )
        birthday = self.current_actor[ 5 ] or ""
        window.setProperty( "current.actor.name",         self.current_actor[ 2 ]  or "" )
        window.setProperty( "current.actor.biography",    metautils.clean_bio( self.current_actor[ 3 ] or "" ) )
        window.setProperty( "current.actor.biooutline",   self.current_actor[ 4 ]  or "" )
        window.setProperty( "current.actor.birthday",     birthday )
        window.setProperty( "current.actor.deathday",     self.current_actor[ 6 ]  or "" )
        window.setProperty( "current.actor.placeofbirth", self.current_actor[ 7 ]  or "" )
        window.setProperty( "current.actor.alsoknownas",  self.current_actor[ 8 ]  or "" )
        window.setProperty( "current.actor.homepage",     self.current_actor[ 9 ]  or "" )
        window.setProperty( "current.actor.adult",        self.current_actor[ 10 ] or "" )
        if birthday and BIRTH_MONTHDAY in birthday:
            window.setProperty( "current.actor.happybirthday", "true" )
        actuel_age, dead_age, dead_since = metautils.get_ages( birthday, self.current_actor[ 6 ] )
        window.setProperty( "current.actor.age",      actuel_age )
        window.setProperty( "current.actor.deathage", dead_age )
        if actuel_age: window.setProperty( "current.actor.agelong",      STR_AGE_LONG % actuel_age )
        if dead_since: window.setProperty( "current.actor.deathagelong", STR_DEAD_SINCE % dead_since )
        elif dead_age: window.setProperty( "current.actor.deathagelong", STR_DEATH_AGE_LONG % dead_age )

        fanart = TBN.get_fanarts( self.current_actor[ 2 ] )[ 0 ]
        window.setProperty( "current.actor.fanart", fanart )
        icon = "".join( TBN.get_thumb( self.current_actor[ 2 ] ) )
        window.setProperty( "current.actor.icon",   icon )

        # check exist to prevent multiple ERROR: XFILE::CDirectory::GetDirectory - Error getting special://thumbnails/Actors/[ACTOR NAME]/foo/
        cached_actor_thumb = "special://thumbnails/Actors/" + self.current_actor[ 2 ] + "/"
        for extra in [ "extrafanart", "extrathumb" ]:
            #if xbmcvfs.exists( cached_actor_thumb + extra ):
            window.setProperty( "current.actor." + extra, cached_actor_thumb + extra )

    def stop( self ):
        print self.strEnd
        self.clearProperties()
        self._stop = True

    def autoStop( self, hrs=2 ):
        # get auto stop to prevent 24/7 running :D
        # http://forum.xbmc.org/showthread.php?tid=129473&pid=1082117#pid1082117
        return xbmc.getGlobalIdleTime() > ( hrs*60**2 )


class Dialog( Backend ):
    def __init__( self ):
        Backend.__init__( self )
        self.strEnd = "Actor dialog backend ended!"
        self.windowID = 12003
        # get actors from actors1.db
        self.get_actors()
        # start thread
        self.start()

    def get_actors( self ):
        xbmcgui.Window( 10025 ).clearProperty( "reload.actors.backend" )
        self.ACTORS = get_actors_for_backend( xbmc )

    def run( self ):
        try:
            print "Actor dialog backend started!"
            while not self._stop:
                if not xbmc.getCondVisibility( "Window.IsVisible(12003)" ) or self.autoStop(): self.stop()
                if xbmc.getCondVisibility( "![Window.IsVisible(progressdialog) | Window.IsVisible(selectdialog)]" ):
                    if xbmcgui.Window( 10025 ).getProperty( "reload.actors.backend" ) == "1": self.get_actors()
                    temp_actor = self.ACTORS.get( unicode( xbmc.getInfoLabel( "Container(50).ListItem.Label" ), "utf-8" ) )
                    if temp_actor != self.current_actor:
                        self.current_actor = temp_actor
                        self.setProperties()
                time.sleep( .25 )
        except SystemExit:
            print "SystemExit!"
            self.stop()
        except:
            print_exc()
            self.stop()


class Window( Backend ):
    def __init__( self ):
        Backend.__init__( self )
        self.strEnd = "Actor backend ended!"
        self.windowID = 10025
        # get actors from actors1.db
        self.get_actors()
        # start thread
        self.start()

    def get_actors( self ):
        xbmcgui.Window( 10025 ).clearProperty( "reload.actors.backend" )
        self.ACTORS = get_actors_for_backend( None )

    def run( self ):
        try:
            print "Actor backend started!"
            while not self._stop:
                if not xbmc.getCondVisibility( "Window.IsVisible(10025)" ) or self.autoStop(): self.stop()
                if xbmc.getCondVisibility( "Container.Content(Actors) | Container.Content(Directors) | Container.Content(Artists)" ):
                    if xbmcgui.Window( 10025 ).getProperty( "reload.actors.backend" ) == "1": self.get_actors()
                    temp_actor = self.ACTORS.get( unicode( xbmc.getInfoLabel( "ListItem.Label" ), "utf-8" ) )
                    if temp_actor != self.current_actor:
                        self.current_actor = temp_actor
                        self.setProperties()
                else:
                    self.clearProperties()
                    self.current_actor = None
                time.sleep( .25 )
        except SystemExit:
            print "SystemExit!"
            self.stop()
        except:
            print_exc()
            self.stop()



if __name__=="__main__":
    args = ",".join( sys.argv[ 1: ] )
    if "dialogbackend" in args.lower():
        Dialog()
    else:
        Window()
