#!/usr/bin/python
# Copyright 2009 James P Goodwin prototype for automatic playlist
# audio annotation

import os
import shutil
import re
import pprint
import subprocess
import random
import time
import sys
import getcal
import getfeed
from optparse import OptionParser
import music_catalog
import config
import xml.sax
import xml.sax.handler
from config import get_profile
import datetime
import album
import artist
import codecs
from my_radio_module import nopunct, normalize, escape, safeRemove, hasalnum
from voice import text2wav
import shutil
import traceback
import string


class TemplateReader (xml.sax.handler.ContentHandler):
    def __init__(self, filename, context ):
        self.filename = filename
        self.context = context
        self.context_stack = []
        self.curtext_required = None
        self.curtext_voice = None
        self.curtext_type = None
        self.curtext = None
        self.elementid = 0
        xml.sax.parse(self.filename,self)
        
    def pushContext(self):
        self.context_stack.append(self.context)
        
    def popContext(self):
        self.context = self.context_stack.pop()   
        
    def tagContext(self):
        self.context["contextid"] = str(self.elementid)
        self.elementid += 1
        
    def startElement(self, name, attrs ):
        if name == "template":
            self.context["template"] = {}
            self.pushContext()
            self.context = self.context["template"]
            self.tagContext()
        elif name == "text":
            self.curtext_type = attrs["type"]
            if "required" in attrs:
                self.curtext_required = attrs["required"]
            else:
                self.curtext_required = None
                
            if "voice" in attrs:
                self.curtext_voice = attrs["voice"]
            else:
                self.curtext_voice = None
            self.curtext = ""
        elif name in ["block", "tracks"]:
            self.context[name] = {}
            self.pushContext()
            self.context = self.context[name]
            self.context["repeat"] = attrs["repeat"]
            self.tagContext()
        elif name in ["weather", "news", "appointments"]:
            self.context[name] = {}
            self.pushContext()
            self.context = self.context[name]
            self.context["freq"] = attrs["freq"]
            self.tagContext()
        elif name in [ "track", "artist", "album"] :
            self.context[name] = {}
            self.pushContext()
            self.context = self.context[name]
            self.context["type"] = attrs["type"]
            self.tagContext()
            
    def characters(self, content):
        if self.curtext_type and self.curtext != None:
            self.curtext += content.strip()
    
    def endElement(self, name ):
        if name == "text":      
            self.curtext = re.sub("(\%\([0-9a-zA-Z_]*\)s)","|\g<1>|",self.curtext)
            if self.curtext_type not in self.context:
                self.context[self.curtext_type] = []
            self.context[self.curtext_type].append((self.curtext,self.curtext_required,self.curtext_voice))
            self.curtext_type = None
            self.curtext_required = None
            self.curtext_voice = None
            self.curtext = None
        elif name in ["block", "weather", "news", "appointments","track","artist", "album", "tracks"]:
            self.popContext()

class MyRadio:
    def __init__(self,
        user_path = "~",
        data_path = "music_extract", 
        music_index = "music_extract.idx", 
        music_path= "~",
        weather_provider = None,
        weather_rss = None,
        news_provider = None,
        news_rss = None,
        calendar_provider = None,
        calendar_path = None,
        verbose = False,
        debug = False,
        filter = None,
        web_root = None,
        web_server = None,
        web_sync = None,
        voice = "julie" ):
        self.user_path = user_path
        self.weather_provider = weather_provider
        self.weather_rss = weather_rss
        self.news_provider = news_provider
        self.news_rss = news_rss
        self.calendar_provider = calendar_provider
        self.calendar_path = calendar_path
        self.basename = time.strftime("my_radio_%A_%B_%d_%Y")
        self.music_basepath = os.path.expanduser(music_path)
        self.music_path = os.path.join(self.music_basepath,self.basename)
        self.user_path = os.path.expanduser("~")
        self.db = None
        self.selected_artists = set()
        self.selected_albums = set()
        self.data_path = data_path
        self.music_index = music_index
        self.sizedb = 0
        self.playlist = None
        self.sequence = 0
        self.verbose = verbose
        self.text_segment = ""
        self.debug = debug
        self.filter = filter
        self.web_root = web_root
        self.web_server = web_server
        if web_sync == "true":
            self.web_sync = True
        else:
            self.web_sync = False
        self.voice = voice
            
        random.seed()         
        
    def get_artist_text( self, artist_name, debug = False ):
    
        if not artist_name:
            return []
    
        key = normalize("artist_%s_used_lines"%(normalize(artist_name)))
        used_lines = get_profile(self.user_path).getKey(key)
        if used_lines == None:
            used_lines = 0
        else:
            used_lines = int(used_lines)
    
        paras = artist.fetch_paragraphs( artist_name )
        if debug:
            print "======== start artist paras %s ========="%(artist_name)
            print paras
            print "======== start artist paras %s ========="%(artist_name)
    
        if not paras:
            return []
    
        sent = []
        for (s,p) in paras:
            for l in re.split("[\.\?\!]",p):
                l = l.strip()
                if l:
                    sent.append(l)
    
        wc = 0
        idx = 0
        for k in sent[used_lines:]:
            wc = wc + len(k.split())
            if wc >= 60:
                break
            idx = idx + 1
    
    
        get_profile(self.user_path).setKey(key,str(used_lines+idx))
    
        if debug:
            print "+++++++++++++ start selected artist lines %s ++++++++++++"%(artist_name)
            print sent[used_lines:used_lines+idx]
            print "+++++++++++++ end selected artist lines %s ++++++++++++"%(artist_name)
        return sent[used_lines:used_lines+idx]
    
    def get_album_text( self, album_name, artist_name, debug = False ):
    
        if not album_name:
            return []
    
        key = normalize("album_%s_%s_used_lines"%(normalize(album_name),normalize(artist_name)))
        used_lines = get_profile(self.user_path).getKey(key)
        if used_lines == None:
            used_lines = 0
        else:
            used_lines = int(used_lines)
    
        paras = album.fetch_paragraphs( album_name, artist_name )
        if not paras:
            return []
    
        if debug:
            print "======== start album paras %s %s ========="%(artist_name, album_name)
            print paras
            print "======== start album paras %s %s ========="%(artist_name, album_name)
    
        sent = []
        for (s,p) in paras:
            for l in re.split("[\.\?\!]",p):
                l = l.strip()
                if l:
                    sent.append(l)
    
        wc = 0
        idx = 0
        for k in sent[used_lines:]:
            wc = wc + len(k.split())
            if wc >= 60:
                break
            idx = idx + 1
    
        get_profile(self.user_path).setKey(key,str(used_lines+idx))
        if debug:
            print "+++++++++++++ start selected album lines %s %s ++++++++++++"%(artist_name,album_name)
            print sent[used_lines:used_lines+idx]
            print "+++++++++++++ end selected album lines %s %s ++++++++++++"%(artist_name, album_name)
        return sent[used_lines:used_lines+idx]
    
    def openCatalog( self, player_path ):
        if self.verbose:
            print "Opening music catalog"
        self.db = music_catalog.get_catalog(verbose=self.verbose,path=self.user_path)
        self.sizedb = self.db.numtracks()
        
    def closeCatalog( self ):
        if self.verbose:
            print "Copying to music catalog"
        self.playlist.save()
#        self.db.save()
        if self.verbose:
            print "Closing database"
        self.db = None
        self.sizedb = 0
        self.playlist = None
        
    def newPlaylist( self, name ):
        if self.verbose:
            print "Creating playlist"
        full_name = os.path.join(self.music_path,name)
        self.db.delete_playlist(full_name)
        self.playlist = self.db.create_playlist(full_name)
        
    def transferTrack( self, source, dest, downsample=False ):
        if self.verbose:
            print "transferTrack", source, dest
        (dest_path,dest_name) = os.path.split(dest)
        path_parts = []                            
        (dest_path,path_part) = os.path.split(dest_path)
        while dest_path != "/":
            path_parts.insert(0,path_part)
            (dest_path,path_part) = os.path.split(dest_path)
        path_parts.insert(0,os.path.join(dest_path,path_part))
        create_path = path_parts[0]
        if not os.path.exists(create_path):
            os.mkdir(create_path)
        for ridx in range(1,len(path_parts)):
            create_path = os.path.join(create_path,path_parts[ridx])
            if not os.path.exists(create_path):
                os.mkdir(create_path)
                
        if downsample and source.endswith("mp3"):
            cmd = ["/bin/bash","-c","lame --preset 32 \"%s\" \"%s\""%(source,dest)]
        elif downsample and source.endswith("m4a"):
            cmd = ["/bin/bash","-c","faad -w \"%s\" | lame --preset 32 \"-\" \"%s\""%(source,dest.replace(".m4a",".mp3"))]
        else:
            cmd = ["/bin/bash","-c","cp \"%s\" \"%s\""%(source,dest)]
 
        if self.verbose:
            subprocess.call(cmd)
        else:
            subprocess.call(cmd,
            stdin = open("/dev/null","r"),
            stdout = open("/dev/null","w"),
            stderr = open("/dev/null","w"),
            close_fds = True)
            
            
        
    def syncPlaylist( self, player_path, wrapmp3=False ):
        playlist_path = os.path.join(player_path, self.basename)
        if os.path.exists(playlist_path):
            shutil.rmtree(playlist_path)
        os.mkdir(playlist_path)
        out_playlist_name = os.path.join(playlist_path, self.basename)
        out_playlist = self.db.create_playlist(out_playlist_name)    
        
        if self.verbose:
            print player_path
            print self.basename
            print playlist_path
            print self.music_path
            print self.music_basepath

        tracks = []
        for rdx in range(0, self.playlist.numtracks()):
            track = self.playlist.gettrack(rdx).copy()
            path = track["path"]
            out_path = os.path.join(playlist_path,"t%04d.mp3"%(rdx))
            tracks.append(out_path)
          
            self.transferTrack( path, out_path )
            print self.web_sync, self.web_root, self.web_server, out_path
            if self.web_sync:
                out_path = out_path.replace(self.web_root, self.web_server,1)
            print out_path        
            track["path"] = out_path
            out_playlist.addtrack(track)
        out_playlist.save()
        if self.web_sync:                             
            show_link = os.path.join(player_path,"show")
            subprocess.call(["/bin/bash","-c","rm %s.m3u;ln %s.m3u %s.m3u"%(show_link,out_playlist_name,show_link)])
            if wrapmp3:
                if os.path.exists("%s_MP3WRAP.mp3"%(out_playlist_name)):
                    os.remove("%s_MP3WRAP.mp3"%(out_playlist_name))
                subprocess.call(["/bin/bash","-c","mp3wrap %s %s"%(out_playlist_name," ".join(["\"%s\""%(f) for f in tracks]))])
                subprocess.call(["/bin/bash","-c","ffmpeg -i %s_MP3WRAP.mp3 -acodec copy %s.mp3"%(out_playlist_name,out_playlist_name)])
                os.remove("%s_MP3WRAP.mp3"%(out_playlist_name))
                subprocess.call(["/bin/bash","-c","rm %s.mp3;ln %s.mp3 %s.mp3"%(show_link,out_playlist_name,show_link)])

    def produceShow( self, player_path, template = "default.show", sync = False ):
        # build proto playlist with annotations
        
        def hasRequired( required, meta_data ):
            for k in required.split(","):
                if (k.strip() not in meta_data) or (not meta_data[k.strip()]):
                    return False
            return True      
            
        def uniqueChoice( context, intro_type ):
            options = context[intro_type]
            key = context["contextid"]+"_"+intro_type
            previous = get_profile(self.user_path).getKey(key)
            if previous:
                used = eval(previous)
                if len(used) == len(options):
                    used = set([])
            else:
                used = set([])
            choice = random.randint(0,len(options)-1)
            while choice in used:
                choice = random.randint(0,len(options)-1)
            used.add(choice)
            get_profile(self.user_path).setKey(key,str(used))
            return options[choice]

        def recordIntro( context, intro_type, meta_data, title):
            if intro_type in context:
                try:   
                    item = uniqueChoice(context, intro_type)
                    if not item[1] or hasRequired( item[1], meta_data ):
                        self.recordText( item[0]%meta_data, item[2])
                    else:
                        print "Required missing", context, intro_type, meta_data, title
                except Exception,e:
                    print >>sys.stderr,"Content warning continuing: "+str(e)
                    print >>sys.stderr,"============================================================================================"
                    traceback.print_exc(file=sys.stderr)
                    print >>sys.stderr,intro_type,title,item
                    print >>sys.stderr,"--------------------------------------------------------------------------------------------"
                    print >>sys.stderr,context
                    print >>sys.stderr,"--------------------------------------------------------------------------------------------"
                    print >>sys.stderr,meta_data
                    print >>sys.stderr,"============================================================================================"
                
        def recordTrack( context, meta_data, track_index ):
            self.flushText()
            self.playlist.addtrack( self.db.gettrack(meta_data["track_%d"%(track_index)]) )
            
        def list_script( talk_list ):
            if not talk_list:
                return ""
            elif len(talk_list) == 1:
                return talk_list[0]
            else:
                return  ", ".join(talk_list[:-1]) + " and " + talk_list[-1]
                
        def match_filter( track ):
            if not self.filter:
                return True
                
            for f in self.filter:
                (name,pat) = f.split(":",1)
                if not name in track:
                    return False
                if not re.match(pat,track[name]):
                    return False
            
            return True
                
        selected = set()
        def getTrackMetadata( repeat, meta_data ):
            artist_list = []
            album_list = []
            track_list = []
            for tn in range(0,repeat):
                while True:
                    choice = random.randrange(0,self.sizedb)
                    track = self.db.gettrack(choice)
                    if choice in selected:
                        continue
                        
                    if not match_filter(track):
                        continue
                        
                    if 'skip_when_suffling' in track and track['skip_when_shuffling']:
                        continue
                    album_name = track['album']
                    artist_name = track['artist']
                    if not artist_name and not album_name:
                        continue                
                    artists_db = artist.fetch_artist(artist_name)
                    albums_db = album.fetch_album_by_artist_and_name( artist_name, album_name)
                    if not artists_db and not albums_db:
                        continue
                    if artist_name not in artist_list:
                        artist_list.append(artist_name)
                    if album_name not in album_list:
                        album_list.append(album_name)
                    if track['title'] not in track_list:
                        track_list.append(track['title'])
                    break     
                track_prefix ="track_%d"%tn
                album_prefix ="album_%d"%tn
                artist_prefix ="artist_%d"%tn
                meta_data[track_prefix] = choice
                meta_data[artist_prefix] = artist_name
                if artists_db:
                    meta_data[artist_prefix+"_alias"] = artists_db[0].alias
                    meta_data[artist_prefix+"_assoc"] = artists_db[0].assoc
                    meta_data[artist_prefix+"_backgnd"] = artists_db[0].backgnd
                    meta_data[artist_prefix+"_birthname"] = artists_db[0].birthname
                    meta_data[artist_prefix+"_born"] = artists_db[0].born
                    meta_data[artist_prefix+"_died"] = artists_db[0].died
                    meta_data[artist_prefix+"_genre"] = artists_db[0].genre 
                    meta_data[artist_prefix+"_instrument"] = artists_db[0].instrument
                    meta_data[artist_prefix+"_label"] = artists_db[0].label
                    meta_data[artist_prefix+"_members"] = artists_db[0].members
                    meta_data[artist_prefix+"_origin"] = artists_db[0].origin
                    meta_data[artist_prefix+"_pastmemb"] = artists_db[0].pastmemb
                    meta_data[artist_prefix+"_years"] = artists_db[0].years
                meta_data[album_prefix] = album_name
                if albums_db:
                    meta_data[album_prefix+"_genre"] = albums_db[0].genre
                    meta_data[album_prefix+"_label"] = albums_db[0].label
                    meta_data[album_prefix+"_lastalbum"] = albums_db[0].lastalbum
                    meta_data[album_prefix+"_nextalbum"] = albums_db[0].nextalbum
                    meta_data[album_prefix+"_producer"] = albums_db[0].producer
                    meta_data[album_prefix+"_recorded"] = albums_db[0].recorded
                    meta_data[album_prefix+"_released"] = albums_db[0].released
                meta_data["title_%d"%tn] = track['title']
                meta_data["artist_list"] = list_script(artist_list)
                meta_data["album_list"] = list_script(album_list)
                meta_data["track_list"] = list_script(track_list)
                
            if self.verbose:
                pprint.pprint(meta_data)
                        
        def exerptFeed( feedurl, content ):
            key = normalize(feedurl + datetime.date.today().isoformat())
            lines_used = get_profile(self.user_path).getKey(key)
            if lines_used == None:
                lines_used = 0
            else:
                lines_used = int(lines_used)
                
            newcontent = "\n".join(content.split("\n")[lines_used:lines_used+10])
            if not newcontent.strip():
                lines_used = 0
                newcontent = "\n".join(content.split("\n")[lines_used:lines_used+10])
                
            get_profile(self.user_path).setKey(key,str(lines_used+10))
            return newcontent
                                                      
        def getContent( content_type, meta_data, index ):
            artist = meta_data.get("artist_%d"%index,None)
            meta_data["this_artist"] = artist
            album = meta_data.get("album_%d"%index,None)
            meta_data["this_album"] = album
            track = meta_data.get("title_%d"%index,None)
            meta_data["this_track"] = track
                
            next_artist = meta_data.get("artist_%d"%(index+1),None)
            meta_data["next_artist"] = next_artist
            next_album = meta_data.get("album_%d"%(index+1),None)
            meta_data["next_album"] = next_album
            next_track = meta_data.get("title_%d"%(index+1),None)
            meta_data["next_track"] = next_track
            
            if content_type == "news":  
                meta_data["news_source"] = self.news_provider
                return [exerptFeed(self.news_rss,getfeed.get_news(self.news_rss,self.verbose))]
            elif content_type == "weather": 
                meta_data["weather_source"] = self.weather_provider
                return [getfeed.get_weather(self.weather_rss,self.verbose)]
            elif content_type == "appointments":
                meta_data["appointments_source"] = self.calendar_provider
                cal_message = getcal.get_calendar(self.calendar_path,self.verbose)
                if cal_message:
                    return [cal_message]
                else:
                    return []
            elif content_type == "artist":
                if not (artist in self.selected_artists):
                    self.selected_artists.add(artist)
                    return self.get_artist_text(artist,self.debug )
                else:
                    return []
            elif content_type == "album":
                if not (album in self.selected_albums):
                    self.selected_albums.add(album)
                    return self.get_album_text(album,artist, self.debug)
                else:
                    return []
            elif content_type == "track":
                return [""]
                
        def recordTracks( context, meta_data):
            repeat = int(context["repeat"])
            getTrackMetadata( repeat, meta_data )
            for content_type in ("news","weather","appointments","artist","album","track"):
                getContent( content_type, meta_data, 0)
            recordIntro( context, "intro", meta_data, "Tracks Introduction")
            for track_index in range(0,repeat):
                recordTrack( context, meta_data, track_index )
                for content_type in ("news","weather","appointments","artist","album","track"):
                    recordContent( context, content_type, meta_data, track_index )
            recordIntro( context, "outro", meta_data, "Tracks Finale" )
            
        def recordContent( context, content_type, meta_data, index ):
            try:
                content = ""
                if content_type in context:
                    context = context[content_type]
                    freq = 1
                    if freq in context:
                        freq = int(context["freq"])
                    if not (index % freq):
                        content = getContent(content_type,meta_data, index)
                        if content:
                            recordIntro( context, "intro", meta_data, "%s Introduction"%content_type )
                            self.recordText( "|%s|"%" ".join(content) )
                            recordIntro( context, "outro", meta_data, "%s Finale"%content_type )
            except:  
                if self.verbose:
                    print "-------------------------------------------------------------------"
                    print content
                    pprint.pprint( context )
                    print content_type
                    pprint.pprint( meta_data )
                    print index
                    print "-------------------------------------------------------------------"
                raise
            
        # open and complile the template
        context = {}
        TemplateReader( template, context)
        
        if self.verbose:
            pprint.pprint(context)

        if not os.path.exists(self.music_path):
            os.mkdir(self.music_path)

        self.openCatalog( player_path )
        self.newPlaylist( self.basename )

        if context["template"]:
            meta_data = { "day" : time.strftime("%A"),
                            "date" : time.strftime("%B %d, %Y") }

            recordIntro(context["template"], "intro", meta_data, "Show Introduction" )

            if "block" in context["template"]:
                block_context = context["template"]["block"]
                repeat = int(block_context["repeat"])

                for block_index in range(0,repeat):
                    recordIntro( block_context, "intro", meta_data, "Block Introduction" )
                    if "tracks" in block_context:
                        recordTracks( block_context["tracks"], meta_data )
                    for content in ("news","weather","appointments"):
                        recordContent( block_context,content, meta_data, block_index )
                    recordIntro( block_context, "outro", meta_data, "Block Finale" )

            recordIntro(context["template"], "outro", meta_data, "Show Introduction" )
            self.flushText()

        if sync:
            self.syncPlaylist(player_path)
        self.closeCatalog()
                      
    def recordText( self, text, voice=None ):
        if voice != None and voice != self.voice:
            self.flushText()
            self.voice = voice
            
        self.text_segment = self.text_segment + " " + text
        
    def flushText( self ):                 
        if self.text_segment:
            self.recordTextTo(self.text_segment,"my_radio_show_", False, self.voice)
            self.text_segment = ""
                   
    def recordTextTo( self, text, mp3name, downsample=False, voice = "julie" ):
        chunk = os.path.join("/tmp",self.basename+"."+mp3name+str(self.sequence))
        codecs.open(chunk+".txt","w","utf-8","replace").write(nopunct(text))
        mp3path = os.path.join(self.music_path,"%s%d.mp3"% (mp3name,self.sequence))
#       cmd = ["/bin/bash","-c","espeak -f /tmp/%s.txt -w /tmp/%s.wav;lame -a /tmp/%s.wav %s" % (chunk,chunk,chunk,mp3path)]
#       cmd = ["/bin/bash","-c","text2wave -o '%s.wav' < '%s.txt';lame -m m -h '%s.wav' '%s'" % (chunk,chunk,chunk,mp3path)]
        number = 0
        parts = []
        for text_chunk in text.split("|"):
            if hasalnum(text_chunk) :
                part_name = chunk+"%d.wav"%(number)
                number = number + 1
                parts.append(part_name)
                text2wav(text_chunk,part_name,self.verbose, voice)
                
        if downsample:
            cmd = ["/bin/bash","-c","sox %s \"%s\"" % (" ".join(["\"%s\""%f for f in parts]),mp3path)]
        else:
            cmd = ["/bin/bash","-c","sox %s \"%s\"" % (" ".join(["\"%s\""%f for f in parts]),mp3path)]
        if self.verbose:
            subprocess.call(cmd)
        else:
            subprocess.call(cmd,
            stdin = open("/dev/null","r"),
            stdout = open("/dev/null","w"),
            stderr = open("/dev/null","w"),
            close_fds = True)
              
        if not self.debug:
            safeRemove( "%s.txt" % (chunk))
            safeRemove( "%s.wav" % (chunk))
            for p in parts:
                safeRemove( p )
        track = {}
        track['path'] = mp3path
        track['title'] = " ".join(" ".join(text.split("\n")).split(" ")[:10])
        track['album'] = self.basename
        track['artist'] = "RadioMe Announcer"
        track['tracknumber'] = str(self.sequence)
        track['skip_when_shuffling'] = '0x01'
#        self.db.addtrack( track )
        self.playlist.addtrack(track)
        self.sequence += 1
        return

def main( options, args ):
    """ main driver for playlist annotation generator """
        
    user_path = "~"
    if args:
        user_path = args[0]

    if options.verbose:
        print "user path", user_path
        
    # discover the catalog and save it if the option is set
    if options.discover:
        if options.verbose:
            print "Searching home directory for music files"
        catalog = music_catalog.get_catalog(verbose=options.verbose,path=user_path)
        catalog.discover()
        catalog.save()
        return 0
        
    # save the default config if requested
    if options.config:
        if options.verbose:
            print "Saving default configuration"
        conf = config.get_config(user_path)
        conf.save()
        return 0
                                                 
    # load information for user from config file
    conf = config.get_config(user_path)
    data_path = conf.getKey(config.DATA_PATH)
    music_index = conf.getKey(config.MUSIC_INDEX)
    template = conf.getKey(config.TEMPLATE)
    player_location = conf.getKey(config.PLAYER_LOCATION)
    music_path = conf.getKey(config.MUSIC_PATH)           
    (weather_provider, weather_rss) = conf.getKey(config.WEATHER_PROVIDER).split(",",1)
    (news_provider, news_rss) = conf.getKey(config.NEWS_PROVIDER).split(",",1)
    (calendar_provider, calendar_path) = conf.getKey(config.CALENDAR_PROVIDER).split(",",1)
    web_root = conf.getKey(config.WEB_ROOT)
    web_server = conf.getKey(config.WEB_SERVER)
    web_sync = conf.getKey(config.WEB_SYNC)
    
    my_radio = MyRadio( user_path,
                        data_path,
                        music_index, 
                        music_path,
                        weather_provider,
                        weather_rss,
                        news_provider,
                        news_rss,
                        calendar_provider,
                        calendar_path,
                        options.verbose,
                        options.debug,
                        options.filter,
                        web_root,
                        web_server,
                        web_sync,
                        "julie" )
    
    
    my_radio.produceShow(player_location, template, sync= options.sync)
    # save updated stats for this show
    get_profile(user_path).save()
    return 0

if __name__ == '__main__':
    try:
        parser = OptionParser(usage="usage: %prog [options][user_path]", description="Playlist annotation generator prototype, generates playlist and annotations.")
        parser.add_option("-d","--discover", dest="discover", action="store_true", default=False, help="disover music on this computer and save catalog")
        parser.add_option("-c","--config", dest="config", action="store_true", default=False, help="save default config to config file")
        parser.add_option("-v","--verbose", dest="verbose", action="store_true", default=False, help="turn on debug output")
        parser.add_option("-s","--sync", dest="sync", action="store_true", default=False, help="sync to player")
        parser.add_option("-D","--debug", dest="debug", action="store_true", default=False, help="debug generation of sound files")
        parser.add_option("-f","--filter", dest="filter", default=None, action="append",help="filter tracks based on field:regex")
    
        (options,args) = parser.parse_args()
    
        retval = main(options,args)
        if retval:
            sys.exit(retval)
    except Exception,e:
        print >>sys.stderr,"============================================================================================"
        traceback.print_exc(file=sys.stderr)
        print >>sys.stderr,"============================================================================================"
        sys.exit(1)
