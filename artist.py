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

class Artist:
    def __init__(self,
          alias = None      ,
          assoc = None      ,
          backgnd = None    ,
          birthname = None  ,
          born = None       ,
          caption = None    ,
          died = None       ,
          genre = None      ,
          image = None      ,
          instrument = None ,
          label = None      ,
          members = None    ,
          name = None       ,
          nname = None      ,
          origin = None     ,
          pastmemb = None   ,
          url = None        ,
          voice = None      ,
          years = None      ,
          xml = None,
          id = None ):
        self.alias = alias
        self.assoc = assoc
        self.backgnd = backgnd
        self.birthname = birthname
        self.born = born
        self.caption = caption
        self.died = died
        self.genre = genre
        self.image = image
        self.instrument = instrument
        self.label = label
        self.members = members
        self.name = name
        self.nname = nname
        self.origin = origin
        self.pastmemb = pastmemb
        self.url = url
        self.voice = voice
        self.years = years
        self.xml = xml
        self.id = id

class ParaHandler( handler.ContentHandler ):
    def __init__(self,verbose = False):
        handler.ContentHandler.__init__(self)
        self.paras = []
        self.curpara = ""
        self.cursection = ""
        self.inpara = False
        self.insection = False
        
    def getParas( self ):
        return self.paras
        
    def startElement( self,name,attrs):
        self.curpara = ""     
        if name == "Section":
            self.insection = True
            self.cursection = ""
        else:
            self.insection = False
        if name == "Paragraph":
            self.inpara = True
        else:
            self.inpara = False
                    
        
    def characters( self, content):
        if self.inpara:
            self.curpara += content
        elif self.insection:
            self.cursection += content
        
        
    def endElement( self,name):
        if name == "Paragraph":
            self.paras.append((self.cursection, self.curpara))
        elif name == "Section":
            self.insection = False
            self.cursection = ""

conn = MySQLdb.connect( host="localhost", user=None, passwd=None, db="MYRADIO", charset="utf8" )
cursor = conn.cursor()

def fetch_artist( name ):
    sel = "SELECT * FROM MYRADIO.ARTISTS WHERE NAME = '%s'"%(normalize(name))
    cursor.execute(sel)
    return [ Artist(*f) for f in cursor.fetchall() ]

def fetch_paragraphs( name ):
    alist = fetch_artist( name )
    paras = []          
    handler = ParaHandler()
    for a in alist:
        xml = sax.parse(open(a.xml), handler)
        
    return handler.getParas()
    
if __name__ == '__main__':

    for a in fetch_artist("Bud Powell"):
        print a.nname,a.xml
        
    for p in fetch_paragraphs("Bud Powell"):
        print p
