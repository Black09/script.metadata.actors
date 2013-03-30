
__all__ = [ "htmlentitydecode", "normalize_string", "set_pretty_formatting" ]

import re
import unicodedata
import htmlentitydefs


__doc__ = u"""illegal_characters:
    les caractères codés de &#128; à &#159; - propres à Windows, mais invalides selon les spécifications HTML 4+ et XHTML  .

    Encodés incorrectement comme dans la première colonne de résultat du tableau ci-dessous, ces caractères ne seront pas
    restitués correctement sur d'autres plates-formes que Windows (Linux...), où, au mieux,
    un caractère générique sera affiché (fréquemment un carré vide).

    Ils doivent donc être remplacés par leur équivalent en entités numériques ou entités caractères qui, elles, sont valides et
    seront correctement restituées.

    Ces deux solutions ne sont toutefois pas équivalentes :
        * aucune des entités caractères ne s'affiche dans Netscape 4 ;
        * le résultat obtenu avec les références numériques est indépendant du Character Encoding (ISO-8859-1 ou UTF-8),
        puisque ces codes relèvent du Character Set ISO-10646 utilisé en HTML et en XHTML.

    More :
        * Internal -- convert entity or character reference
        * http://www.trans4mind.com/personal_development/HTMLGuide/specialCharacters.htm
        * http://www.toutimages.com/codes_caracteres.htm
        * http://openweb.eu.org/articles/caracteres_illegaux/
"""


illegal_characters = {
    '#128': '&#8364;', # Euro
    '#129': '', #
    '#130': '&#8218;', # apostrophe anglaise basse
    '#131': '&#402;', # florin, forte musical
    '#132': '&#8222;', # guillemet anglais bas
    '#133': '&#8230;', # points de suspension
    '#134': '&#8224;', # obèle, dague, croix (renvoi de notes de bas de page)
    '#135': '&#8225;', # double croix
    '#136': '&#710;', # accent circonflexe
    '#137': '&#8240;', # pour mille
    '#138': '&#352;', # S majuscule avec caron (accent circonflexe inversé) utilisé en tchèque
    '#139': '&#8249;', # guillemet simple allemand et suisse, parenthèse angulaire ouvrante
    '#140': '&#338;', # Ligature o-e majuscule (absente de la norme ISO-8859-1 pour une raison aberrante…)
    '#141': '', #
    '#142': '&#381;', # Z majuscule avec caron (accent circonflexe inversé) utilisé en tchèque. Présent dans le Character Encoding  ISO-8859-2
    '#143': '', #
    '#144': '', #
    '#145': '&#8216;', # guillemet anglais simple ouvrant(utilisé dans les guillemets doubles)
    '#146': '&#8217;', # guillemet anglais simple fermant(utilisé dans les guillemets doubles)
    '#147': '&#8220;', # guillemets anglais doubles ouvrants
    '#148': '&#8221;', # guillemets anglais doubles fermants
    '#149': '&#8226;', # boulet, utiliser plutôt des listes à puces
    '#150': '&#8211;', # tiret demi-cadratin (incise), voir The Trouble With EM 'n EN
    '#151': '&#8212;', # tiret cadratin (dialogue), voir The Trouble With EM 'n EN
    '#152': '&#732;', # tilde
    '#153': '&#8482;', # marque déposée
    '#154': '&#353;', # s minuscule avec caron (accent circonflexe inversé) utilisé en tchèque
    '#155': '&#8250;', # guillemet simple allemand et suisse, parenthèse angulaire fermante
    '#156': '&#339;', # Ligature o-e minscule (absente de la norme ISO-8859-1 pour une raison aberrante…)
    '#157': '', #
    '#158': '&#382;', # z minuscule avec caron (accent circonflexe inversé) utilisé en tchèque. Présent dans le Character Encoding  ISO-8859-2
    '#159': '&#376;' # Y majuscule avec trema, présent en français dans quelques noms propres (PDF).
    }


def htmlentitydecode( s ):
    # First1 convert numerical illegal_characters (such as &#128;-&#159;)
    def illegal( m ):
        entity = m.group( 1 )
        if entity in illegal_characters.keys():
            return u""+illegal_characters[ entity ] or u'&%s;' % entity#u'&#39;&#168;&#39;'#
        return  u'&%s;' % entity
    t = re.sub( u'&(%s);' % u'|'.join( illegal_characters ), illegal, s )
    t = t.replace( "\t", "&#8212;" ).replace( "&nbsp;", "&#8212;" )

    # First2 convert alpha entities (such as &eacute;)
    def entity2char( m ):
        entity = m.group( 1 )
        if entity in htmlentitydefs.name2codepoint:
            return unichr( htmlentitydefs.name2codepoint[ entity ] )# or '&%s;' % entity
        return u" "  # Unknown entity: We replace with a space.
    t = re.sub( u'&(%s);' % u'|'.join( htmlentitydefs.name2codepoint ), entity2char, t )

    # Then convert numerical entities (such as &#233;)
    t = re.sub( u'&#(\d+);', lambda x: unichr( int( x.group( 1 ) ) ), t )

    # Then convert hexa entities (such as &#x00E9;)
    return re.sub( u'&#x(\w+);', lambda x: unichr( int( x.group( 1 ), 16 ) ), t )


def normalize_string( text ):
    return unicodedata.normalize( 'NFKD', text ).encode( 'ascii', 'ignore' )


def set_pretty_formatting( text ):
    text = text.replace( "<br />", "\n" )
    text = text.replace( "<hr />", ( "_" * 150 ) + "\n" )
    text = text.replace( "<p>", "" ).replace( "</p>", "" )
    text = text.replace( "<i>", "[I]" ).replace( "</i>", "[/I]" )
    text = text.replace( "<em>", "[I]" ).replace( "</em>", "[/I]" )
    text = text.replace( "<b>", "[B]" ).replace( "</b>", "[/B]" )
    text = text.replace( "<strong>", "[B]" ).replace( "</strong>", "[/B]" )
    text = re.sub( "(?s)<[^>]*>", "", text )
    return text.strip()



if ( __name__ == "__main__" ):
    #print __doc__.encode( "ISO-8859-1" )
    #print "-"*100
    #print "normalize_string::%s" % normalize_string( __doc__ )
    #print "-"*100
    print htmlentitydecode( "Ast&#xE9;rix &#x26; Ob&#xE9;lix: Mission Cl&#xE9;op&#xE2;tre" )

