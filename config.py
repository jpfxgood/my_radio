#!/usr/bin/python
# Copyright 2009 James P Goodwin prototype for automatic playlist
# audio annotation

import os
import codecs

# keys for configuration
CATALOG_TYPE = "catalog_type"
CATALOG_NAME = "catalog_name"
PLAYER_LOCATION = "player_location"
DATA_PATH = "data_path"
TEMPLATE = "template"
MUSIC_INDEX = "music_index"
MUSIC_PATH = "music_path"
NEWS_PROVIDER = "news_provider"
WEATHER_PROVIDER = "weather_provider"
CALENDAR_PROVIDER = "calendar_provider"
WEB_ROOT= "web_root"
WEB_SERVER= "web_server"
WEB_SYNC= "web_sync"

# constants for config fields
# constants for catalog_type
MP3_CATALOG = "MP3"
IPOD_CATALOG = "IPOD"

profiles = {}      
configs = {}

def get_profile(path="~"):
    """ factory to return a profile object for the current user to store data about shows generated """
    global profiles
    profile = profiles.get(path,None)
    if not profile:
        profile = InitFileConfig(os.path.join(path,".myradioprofile"), {} )
        profiles[path] = profile
    return profile
    
def get_config(path="~"):
    """ factory to return a config object for the current user """
    global configs
    config = configs.get(path,None)
    if not config:
        config = InitFileConfig( os.path.join(path,".myradioconfig"), {    CATALOG_TYPE:MP3_CATALOG,
                                                    CATALOG_NAME: os.path.join(path,".myradiocatalog"),
                                                    PLAYER_LOCATION: "/media/9C5C-E9A6/Music",
                                                    DATA_PATH: "/data/music_extract",
                                                    TEMPLATE: "template.xml",
                                                    MUSIC_INDEX: "music_extract.idx",
                                                    MUSIC_PATH: os.path.join(path,"Music"),
                                                    NEWS_PROVIDER: "boston dot com,http://syndication.boston.com/news?mode=rss_10",
                                                    WEATHER_PROVIDER: "weather dot com,http://rss.weather.com/weather/rss/local/01915?cm_ven=LWO&cm_cat=rss&par=LWO_rss",
                                                    CALENDAR_PROVIDER: "google calendar,%s"%os.path.join(path,"onlinecalendar.ics"),
                                                    WEB_ROOT: "/var/www",
                                                    WEB_SERVER: "http://james-server:20080",
                                                    WEB_SYNC: "false" } )
        configs[path] = config
    return config
    
class Config:
    """ base class for configuration implementations """
    def __init__(self, name, defaults = {} ):
        pass
        
    def getKey( self, key ):
        pass
        
    def setKey( self, key, value ):
        pass
        
    def delKey( self, key ):
        pass
        
    def save( self ):
        pass
        
    def reset( self ):
        pass
        
    def delete( self ):
        pass
        
    

class InitFileConfig ( Config ):
    """ implementation of configuration based on properties file in an ini file """
    def __init__(self, name, defaults = {} ):
        """ create or load configuration """
        self.defaults = defaults
        self.filename = os.path.expanduser(name)+".ini"
        self.conf = {}
        self.reset()
        if os.path.exists(self.filename):
            self.load()
            
    def load( self ):
        """ load the configuration from the ini file """
        ini = codecs.open(self.filename,"r","utf-8",errors="replace",buffering=0)
        for l in ini:
            l = l.strip()
            if l:
                (name,value) = l.split("=",1)
                self.conf[name.strip()] = value.strip()
        ini.close()
        
    def reset( self ):
        """ reset the configuration to defaults """
        self.conf = self.defaults
        
    def getKey( self, key ):
        """ look up a key in the config """
        if key in self.conf:
            return self.conf[key]
        else:
            return None
        
    def setKey(self, key, value ):
        """ set a key in the config """
        self.conf[key] = value
        
    def delKey(self, key ):
        """ delete a key from the config """
        if key in self.conf:
            del self.conf[key]
            
    def save( self ):
        """ write out the config file with changes """
        ini = codecs.open(self.filename,"w","utf-8",errors="replace",buffering=0)
        for (name,value) in self.conf.items():
            print >>ini, name, "=", value
        ini.close()
        
    def delete( self ):
        """ remove the ini file """
        if os.path.exists(self.filename):
            os.remove(self.filename)
