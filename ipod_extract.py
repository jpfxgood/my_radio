#!/usr/bin/python
import os
import gpod
import re
import pprint
import subprocess

db = gpod.Database("/media/JAMES' IPOD")

albums = {}
artists = {}

def normalize( name ):
    name = name.strip().upper()
    retname = ""
    inSpace = False
    for c in name:
        if c.isspace():
            if inSpace:
                continue
            inSpace = True
            retname = retname + "_"
        elif c.isalnum():
            inSpace = False
            retname = retname + c
    return retname


for track in db:
    album = track['album']
    artist = track['artist']

    if artist == None:
        artist = ""

    if album:
        albums[normalize(album+" "+artist)] = (album,artist)
    if artist:
        if artists.get(normalize(artist),None):
            artists[normalize(artist)][1].add(album)
        else:
            artists[normalize(artist)] = (artist,set([album]))

wiki_albums = {}
wiki_artists = {}

for fname in os.listdir("music_extract"):
    f = open("music_extract/"+fname,"r")
    etype = f.readline().strip()
    name = f.readline().strip()
    if etype == "Album":
        artist_name = f.readline().strip()

    article = f.readline().strip()

    if etype == "Album":
        wiki_albums[normalize(name+" "+artist_name)] = (name,re.split(r"\.",article)[:5])

    if etype == "Artist":
        wiki_artists[normalize(name)] = (name,re.split(r"\.",article)[:5])

    f.close()


albums_found = 0
artists_found = 0

if not os.path.exists("music_descriptions"):
    os.mkdir("music_descriptions")

for a in albums.keys():
    desc = wiki_albums.get(a,None)
    if desc:
        open("music_descriptions/%s.txt" % (a),"w").write(".".join(desc[1]))
        subprocess.call(["/bin/bash","-c","espeak -a 50 -p 50 -f music_descriptions/%s.txt -w music_descriptions/%s.wav;lame music_descriptions/%s.wav music_descriptions/%s.mp3" % (a,a,a,a)])
        albums_found = albums_found + 1

for a in artists.keys():
    desc = wiki_artists.get(a,None)
    if desc:
        open("music_descriptions/%s.txt" % (a),"w").write(".".join(desc[1]))
        subprocess.call(["/bin/bash","-c","espeak -a 50 -p 50 -f music_descriptions/%s.txt -w music_descriptions/%s.wav;lame music_descriptions/%s.wav music_descriptions/%s.mp3" % (a,a,a,a)])
        artists_found = artists_found + 1

print "Found %d albums out of %d" % (albums_found,len(albums))
print "Found %d artists out of %d" % (artists_found,len(artists))

#pp = pprint.PrettyPrinter(indent=4)
#
#print "====== Albums ======"
#pp.pprint(albums)
#print "====== Artists ======"
#pp.pprint(artists)
#print "====== Wiki Albums ====="
#pp.pprint(wiki_albums)
#print "====== Wiki Artists ===="
#pp.pprint(wiki_artists)

