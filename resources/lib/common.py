import metautils
import actorsdb

# constants
ADDON    = metautils.ADDON
Language = metautils.Language  # ADDON strings
LangXBMC = metautils.LangXBMC  # XBMC strings

showlabeladult = int( ADDON.getSetting( "showlabeladult" ) )
bdayformat = ( "datelong", "dateshort" )[ int( ADDON.getSetting( "datelongshort" ) ) ]
dateformat = ( "long", "short" )[ ADDON.getSetting( "fulldatelong" ) == "false" ]

BIRTH_MONTHDAY = metautils.datetime.datetime.today().strftime( "%m-%d" )

def setActorProperties( listitem, actor ):
    birthday = actor.get( "birthday" ) or ""
    if birthday and BIRTH_MONTHDAY in str( birthday ):
        listitem.setProperty( "HappyBirthday", "true" )

    listitem.setProperty( "Biography",    actor[ "biography" ] )
    listitem.setProperty( "Biooutline",   actor[ "biooutline" ] or "" )
    listitem.setProperty( "Homepage",     actor[ "homepage" ]   or "" )
    listitem.setProperty( "PlaceOfBirth", actor[ "place_of_birth" ] or "" )
    listitem.setProperty( "AlsoKnownAs",  actor[ "also_known_as" ]  or "" )

    if showlabeladult:
        adult = LangXBMC( ( 106, 107 )[ str( actor[ "adult" ] ).lower() == "true" ] )
        if showlabeladult == 2 and adult == LangXBMC( 106 ): adult = ""
        listitem.setProperty( "Adult", adult )

    birthday = metautils.get_user_date_format( birthday, bdayformat )
    deathday = metautils.get_user_date_format( ( actor[ "deathday" ] or "" ), bdayformat )
    listitem.setProperty( "Birthday",     unicode( metautils.translate_date( birthday, dateformat ) ) )
    listitem.setProperty( "Deathday",     unicode( metautils.translate_date( deathday, dateformat ) ) )

    actuel_age, dead_age, dead_since = metautils.get_ages( actor[ "birthday" ], actor[ "deathday" ] )
    listitem.setProperty( "Age",          actuel_age )
    listitem.setProperty( "Deathage",     dead_age )
    listitem.setProperty( "AgeLong",      "" )
    listitem.setProperty( "DeathageLong", "" )
    if actuel_age: listitem.setProperty( "AgeLong",      Language( 32020 ) % actuel_age )
    if dead_since: listitem.setProperty( "DeathageLong", Language( 32021 ) % dead_since )
    elif dead_age: listitem.setProperty( "DeathageLong", Language( 32020 ) % dead_age )

    return listitem