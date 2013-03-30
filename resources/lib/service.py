
import time
t1 = time.time()

import os
import sys
import xbmc
from metautils import getXBMCActors

totals = 0
for library_type in [ "artist", "actor", "" ]:
    totals += len( getXBMCActors( library_type, False ) )

if xbmc.getCondVisibility( "System.HasAlarm(actors.service)" ):
    xbmc.executebuiltin( "CancelAlarm(actors.service,true)" )
command = "RunScript(%s)" % os.path.join( sys.path[ 0 ], "service.py" )
xbmc.executebuiltin( "AlarmClock(actors.service,%s,30,true)" % command )

print "Service: %i actors took %r" % ( totals, time.time() - t1 )
