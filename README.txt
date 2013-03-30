Parameters:
Simply add $INFO[ListItem.foo]

For example:
XBMC.RunScript(script.metadata.actors,$INFO[ListItem.foo])


Launch from Library MovieActors, MovieDirectors or TvShowActors.
Add button in DialogContextMenu.xml in main grouplist.

<control type="grouplist" id="996">
	<description>grouplist for context buttons</description>
	...
	<control type="button" id="2001">
		<description>actor/director info button (visible only container is MovieActors, MovieDirectors or TvShowActors)</description>
		...
		<label>$VAR[ContextMenuLabel2001]</label>
		<onclick>RunScript(script.metadata.actors,$INFO[ListItem.Label])</onclick>
		<visible>Container.Content(Actors) | Container.Content(Directors) | Container.Content(Artists)</visible>
		<visible>System.HasAddon(script.metadata.actors) + !Window.IsVisible(script-Actors-DialogInfo.xml)</visible>
	</control>
	...
</control>
And in includes.xml
<includes>
	<variable name="ContextMenuLabel2001">
		<value condition="Container.Content(Artists) + Window.IsVisible(MusicLibrary)">Filmography</value>
		<value condition="Container.Content(Actors)">Actor information</value>
		<value condition="Container.Content(Directors)">Director information</value>
		<value condition="Container.Content(Artists)">Artist information</value>
	</variable>
</includes>


Launch from DialogVideoInfo.xml for actor infos: (create a new button and keep $INFO[Container(50).Listitem.Label] )

<control type="button" id="????">
	<description>actor info button</description>
	...
	<onclick>RunScript(script.metadata.actors,$INFO[Container(50).Listitem.Label])</onclick>
	<visible>Control.IsVisible(50) + System.HasAddon(script.metadata.actors)</visible>
</control>


Launch from DialogVideoInfo.xml for director/writer infos:

<onclick condition="System.HasAddon(script.metadata.actors)">RunScript(script.metadata.actors,$INFO[ListItem.Director])</onclick>
<onclick condition="System.HasAddon(script.metadata.actors)">RunScript(script.metadata.actors,$INFO[ListItem.Writer])</onclick>


Special Launch for Artists from DialogAlbumInfo.xml:

<control type="button" id="15">
	<description>Filmography</description>
	...
	<label>Filmography</label>
	<onclick>RunScript(script.metadata.actors,$INFO[Listitem.Artist])</onclick>
	<visible>container.content(Artists) + System.HasAddon(script.metadata.actors)</visible>
</control>


Available Property for hide DialogVideoInfo.xml / DialogAlbumInfo.xml:
Window.Property(script.metadata.actors.isactive): return 1 or empty

For example:
<onload>ClearProperty(script.metadata.actors.isactive)</onload>

<animation effect="slide" start="1100,0" end="0,0" time="400" condition="!StringCompare(Window.Property(script.metadata.actors.isactive),1)">Conditional</animation>
<animation effect="slide" start="0,0" end="1100,0" time="400" condition="StringCompare(Window.Property(script.metadata.actors.isactive),1)">Conditional</animation>


-------------------------------------------------------------------------------------------------------------------------------------------------------------------

List of Built In Controls Available In script-Actors-DialogInfo.xml:

5 ---> button ----> Toggle between Biography and Known Movies (Deprecated)
6 ---> button ----> Refresh actor information
8 ---> button ----> Browse your movies of the currently selected actor
10 --> button ----> Get actor thumbnail
11 --> button ----> edit (require tmdb account)
20 --> button ----> Get actor fanart
25 --> button ----> open add-on settings
50 --> container -> window actor info
150 -> container -> movies list (acting / directing / writing)
250 -> container -> thumbs list of actor


Labels Available In script-Actors-DialogInfo.xml:

Labels of the currently selected actor / director / writer / artist.
Container(50).Property(ParentDir) -> return true if parent dir exists or empty
Listitem.Title --------------------> Name
Listitem.Label --------------------> Same as Title
ListItem.Icon ---------------------> icon
ListItem.Plot ---------------------> Biography
ListItem.Property(Biography) ------> Same as Plot
ListItem.Property(Biooutline) -----> (currently not used)
ListItem.Property(TotalMovies) ----> Total of Known Movies (acting / directing / writing)
ListItem.Property(Birthday) -------> Date of Birthday
ListItem.Property(HappyBirthday) --> return true or empty
ListItem.Property(Age) ------------> Age (30)
ListItem.Property(AgeLong) --------> Age long format (age 30)
ListItem.Property(Deathday) -------> Date of Deathday
ListItem.Property(Deathage) -------> Age of dead (30)
ListItem.Property(DeathageLong) ---> Age of dead long format (age 30)
ListItem.Property(PlaceOfBirth) ---> Place of birth
ListItem.Property(AlsoKnownAs) ----> Also Known Name
ListItem.Property(Homepage) -------> Link of homepage, you can use onclick for open web browser directly on homepage: RunScript(script.metadata.actors,homepage=$INFO[ListItem.Property(Homepage)])
ListItem.Property(Adult) ----------> Is Adult Actor (no / yes)
ListItem.Property(Fanart_Image) ---> Fanart
ListItem.Property(extrafanart) ----> extrafanart (return empty if not exists)
ListItem.Property(extrathumb) -----> extrathumb (return empty if not exists)

Labels of Known Movies list
Container(150).ListItem.Label ---------------------> Title of movie
Container(150).ListItem.Title ---------------------> same as label
Container(150).ListItem.originaltitle -------------> originaltitle
Container(150).ListItem.Year ----------------------> year
Container(150).Listitem.Icon ----------------------> icon of movie
Container(150).ListItem.Property(role) ------------> role in currently slected movie
Container(150).ListItem.Property(job) -------------> job in currently slected movie (director / writer / etc)
Container(150).ListItem.Property(releasedate) -----> release date of movie
Container(150).ListItem.Property(year) ------------> same as year, but not return empty
Container(150).ListItem.Property(LibraryHasMovie) -> return 1 or empty, if movie exists in library
Container(150).ListItem.Property(Playcount) -------> Playcount of movie (default is 0)
Container(150).ListItem.Property(file) ------------> media to play

Labels of thumbs list
Container(250).ListItem.Label --------------------> Image résolution (512x720)
Container(250).Listitem.Icon ---------------------> Image
Container(250).ListItem.Property(aspect_ratio) ---> Aspect Ratio (0.66)


-------------------------------------------------------------------------------------------------------------------------------------------------------------------

List of Built In Controls Available In script-Actors-DialogVideoInfo.xml:

5 ---> button ----> (currently not used in python)
6 ---> button ----> Refresh movie information
8 ---> button ----> (currently not used in python)
10 --> button ----> (currently not used in python)
20 --> button ----> movie fanart
50 --> container -> window movie info
150 -> container -> actor / director / writer / artist listing


Labels Available In script-Actors-DialogVideoInfo.xml:

Labels of the currently selected movie.
Container(50).Property(ParentDir) -> return true if parent dir exists or empty
Listitem.Title --------------------> Name
Listitem.Label --------------------> Same as Title
ListItem.Icon ---------------------> icon
ListItem.Plot ---------------------> plot
ListItem.year ---------------------> year
ListItem.Date ---------------------> same as ListItem.Property(releasedate)
ListItem.originaltitle ------------> originaltitle
ListItem.director -----------------> director
ListItem.trailer ------------------> trailer
ListItem.genre --------------------> genre
ListItem.mpaa ---------------------> mpaa
ListItem.playcount ----------------> playcount
ListItem.plotoutline --------------> plotoutline
ListItem.rating -------------------> rating
ListItem.duration -----------------> duration
ListItem.studio -------------------> studio
ListItem.tagline ------------------> tagline
ListItem.top250 -------------------> top250
ListItem.votes --------------------> votes
ListItem.writer -------------------> writer
ListItem.lastplayed ---------------> lastplayed
ListItem.FilenameAndPath ----------> path of your movie
ListItem.Property(Fanart_Image) ---> fanart
ListItem.Property(set) ------------> Title of Movie Set (return empty if not exists)
ListItem.Property(country) --------> country
ListItem.Property(releasedate) ----> release date of movie
ListItem.Property(lastupdated) ----> last update info
ListItem.Property(Homepage) -------> Link of homepage, you can use onclick for open web browser directly on homepage: RunScript(script.metadata.actors,homepage=$INFO[ListItem.Property(Homepage)])
ListItem.Property(onlineinfo) -----> Link to visit movie on site, you can use onclick for open web browser directly on site: RunScript(script.metadata.actors,homepage=$INFO[ListItem.Property(onlineinfo)])

Labels of the list actor / director / writer / artist.
Container(150).Listitem.Title -------------------> Name
Container(150).Listitem.Label -------------------> Same as Title
Container(150).Listitem.Label2-------------------> Role
Container(150).ListItem.Icon --------------------> icon
Container(150).ListItem.Plot --------------------> Biography
Container(150).ListItem.Property(Biography) -----> Same as Plot
Container(150).ListItem.Property(Biooutline) ----> (currently not used)
Container(150).ListItem.Property(TotalMovies) ---> Total of Known Movies (acting / directing / writing)
Container(150).ListItem.Property(Birthday) ------> Date of Birthday
Container(150).ListItem.Property(HappyBirthday) -> return true or empty
Container(150).ListItem.Property(Age) -----------> Age (30)
Container(150).ListItem.Property(AgeLong) -------> Age long format (age 30)
Container(150).ListItem.Property(Deathday) ------> Date of Deathday
Container(150).ListItem.Property(Deathage) ------> Age of dead (30)
Container(150).ListItem.Property(DeathageLong) --> Age of dead long format (age 30)
Container(150).ListItem.Property(PlaceOfBirth) --> Place of birth
Container(150).ListItem.Property(AlsoKnownAs) ---> Also Known Name
Container(150).ListItem.Property(Homepage) ------> Link of homepage, you can use onclick for open web browser directly on homepage: RunScript(script.metadata.actors,homepage=$INFO[ListItem.Property(Homepage)])
Container(150).ListItem.Property(Adult) ---------> Is Adult Actor (no / yes)
Container(150).ListItem.Property(Fanart_Image) --> Fanart
Container(150).ListItem.Property(extrafanart) ---> extrafanart (return empty if not exists)
Container(150).ListItem.Property(extrathumb) ----> extrathumb (return empty if not exists)


-------------------------------------------------------------------------------------------------------------------------------------------------------------------

** BACKEND AND DIALOG BACKEND**

For example from MyVideoNav.xml:
<window id="25">
	<onload condition="System.HasAddon(script.metadata.actors)">RunScript(script.metadata.actors,backend)</onload>

For example from DialogVideoInfo.xml:
<window id="2003">
	<onload condition="System.HasAddon(script.metadata.actors) + !IsEmpty(ListItem.Cast)">RunScript(script.metadata.actors,dialogbackend)</onload>

Labels Available from backend.

Window.Property(current.actor.name) ----------> Name
Window.Property(current.actor.biography) -----> Biography
Window.Property(current.actor.biooutline) ----> (currently not used)
Window.Property(current.actor.birthday) ------> Date of Birthday
Window.Property(current.actor.happybirthday) -> return true or empty
Window.Property(current.actor.age) -----------> Age (30)
Window.Property(current.actor.agelong) -------> Age long format (age 30)
Window.Property(current.actor.deathday) ------> Date of Deathday
Window.Property(current.actor.deathage) ------> Age of dead (30)
Window.Property(current.actor.deathagelong) --> Age of dead long format (age 30)
Window.Property(current.actor.placeofbirth) --> Place of birth
Window.Property(current.actor.alsoknownas) ---> Also Known Name
Window.Property(current.actor.homepage) ------> Link of homepage, you can use onclick for open web browser directly on homepage: RunScript(script.metadata.actors,homepage=$INFO[Window.Property(current.actor.homepage)])
Window.Property(current.actor.adult) ---------> Is Adult Actor (no / yes)

Window.Property(current.actor.icon) ----------> icon
Window.Property(current.actor.fanart_image) --> Fanart
Window.Property(current.actor.extrafanart) ---> extrafanart (return empty if not exists)
Window.Property(current.actor.extrathumb) ----> extrathumb (return empty if not exists)

Window.Property(current.actor.totalmovies) ---> (currently not used) Total of Known Movies (acting / directing / writing)


-------------------------------------------------------------------------------------------------------------------------------------------------------------------

** HOME WIDGET : Most Popular Artists Born Today **

Parameters:
RunScript(script.metadata.actors,borntoday[,limit,random])
limit  : 1 - 100 max
random : random and choice limit in 100 peoples

For example:
<onload condition="System.HasAddon(script.metadata.actors)">RunScript(script.metadata.actors,borntoday,10,random)</onload>

Labels Available from borntoday in Home.

Window.Property(peopleborntoday.[1-100max].name) --------> Name
Window.Property(peopleborntoday.[1-100max].job) ---------> Actor / Actress / Other, and last notable movie  
Window.Property(peopleborntoday.[1-100max].bio) ---------> Biography
Window.Property(peopleborntoday.[1-100max].icon) --------> icon
Window.Property(peopleborntoday.[1-100max].fanart) ------> Fanart
Window.Property(peopleborntoday.[1-100max].extrafanart) -> extrafanart (return empty if not exists)
Window.Property(peopleborntoday.[1-100max].extrathumb) --> extrathumb (return empty if not exists)
Window.Property(peopleborntoday.[1-100max].urlinfo) -----> used from python <onclick>RunScript(script.metadata.actors,urlinfo=$INFO[Window.Property(peopleborntoday.[1-10].urlinfo)])</onclick>

Window.Property(peopleborntoday.[1-100max].media.[1-25max].title) --> Title
Window.Property(peopleborntoday.[1-100max].media.[1-25max].icon) ---> Icon
Window.Property(peopleborntoday.[1-100max].media.[1-25max].fanart) -> Fanart
Window.Property(peopleborntoday.[1-100max].media.[1-25max].file) ---> media to play
Window.Property(peopleborntoday.[1-100max].media.[1-25max]1.type) --> movie / tvshow / music


-------------------------------------------------------------------------------------------------------------------------------------------------------------------
