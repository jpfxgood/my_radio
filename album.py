#!/usr/bin/python
import xml.sax as sax
import xml.sax.handler as handler
from optparse import OptionParser
import sys
import pprint
import re
import codecs
import os
import MySQLdb
import traceback
from my_radio_module import normalize
from artist import ParaHandler

class Album:
    def __init__(self,
        artist=None,
        nartist=None,
        cover=None,
        genre=None,
        label=None,
        lastalbum=None,
        name=None,
        nname=None,
        nextalbum=None,
        producer=None,
        recorded=None,
        released=None,
        review=None,
        xml=None,
        id=None):
        self.artist=artist
        self.nartist=nartist
        self.cover=cover
        self.genre=genre
        self.label=label
        self.lastalbum=lastalbum
        self.name=name
        self.nname=nname
        self.nextalbum=nextalbum
        self.producer=producer
        self.recorded=recorded
        self.released=released
        self.review=review
        self.xml=xml
        self.id=id

conn = MySQLdb.connect( host="localhost", user=None, passwd=None, db="MYRADIO", charset="utf8" )
cursor = conn.cursor()

def fetch_album( name ):
    sel = "SELECT * FROM MYRADIO.ALBUMS WHERE NAME = '%s'"%(normalize(name))
    cursor.execute(sel)
    return [ Album(*f) for f in cursor.fetchall() ]
    
def fetch_album_by_artist( artist ):
    sel = "SELECT * FROM MYRADIO.ALBUMS WHERE ARTIST = '%s'"%(normalize(artist))
    cursor.execute(sel)
    return [ Album(*f) for f in cursor.fetchall() ]
    
def fetch_album_by_artist_and_name( artist, name ):
    sel = "SELECT * FROM MYRADIO.ALBUMS WHERE ARTIST = '%s' AND NAME='%s'"%(normalize(artist),normalize(name))
    cursor.execute(sel)
    return [ Album(*f) for f in cursor.fetchall() ]
    
def fetch_paragraphs( name, artist=None ):
                                       
    if not artist:
        alist = fetch_album( name )
    else:
        alist = fetch_album_by_artist_and_name( artist, name )
        
    paras = []          
    handler = ParaHandler()
    for a in alist:
        xml = sax.parse(open(a.xml), handler)
        
    return handler.getParas()
    
if __name__ == '__main__':
                                             
    test_album = None             
    print "============ Test fetch_album_by_artist ============"
    for a in fetch_album_by_artist("Bud Powell"):
        print a.nname,a.name,a.xml
        if not test_album:
            test_album = a.nname           
        print "======== Test fetch_paragraphs =========="
        for p in fetch_paragraphs(a.nname):
            print p
                                                         
    print "=========== test fetch_album_by_artist_and_name ========"
    for a in fetch_album_by_artist_and_name("Bud Powell",test_album):
        print a.nname,a.name,a.xml,a.nartist
