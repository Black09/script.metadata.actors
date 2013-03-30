
import os
import sys
import xbmc
from traceback import print_exc

xbmc.executebuiltin( "SetProperty(script.metadata.actors.isactive,1)" )

try:
    args = ",".join( sys.argv[ 1: ] )
    if "backend" in args.lower() or "borntoday" in args.lower():
        from xbmcaddon import Addon
        ADDON_DIR = Addon( "script.metadata.actors" ).getAddonInfo( "path" )
        script = ( "borntoday.py", "backend.py" )[ "backend" in args.lower() ]
        xbmc.executebuiltin( "RunScript(%s,%s)" % ( os.path.join( ADDON_DIR, "resources", "lib", script ), args ) )

    elif "homepage=" in args.lower():
        import webbrowser
        webbrowser.open( args.replace( "homepage=", "" ) )

    elif "urlinfo=" in args.lower():
        # show user movies acting, tvshows acting, movies directing, discography
        urlinfo = eval( args.replace( "urlinfo=", "" ) )
        name = urlinfo[ 0 ]
        urlinfo = urlinfo[ 1: ]
        if urlinfo:
            import xbmcgui
            selected = xbmcgui.Dialog().select( name, [ i[ 0 ] for i in urlinfo ] )

            if selected > -1:   
                path_db = urlinfo[ selected ][ 1 ]
                if path_db.startswith( "http" ):
                    import webbrowser
                    webbrowser.open( path_db )
                else:
                    from resources.lib.metautils import LIBRARY_TYPE
                    if LIBRARY_TYPE:
                        command = "Container.Update(%s,replace)" % path_db
                    else:
                        window = ( "Videos", "MusicLibrary" ) [ "musicdb" in path_db ]
                        command = "ActivateWindow(%s,%s,return)" % ( window, path_db )
                    xbmc.executebuiltin( command )

    else:
        from resources.lib.dialoginfo import Main
        Main( args )
except:
    print_exc()

xbmc.executebuiltin( "ClearProperty(script.metadata.actors.isactive)" )
