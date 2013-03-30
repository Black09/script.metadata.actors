
import os
from traceback import print_exc

try:
    from xbmc import translatePath
    ACTORS_DB = translatePath( "special://Database/Actors1.db" )
except:
    ACTORS_DB = 'Actors1.db'

try:
    import json
    # test json
    json.loads( "[null]" )
except:
    import simplejson as json

# http://docs.python.org/library/sqlite3.html
try:
    import sqlite3
    sql_connect = sqlite3.connect
except:
    raise
    #try: import sqlite
    #except:
    #    try: from pysqlite2 import dbapi2 as sqlite
    #    except: sqlite = None
    #def sql_connect( *args, **kwargs ):
    #    return sqlite.connect( *args )


def dumps( l ):
    if not bool( l ): return None
    return json.dumps( l, sort_keys=True )


def createTables( c, idVersion=1 ):
    # http://docs.python.org/library/sqlite3.html#sqlite3.Cursor.executescript
    # Create tables
    many = None
    try:
        many = c.executescript(
            """
            CREATE TABLE version ( idVersion integer, iCompressCount integer );

            CREATE TABLE actors (
            idActor integer primary key,
            idTMDB integer,
            strActor text,
            strBio text,
            strBioOutLine text,
            strBirthday text,
            strDeathday text,
            strPlaceOfBirth text,
            strAlsoKnownAs text,
            strHomepage text,
            strAdult text,
            cachedThumb text );
            CREATE UNIQUE INDEX ix_actors_1 ON actors ( idActor );

            CREATE TABLE thumbs ( idActor integer, cachedUrl text, strUrl text, strThumb text );
            CREATE UNIQUE INDEX ix_thumbs_1 ON thumbs ( idActor );

            CREATE TABLE castandcrew ( idActor integer, strCast text, strCrew text );
            CREATE UNIQUE INDEX ix_castandcrew_1 ON castandcrew ( idActor );

            INSERT INTO version ( idVersion, iCompressCount ) values( %i, 0 );
            """ % idVersion
            )
    except:
        print_exc()
    return many


def getVersion( c ):
    version = 0
    try: version = c.execute( "SELECT idVersion FROM version" ).fetchone()[ 0 ]
    except: pass
    return version


def getConnection():
    con = sql_connect( ACTORS_DB, check_same_thread=False )
    cur = con #.cursor()

    if not getVersion( cur ):
        if createTables( cur ):
            con.commit()
        else:
            con.rollback()

    return con, cur


def addActor( c, actor, castandcrew=([], []), thumbs=('', '', []), update_id=-1 ):
    ok = 0
    idActor = -1
    try:
        if update_id >= 0: idTMDB = update_id
        else: idTMDB = int( actor[ 0 ] )
        # first check if exists update
        idActor = c.execute( "SELECT idActor FROM actors WHERE idTMDB=%i" % idTMDB ).fetchone()
        if idActor:
            idActor = idActor[ 0 ]
            where = " WHERE idActor=%i" % idActor
            ok += c.execute( "UPDATE actors SET idTMDB=?, strActor=?, strBio=?, strBioOutLine=?, strBirthday=?, strDeathday=?, strPlaceOfBirth=?, strAlsoKnownAs=?, strHomepage=?, strAdult=?, cachedThumb=?" + where, actor ).rowcount
            ok += c.execute( "UPDATE thumbs SET cachedUrl=?, strUrl=?, strThumb=?" + where, ( thumbs[ 0 ], thumbs[ 1 ], dumps( thumbs[ 2 ] ) ) ).rowcount
            ok += c.execute( "UPDATE castandcrew SET strCast=?, strCrew=?" + where, ( dumps( castandcrew[ 0 ] ), dumps( castandcrew[ 1 ] ) ) ).rowcount

            if ( ok < 3 ):
                ok = 0
                idActor = -1
                for table in [ "actors", "thumbs", "castandcrew" ]:
                    c.execute( "DELETE FROM " + table + where )

        if ( not ok ):
            # Insert a row of data
            ok += c.execute( "INSERT INTO actors VALUES ( NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? )", actor ).rowcount
            idActor = c.execute( "SELECT idActor FROM actors WHERE idTMDB=%i" % idTMDB ).fetchone()[ 0 ]
            ok += c.execute( "INSERT INTO thumbs VALUES ( ?, ?, ?, ? )",   ( idActor, thumbs[ 0 ], thumbs[ 1 ], dumps( thumbs[ 2 ] ) ) ).rowcount
            ok += c.execute( "INSERT INTO castandcrew VALUES ( ?, ?, ? )", ( idActor, dumps( castandcrew[ 0 ] ), dumps( castandcrew[ 1 ] ) ) ).rowcount
    except:
        print_exc()
    return ( ok == 3 ), idActor


def getActor( c, **kwargs ):
    actor = {}
    where = ""
    if kwargs.get( "idTMDB" ):      where, like = "WHERE idTMDB=?", kwargs[ "idTMDB" ]
    elif kwargs.get( "idActor" ):   where, like = "WHERE idActor=?", kwargs[ "idActor" ]
    elif kwargs.get( "ustrActor" ): where, like = "WHERE strActor=?", kwargs[ "ustrActor" ]
    elif kwargs.get( "strActor" ):  where, like = "WHERE strActor=?", unicode( kwargs[ "strActor" ], 'utf-8', errors='ignore' )
    if where:
        actor = dict( zip(
            ( "idactor", "id", "name", "biography", "biooutline", "birthday", "deathday", "place_of_birth", "also_known_as", "homepage", "adult", "cachedthumb" ),
            list( c.execute( "SELECT * FROM actors " + where, (like,) ).fetchone() or () ) ) )
        if actor:
            where = "WHERE idActor=%i" % actor[ "idactor" ]
            actor[ "thumbs" ] = c.execute( "SELECT cachedUrl, strUrl, strThumb FROM thumbs " + where ).fetchone() or ( '', '', '[]' )
            actor[ "castandcrew" ] = c.execute( "SELECT strCast, strCrew FROM castandcrew "  + where ).fetchone() or ( '[]', '[]' )

    return actor


def save_actor( js, profile_path="", update_id=-1, TBN=None ):
    actor = {}
    idActor = -1
    con, cur = getConnection()
    try:
        cachedThumb = None #if TBN: TBN.get_thumb( js[ "name" ] )[ 1 ]
        cachedUrl = None
        if TBN and js[ "profile_path" ]:
            cachedUrl = TBN.get_cached_url_thumb( profile_path + js[ "profile_path" ] )[ 1 ]

        bio_out_line = None
        # save json object
        actor       = ( js[ "id" ], js[ "name" ], js[ "biography" ], bio_out_line, js[ "birthday" ], js[ "deathday" ], js[ "place_of_birth" ], ' / '.join( js[ "also_known_as" ] ), js[ "homepage" ], str( js[ "adult" ] ), cachedThumb )
        thumbs      = ( cachedUrl, js[ "profile_path" ], js[ "profiles" ] )
        castandcrew = ( js[ "cast" ], js[ "crew" ] )

        ok, idActor = addActor( cur, actor, castandcrew, thumbs, update_id )
        # Save (commit) the changes
        if ok: con.commit()
        else: con.rollback()
        #
        if idActor > -1:
            actor = getActor( cur, idActor=idActor )
    except:
        print_exc()
    con.close()
    return actor


def get_actors_for_backend( xbmc=None ):
    con, cur = getConnection()
    actors = {}
    if xbmc is None:
        try: actors = dict( [ ( actor[ 2 ], actor ) for actor in con.execute( "SELECT * FROM actors" ) ] )
        except: print_exc()
    else:
        try:
            cast = unicode( xbmc.getInfoLabel( "ListItem.Cast" ), 'utf-8', errors='ignore' ).split( "\n" )
            castandrole = unicode( xbmc.getInfoLabel( "ListItem.CastAndRole" ), 'utf-8', errors='ignore' ).split( "\n" )
            sql = "SELECT * FROM actors WHERE strActor IN (%s)" % ", ".join( [ "?" ] * len( cast ) )
            for actor in con.execute( sql, tuple( cast ) ):
                i = cast.index( actor[ 2 ] )
                actors[ castandrole[ i ] ] = actor
        except:
            print_exc()
    con.close()
    return actors

#print json.dumps( get_actors_for_backend(), sort_keys=True, indent=2 )
