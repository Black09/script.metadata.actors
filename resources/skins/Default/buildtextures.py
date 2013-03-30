
import os
import re
import shutil

prefix = "actors-"

skin_sources_dir = r"E:\coding\Windows\xbmc\addons\skin.confluence"
skin_sources_dir = skin_sources_dir.replace( "\\", "/" ).strip( "/" )

# get xml content
str_xml = ""
for root, dirs, files in os.walk( "720p" ):
    for file in files:
        str_xml += open( os.path.join( root, file ) ).read().lower()


def get_bad_strings():
    strings = re.compile( '<string id="(.*?)">(.*?)</string>' ).findall( open( skin_sources_dir + "language/English/strings.xml" ).read() )
    for i, s in strings:
        if i in str_xml:
            print ( i, s )
#get_bad_strings()


def compile_images():
    # media source
    media = skin_sources_dir + "/media"

    for root, dirs, files in os.walk( media ):#, topdown=False ):
        for file in files:
            fpath = os.path.join( root, file )
            img = fpath.replace( media, "" ).replace( "\\", "/" ).strip( "/" )
            if file.lower() in str_xml:
                dst = "media/" + prefix + img
                print dst
                if not os.path.exists( os.path.dirname( dst ) ):
                    os.makedirs( os.path.dirname( dst ) )
                shutil.copy( fpath, dst )


    # backgrounds source
    backgrounds = skin_sources_dir + "/backgrounds"

    for root, dirs, files in os.walk( backgrounds ):#, topdown=False ):
        for file in files:
            fpath = os.path.join( root, file )
            img = fpath.replace( backgrounds, "" ).replace( "\\", "/" ).strip( "/" )
            if file.lower() in str_xml:
                dst = "backgrounds/" + prefix + img
                print dst
                if not os.path.exists( os.path.dirname( dst ) ):
                    os.makedirs( os.path.dirname( dst ) )
                shutil.copy( fpath, dst )
#compile_images()