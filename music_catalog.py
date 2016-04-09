#!/usr/bin/python
# Copyright 2009 James P Goodwin prototype for automatic playlist
# audio annotation

import os
import sys
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.easyid3 import EasyID3
import codecs
import pprint
from random import randrange
import config
               
catalogs = {}

def get_catalog(verbose = False, path="~"):
    """ factory to return the right type of catalog for this user"""
    userConfig = config.get_config(path)
    if userConfig.getKey(config.CATALOG_TYPE) == config.MP3_CATALOG:
        cat_name = userConfig.getKey(config.CATALOG_NAME)
        catalog = catalogs.get( cat_name, None)
        if not catalog:
            catalog = MP3MusicCatalog(cat_name,verbose=verbose)
            catalogs[cat_name] = catalog
        return catalog
    else:
        raise Exception("Catalog type not supported yet!")


class PlayList:
    """ base class for music catalog playlists """
    def __init__(self):
        pass
        
    def numtracks( self ):
        pass
        
    def addtrack( self, track ):
        pass
        
    def gettrack( self, idx ):
        pass
        
    def deltrack( self, idx ):
        pass
        
    def save( self ):
        pass
        
    def load( self ):
        pass
        
    def delete_playlist():
        pass
        
class M3UPlayList ( PlayList ):
    """ manipulate m3u playlists """
    def __init__( self, name ):
        """ if playlist exists open it and read it, otherwise create it in memory """
        self.entries = []
        self.name = os.path.expanduser(name)+".m3u"
        if os.path.exists( self.name ):
            self.load()
        
    def numtracks( self ):
        return len(self.entries)
        
    def addtrack( self, track ):
        self.entries.append(track)
        
    def gettrack( self, idx ):
        return self.entries[idx]
        
    def deltrack( self, idx ):
        del self.entries[idx]

    def attrout(self, playlist, track, attr ):
        if attr in track:
            print >>playlist, "#%s=%s"%(attr,track[attr].encode('utf-8','ignore'))
        
    def save( self ):
        playlist = open(self.name,"w")
        for t in self.entries:
            self.attrout(playlist,t,"title")
            self.attrout(playlist,t,"album")
            self.attrout(playlist,t,"artist")
            print >>playlist, t["path"]
        playlist.close()
        
    def load( self ):   
        self.entries = []
        playlist = codecs.open(self.name,"r", "utf-8", errors='replace', buffering=0)
        track = {}
        for t in playlist:    
            if t.startswith("#"):
                (attr,value) = t[1:].split("=",1)
                track[attr] = value.strip()
            else:
                track["path"] = t.strip()
                self.entries.append(track)
                track = {}
        playlist.close()
        
    def delete( self ):
        if os.path.exists(self.name):
            os.remove(self.name)
           
class MusicCatalog:
    """ Base class for music catalog interface """
    def __init__( self ):
        pass
        
    def load( self ):
        pass
        
    def discover( self ):
        pass
        
    def save( self ):
        pass
        
    def numtracks( self ):
        pass
        
    def gettrack( self, idx ):
        pass
        
    def addtrack( self, track ):
        pass
        
    def deltrack( self, idx ):
        pass
        
    def delete_playlist( self, name ):
        pass
        
    def create_playlist( self, name ):
        pass
        
    def pprint( self ):
        pass
        
class MP3MusicCatalog(MusicCatalog):
    """ Catalog instance implementing a local mp3 catalog """
    def __init__( self, filename, verbose=False ):
        """ constructs the mp3 based catalog, filename is the name of the catalog file, if it exists it is loaded """
        self.filename = os.path.expanduser(filename)
        self.tracks = {}
        self.track_data = []
        self.track_keys = []
        self.verbose = verbose
        if os.path.exists(self.filename):
            self.load()
            
    def load( self ):
        """ load the catalog from a flat file """
        catalog = codecs.open(self.filename,"r","utf-8",errors="replace", buffering=0)
        for line in catalog:
            parts = line.split("|")
            track = {}
            for part in parts:
                (name,value) = part.split("=",1)
                track[name.strip()] = value.strip()
            self.addtrack( track )
        catalog.close()
        
    def save( self ):
        """ save the catalog to a flat file """
        catalog = codecs.open(self.filename,"w","utf-8",buffering=0)
        for track in self.track_data:
            try:              
                cat_line = "|".join([item[0]+"="+item[1] for item in track.items()])
                cat_line += '\n'
                if self.verbose:
                    print cat_line
                catalog.write(cat_line)
            except Exception, e:
                if self.verbose:
                    print "Error writing ",str(e),track
        catalog.close()
        
    def discover( self ):
        """ dig around the user's home dir and find any mp3's and add them to the catalog """
        def fixtag( mp4tag ):
            tagmap = {'\xa9alb':'album', '\xa9ART':'artist', '\xa9nam':'title', '\xa9gen':'genre', '\xa9day':'date', 'trkn':'tracknumber'}
            if mp4tag in tagmap:
                return tagmap[mp4tag]
            else:
                return None
            
        def scan( path ):
            """ recursively scan the path passed and collect mp3's """
            path = os.path.expanduser(path)
            for (dirpath, dirnames, filenames) in os.walk(path,followlinks=True):
                for f in filenames: 
                    try:
                        if f.endswith("mp3"):
                            fullname = os.path.join(dirpath,f)
                            tags = MP3(fullname, ID3=EasyID3)
                            mp3 = {}
                            for item in tags.items():
                                mp3[item[0].strip()] = item[1][0].strip()
                            mp3["path"] = os.path.abspath(fullname)
                            self.addtrack(mp3)
                        elif f.endswith("m4a"):
                            fullname = os.path.join(dirpath,f)
                            tags = MP4(fullname)
                            mp3 = {}
                            for item in tags.items():
                                tag = fixtag(item[0].strip())
                                if tag:
                                    if tag == 'tracknumber':
                                        mp3[tag] = str(item[1][0][0])
                                    else:
                                        mp3[tag] = item[1][0].strip()
                            mp3["path"] = os.path.abspath(fullname)
                            self.addtrack(mp3)
                    except Exception,e:
                        print "Error:"+str(e)
                        
                        
        scan("~/.")
        
    def addtrack( self, track ):
        """ add a track to the catalog """                                                   
        try:
            hash_value = hash(track["album"]+track["title"]+track["artist"]+track["tracknumber"])
            if hash_value not in self.tracks:
                self.tracks[hash_value] = track
                self.track_keys.append(hash_value)
                self.track_data.append(track)
                return True     
            else:    
                if self.verbose:
                    print "Track is a duplicate",track
                return False
        except Exception,e:
            if self.verbose:
                print "Failed to add track",track,"Error",str(e)
            return False
            
    def pprint(self):
        """ print out a pretty listing of the tracks """
        pprint.pprint(self.track_data)
        
    def numtracks( self ):
        """ return the number of tracks in the catalog """
        return len(self.track_data)
        
    def gettrack( self, idx ):
        """ return track number idx in the catalog """
        return self.track_data[idx]
        
    def deltrack( self, idx ):
        """ delete track number idx from the catalog """
        del self.tracks[self.track_keys[idx]]
        del self.track_data[idx]
        del self.track_keys[idx]
        
    def create_playlist( self, name ):
        """ create a new playlist """
        return M3UPlayList(name)
        
    def delete_playlist( self, name ):
        """ delete a playlist """
        M3UPlayList( name ).delete()
                        
if __name__ == '__main__':
    catalog = get_catalog()
    catalog.delete_playlist("~/random")
    random = catalog.create_playlist("~/random")
    ntracks = catalog.numtracks()
    s = set([])
    for i in range(0,30):
        while True:
            rtrack = randrange(ntracks)
            if rtrack not in s:
                s.add(rtrack)
                break
                
        random.addtrack(catalog.gettrack(rtrack))
    random.save()
