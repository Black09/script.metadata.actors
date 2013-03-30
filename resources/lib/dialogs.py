
# Modules general
import os
import re
import sys
import time
import urllib
from traceback import print_exc


# Modules XBMC
import xbmc
import xbmcgui
import xbmcvfs
from xbmcaddon import Addon

# Require PIL for FLIP
PIL_Image = None
try: import PIL.Image as PIL_Image
except: print_exc()

# Modules Custom
import metautils
import googleAPI
import actorsdb
import tmdbAPI


# constants
ADDON      = metautils.ADDON
Language   = metautils.Language  # ADDON strings
LangXBMC   = metautils.LangXBMC  # XBMC strings
TBN        = metautils.Thumbnails()
RELOAD_ACTORS_BACKEND = False

TEMP_DIR = xbmc.translatePath( "%scache/" % metautils.ADDON_DATA )
metautils.xbmcvfs_makedirs( TEMP_DIR )

DIALOG_PROGRESS = xbmcgui.DialogProgress()

html_to_xbmc = {
    "<b>":    "[B]",
    "</b>":   "[/B]",
    "<i>":    "[I]",
    "</i>":   "[/I]",
    "&amp;":  "&",
    "&quot;": '"',
    "&#39;":  "'"
    }

def _html_to_xbmc( s ):
    # Replace html formatting to xbmc formatting
    return re.sub( '(%s)' % '|'.join( html_to_xbmc ), lambda m: html_to_xbmc.get( m.group( 1 ), "" ), s )


def _unicode( text, encoding="utf-8" ):
    try: text = unicode( text, encoding )
    except: pass
    return text


def get_browse_dialog( default="", heading="", dlg_type=3, shares="files", mask="", use_thumbs=False, treat_as_folder=False ):
    """ shows a browse dialog and returns a value
        - 0 : ShowAndGetDirectory
        - 1 : ShowAndGetFile
        - 2 : ShowAndGetImage
        - 3 : ShowAndGetWriteableDirectory
    """
    dialog = xbmcgui.Dialog()
    value = dialog.browse( dlg_type, heading, shares, mask, use_thumbs, treat_as_folder, default )
    return value


def _delete_files( files ):
    not_deleted = set()
    for dl in files:
        try:
            xbmcvfs.delete( dl )
            if xbmcvfs.exists( dl ):
                os.remove( dl )
        except:
            print_exc()
        if not xbmcvfs.exists( dl ):
            print "OK, FileDelete(%r)" % dl
        else:
            print "ERROR, FileDelete(%r)" % dl
            not_deleted.add( dl )
    return not_deleted


class Browser( xbmcgui.WindowXMLDialog ):
    # constants
    CONTROL_LIST_450      = 450 # Directory list
    CONTROL_LIST_451      = 451 # List of available thumbnails
    CONTROL_HEADING       = 411 # Heading label
    CONTROL_LABEL_PATH    = 412 # label Path of the selected item
    CONTROL_BUTTON_OK     = 413 # OK button
    CONTROL_BUTTON_CANCEL = 414 # Cancel button
    CONTROL_BUTTON_CREATE = 415 # Create folder
    CONTROL_RADIOBUTTON   = 416 # Flip Image horizontally

    def __init__( self, *args, **kwargs ):
        self.search_name  = kwargs.get( "search_name" ) or "Tatjana Simic"
        self.heading      = kwargs.get( "heading", "Google Images: " ) + self.search_name
        self.thumb_type   = kwargs.get( "type" ) or "fanart"
        self.listitems    = []
        self.delete_files = set()
        self.select_all   = False
        self.actor_update = False

        self.default_icon = ( "DefaultActor.png", "DefaultPicture.png" )[ self.thumb_type == "fanart" ]
        self.get_images()

    def get_images( self ):
        xbmc.executebuiltin( 'ActivateWindow(busydialog)' )
        try:
            #googleAPI
            images = googleAPI.getImages( q=self.search_name )#+" wallpaper" )
            indexItem = 1
            images = sorted( images, key=lambda i: int( i.get( "width" ) or 0 ), reverse=True )
            for image in images:
                #for img in image: #if yield, use this...
                img = image
                try:
                    if self.thumb_type == "fanart" and int( img[ "width" ] ) <= int( img[ "height" ] ): continue
                    elif self.thumb_type == "thumb" and int( img[ "height" ] ) <= int( img[ "width" ] ): continue
                    # set listitem
                    label = "[%sx%s] %s" % ( img[ "width" ], img[ "height" ], _html_to_xbmc( img[ "title" ] ) )
                    listitem = xbmcgui.ListItem( label, img[ "unescapedUrl" ], img[ "tbUrl" ] )
                    listitem.setProperty( "indexItem", str( indexItem ) )
                    indexItem +=1
                    # add listitem
                    self.listitems.append( listitem )
                except:
                    print_exc()
        except:
            print_exc()
        xbmc.executebuiltin( 'Dialog.Close(busydialog,true)' )

    def get_current_thumb( self ):
        if self.thumb_type == "thumb":
            icon = "".join( TBN.get_thumb( self.search_name ) )
        else:
            icon = TBN.get_fanarts( self.search_name )[ 0 ]
        return icon

    def onInit( self ):
        try:
            # set controls label
            self.getControl( self.CONTROL_HEADING ).setLabel( self.heading )
            label = ( Language( 32121 ), Language( 32131 ) )[ self.thumb_type == "thumb" ]
            self.getControl( self.CONTROL_LABEL_PATH ).setLabel( label ) #"Select one %s or more for extra%s"
            #self.getControl( self.CONTROL_RADIOBUTTON ).setLabel( LangXBMC( 13206 ) )#"Overwrite"
            flip = ( self.thumb_type == "fanart" ) and PIL_Image is not None #xbmc.getCondVisibility( "System.HasAddon(script.module.pil)" )
            self.getControl( self.CONTROL_RADIOBUTTON ).setEnabled( flip )
            self.getControl( self.CONTROL_BUTTON_CREATE ).setLabel( LangXBMC( 188 ) )#"Select All"

            # get control list
            self.control_list = self.getControl( self.CONTROL_LIST_450 )
            self.control_list.reset()

            # add listitem current thumb or current fanart
            icon = self.get_current_thumb()
            if not xbmcvfs.exists( icon ):
                icon = self.default_icon
            label = ( LangXBMC( 20440 ), LangXBMC( 20016 ) )[ self.thumb_type == "thumb" ]
            listitem = xbmcgui.ListItem( label, "current", self.default_icon, xbmc.translatePath( icon ) )
            self.control_list.addItem( listitem )

            # add listitems
            self.control_list.addItems( self.listitems )

            # add listitem browse
            self.control_list.addItem( xbmcgui.ListItem( LangXBMC( 20153 ), "browse", "DefaultFolder.png" ) )
            self.setFocus( self.control_list )

            # desable container 451
            try: self.getControl( self.CONTROL_LIST_451 ).setEnabled( 0 )
            except: pass
            try: self.getControl( self.CONTROL_LIST_451 ).setVisible( 0 )
            except: pass
        except:
            print_exc()

    def onFocus( self, controlID ):
        pass

    def onClick( self, controlID ):
        try:
            if controlID == self.CONTROL_LIST_450:
                listitem = self.control_list.getSelectedItem()
                l2 = listitem.getLabel2()
                if l2 == "browse":
                    heading = ( LangXBMC( 20019 ), LangXBMC( 20437 ) )[ self.thumb_type == "fanart" ]
                    ipath = xbmc.translatePath( get_browse_dialog( heading=heading, dlg_type=2 ) )
                    if ipath and xbmcvfs.exists( ipath ):
                        listitem = self.control_list.getListItem( 0 )
                        listitem.setThumbnailImage( self.default_icon )
                        dpath = self.get_current_thumb()
                        OK = xbmcvfs.copy( ipath, dpath )
                        print  "%s, FileCopy(%s,%s)" % ( repr( OK ), ipath, dpath )
                        if xbmcvfs.exists( dpath ):
                            if self.getControl( self.CONTROL_RADIOBUTTON ).isSelected():
                                dpath = metautils.flip_fanart( dpath, PIL_Image, ADDON.getSetting( "flipquality" ) )
                            listitem.setThumbnailImage( dpath )
                            self.actor_update = True

                elif l2 == "current":
                    listitem.select( True )
                    icon = self.get_current_thumb()
                    ipath = icon.split( "userdata" )[ -1 ].replace( "\\", "/" ).strip( "/" )
                    if icon and xbmcgui.Dialog().yesno( LangXBMC( 122 ), LangXBMC( 125 ), ipath ):
                        #try: os.remove( xbmc.translatePath( icon ) )
                        #except: print_exc()
                        #else:
                        xbmcvfs.delete( xbmc.translatePath( icon ) )
                        if not xbmcvfs.exists( icon ):
                            listitem.setThumbnailImage( self.default_icon )
                    listitem.select( False )

                else:
                    listitem.select( not listitem.isSelected() )

            elif controlID == self.CONTROL_BUTTON_CREATE:
                self.select_all = not self.select_all
                for listitem in self.listitems:
                    listitem.select( self.select_all )

            elif controlID == self.CONTROL_BUTTON_CANCEL:
                self._close_dialog()

            elif controlID == self.CONTROL_BUTTON_OK:
                self._download()

        except:
            print_exc()

    def _download( self ):
        try:
            selected = [ l for l in self.listitems if l.isSelected() ]
            t_selected, t_movies = len( selected ), len( self.listitems )
            if selected and xbmcgui.Dialog().yesno( self.heading, Language( 32122 ), Language( 32123 ) % ( t_selected, t_movies ), Language( 32124 ) ):
                is_cached_thumb = False
                if t_selected > 1:
                    # if multi download to user folder
                    heading = Language( 32126 ) + ( Language( 32127 ), Language( 32128 ) )[ self.thumb_type == "thumb" ]
                    overwrite = xbmcgui.Dialog().yesno( Language( 32135 ), Language( 32136 ) )
                    # make cached actor thumb
                    cached_actor_thumb = "special://thumbnails/Actors/" + self.search_name + "/extra" + self.thumb_type
                    metautils.xbmcvfs_makedirs( cached_actor_thumb )
                    dpath = xbmc.translatePath( cached_actor_thumb )
                    #print repr( dpath )
                else:
                    # otherwise, download to cached thumb
                    overwrite = True
                    is_cached_thumb = True
                    dpath = self.get_current_thumb()
                    cached_actor_thumb = dpath
                    self.control_list.getListItem( 0 ).setThumbnailImage( self.default_icon )

                def _pbhook( numblocks, blocksize, filesize, ratio=1.0 ):
                    try: pct = int( min( ( numblocks * blocksize * 100 ) / filesize, 100 ) * ratio )
                    except: pct = 100
                    DIALOG_PROGRESS.update( pct )
                    if DIALOG_PROGRESS.iscanceled():
                        raise IOError

                DIALOG_PROGRESS.create( self.heading )
                diff = 100.0 / t_selected
                percent = 0

                flipfanart = self.getControl( self.CONTROL_RADIOBUTTON ).isSelected()

                for count, listitem in enumerate( selected ):
                    self.control_list.selectItem( int( listitem.getProperty( "indexItem" ) ) )
                    url = listitem.getLabel2()
                    if is_cached_thumb: dest = TEMP_DIR + os.path.basename( url )
                    else: dest = _unicode( os.path.join( dpath, os.path.basename( url ) ) )
                    percent += diff
                    line1 = Language( 32125 ) % ( count+1, t_selected, percent )
                    line3 = cached_actor_thumb + "/" + os.path.basename( url )
                    DIALOG_PROGRESS.update( 0, line1, url, line3 )

                    if not overwrite and xbmcvfs.exists( dest ):
                        listitem.select( False )
                        continue
                    # download file
                    try:
                        fp, h = urllib.urlretrieve( url, dest, lambda nb, bs, fs: _pbhook( nb, bs, fs ) )
                        if h[ "Content-Type" ] == "text/html":
                            raise Exception( "bad thumb: %r" % fp )
                    except:
                        self.delete_files.add( dest )
                        dest = None
                        print_exc()
                    listitem.select( False )
                    if DIALOG_PROGRESS.iscanceled():
                        break
                    #flip source
                    if dest and flipfanart:
                        dest = metautils.flip_fanart( dest, PIL_Image, ADDON.getSetting( "flipquality" ) )

                    if is_cached_thumb and dest:
                        self.delete_files.add( dest )
                        OK = xbmcvfs.copy( dest, dpath )
                        print "%s, FileCopy(%s,%s)" %( repr( OK ), dest, dpath )
                        if xbmcvfs.exists( dpath ):
                            listitem = self.control_list.getListItem( 0 )
                            listitem.setThumbnailImage( dpath )
                            self.actor_update = True

            self.delete_files = _delete_files( self.delete_files )
        except:
            print_exc()
        if xbmc.getCondVisibility( "Window.IsVisible(progressdialog)" ):
            xbmc.executebuiltin( "Dialog.Close(progressdialog)" )
        #try: DIALOG_PROGRESS.close()
        #except: pass
        self.setFocusId( self.CONTROL_BUTTON_CANCEL )

    def onAction( self, action ):
        if action in metautils.CLOSE_SUB_DIALOG:
            self._close_dialog()

    def _close_dialog( self ):
        self.delete_files = _delete_files( self.delete_files )
        self.close()
        xbmc.sleep( 500 )


class DialogContextMenu( xbmcgui.WindowXMLDialog ):
    CONTROLS_BUTTON = range( 1001, 1012 )
    BUTTON_START = 1001
    BUTTON_END   = 1012

    def __init__( self, *args, **kwargs ):
        self.buttons  = kwargs[ "buttons" ]
        self.selected = -1
        self.doModal()

    def onInit( self ):
        try:
            for count, button in enumerate( self.buttons ):
                try:
                    self.getControl( self.BUTTON_START + count ).setLabel( button )
                    self.getControl( self.BUTTON_START + count ).setVisible( True )
                except:
                    pass
            self.setFocusId( self.BUTTON_START )

            for control in range( self.BUTTON_START + count + 1, self.BUTTON_END ):
                try: self.getControl( control ).setVisible( False )
                except: pass
        except:
            print_exc()

    def onFocus( self, controlID ):
        pass

    def onClick( self, controlID ):
        try:
            self.selected = controlID - self.BUTTON_START
            if self.selected < 0: self.selected = -1
        except:
            self.selected = -1
            print_exc()
        self._close_dialog()

    def onAction( self, action ):
        if action in metautils.CLOSE_SUB_DIALOG:
            self.selected = -1
            self._close_dialog()

    def _close_dialog( self ):
        self.close()
        xbmc.sleep( 300 )


class DialogSelect( xbmcgui.WindowXMLDialog ):
    def __init__( self, *args, **kwargs ):
        self.actor = {}
        self.add_plus = False
        self.main = kwargs.get( "main" )
        self.listing = kwargs.get( "listing" ) or []
        self.profile_path = self.main.config[ "base_url" ] + self.main.config[ "profile_sizes" ][ 2 ]

        self.refresh = kwargs[ "refresh" ]
        self.page = 1

        if self.main.actor_search.isdigit():
            self._add_actor( self.main.actor_search )
        else:
            self._search_person()

        # if not refresh and just one item, use this
        if not self.refresh and len( self.listing ) == 1:
            self._add_actor( self.listing[ 0 ][ "id" ] )

    def _search_person( self ):
        #first search person
        xbmc.executebuiltin( 'ActivateWindow(busydialog)' )
        js_search = tmdbAPI.search_person( self.main.actor_search, self.page, ADDON.getSetting( "include_adult" ).lower() )
        xbmc.executebuiltin( 'Dialog.Close(busydialog,true)' )
        self.listing += js_search[ "results" ]
        self.add_plus = js_search[ "results" ] and js_search[ "page" ] < js_search[ "total_pages" ]

    def _add_actor( self, ID ):
        # active busy
        xbmc.executebuiltin( 'ActivateWindow(busydialog)' )
        try:
            json_object = tmdbAPI.full_person_info( ID, ADDON.getSetting( "language" ).lower() )
            self.actor = {}
            if json_object:
                if self.main.actor_name:
                    json_object[ "name" ] = unicode( self.main.actor_name, 'utf-8', errors='ignore' )
                update_id = -1
                if str( self.main.actor.get( "id" ) ).isdigit():
                    update_id = int( self.main.actor[ "id" ] )
                #print repr( str( update_id ) )
                self.actor = actorsdb.save_actor( json_object, self.profile_path, update_id, TBN )
                globals().update( { "RELOAD_ACTORS_BACKEND": True } )
        except:
            print_exc()
        xbmc.executebuiltin( 'Dialog.Close(busydialog,true)' )

    def onInit( self ):
        if bool( self.actor ):
            self._close_dialog( 0 )
        try: self.getControl( 1 ).setLabel( Language( 32034 ) % unicode( self.main.actor_search, 'utf-8', errors='ignore' ) )
        except: self.getControl( 1 ).setLabel( 'Person results for "%s"' % self.main.actor_search )
        try:
            self.control_list = self.getControl( 6 )
            self.getControl( 3 ).setVisible( False )
            self.getControl( 5 ).controlUp( self.control_list )
        except:
            self.control_list = self.getControl( 3 )
            print_exc()
        try: self.getControl( 5 ).setLabel( LangXBMC( 413 ) )
        except: print_exc()

        if self.listing:
            try: self.setContainer()
            except: print_exc()
        elif not bool( self.actor ):
            try: self.onClick( 5 )
            except: print_exc()

    def setContainer( self, selectItem=0 ):
        listitems = []
        showlabeladult = int( ADDON.getSetting( "showlabeladult" ) )
        for actor in self.listing:
            label2 = ""
            if showlabeladult:
                adult = LangXBMC( ( 106, 107 )[ str( actor.get( "adult" ) ).lower() == "true" ] )
                if showlabeladult == 2 and adult == LangXBMC( 106 ): adult = ""
                if adult: label2 = ": ".join( [ Language( 32015 ), adult ] )

            listitem = xbmcgui.ListItem( actor[ "name" ], label2, "DefaultActor.png" )
            listitem.setProperty( "Addon.Summary", label2 )
            if actor[ "profile_path" ]:
                listitem.setIconImage( self.profile_path + actor[ "profile_path" ] )
            listitems.append( listitem )

        if self.add_plus:
            self.add_plus = False
            listitem = xbmcgui.ListItem( LangXBMC( 21452 ), "", "DefaultFolder.png" )
            listitem.setProperty( "nextpage", "true" )
            listitems.append( listitem )

        self.control_list.reset()
        self.control_list.addItems( listitems )
        self.control_list.selectItem( selectItem )
        self.setFocus( self.control_list )
        if not listitems:
            self.setFocusId( 5 )

    def onClick( self, controlID ):
        try:
            if controlID in [ 3, 6 ]:
                selected = self.control_list.getSelectedPosition()
                item = self.control_list.getSelectedItem()
                if item.getProperty( "nextpage" ) == "true":
                    self.page += 1
                    self._search_person()
                    self.setContainer( selected )

                else:
                    if selected > -1:
                        # get id for fetching info
                        try: ID = self.listing[ selected ][ "id" ]
                        except IndexError: pass
                        else:
                            self._add_actor( ID )
                            if bool( self.actor ):
                                self._close_dialog()

            elif controlID == 5:
                # show keyboard
                new_name = metautils.keyboard( self.main.actor_search )
                if new_name and new_name != self.main.actor_search:
                    self.main.actor_search = new_name
                    self.page = 1
                    self.listing = []
                    if self.main.actor_search.isdigit():
                        self._add_actor( self.main.actor_search )
                        if bool( self.actor ):
                            self._close_dialog( 0 )
                            return
                    self._search_person()
                    self.setContainer()
        except:
            print_exc()

    def onFocus( self, controlID ):
        pass

    def onAction( self, action ):
        try:
            if self.getFocusId() == 0:
                if self.listing:
                    self.setFocus( self.control_list )
                else:
                    self.setFocusId( 5 )
        except:
            self.setFocus( self.control_list )
        if action in metautils.CLOSE_SUB_DIALOG:
            self.actor = {}
            self._close_dialog()

    def _close_dialog( self, t=500 ):
        self.close()
        if t: xbmc.sleep( t )



def select( main, refresh=False ):
    xbmc.executebuiltin( "SetProperty(actorsselect,1)" )
    w = DialogSelect( "DialogSelect.xml", metautils.ADDON_DIR, main=main, refresh=refresh )
    if not w.actor:
        w.doModal()
    actor = w.actor
    del w
    xbmc.executebuiltin( "ClearProperty(actorsselect)" )
    return actor


def browser( **kwargs ):
    wb = Browser( "script-Actors-Browser.xml", metautils.ADDON_DIR, **kwargs )
    wb.doModal()
    refresh = wb.actor_update
    del wb
    return refresh


def contextmenu( buttons ):
    cm = DialogContextMenu( "script-Actors-ContextMenu.xml", metautils.ADDON_DIR, buttons=buttons )
    selected = cm.selected
    del cm
    return selected
