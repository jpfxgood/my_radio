#!/usr/bin/python

import xml.sax as sax

class MyHandler (sax.handler.ContentHandler):
    def startElement(self, name, attrs):
        print name, attrs.items()
        
    def characters(self,content):
        print content
        
sax.parse("template.xml", MyHandler())
