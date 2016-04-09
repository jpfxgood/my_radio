#!/usr/bin/python
import xml.sax as sax
import xml.sax.saxutils as saxutils
import xml.sax.handler as handler
from optparse import OptionParser
import sys
from bz2 import BZ2File
import pprint
import mwlib
from mwlib.refine.compat import parse_txt
from mwlib.refine import core
from mwlib.parser import nodes
import re
import codecs
import os
import string
import time
import threading

music_re = re.compile(r"(\{\{Infobox\s+)(musical artist|Album)")
                            
def extractText( node, text = None, level = 0 ):
    top = False
    if text == None:
        text = []
        top = True   
                    
    tag = None
    etag = None
    if isinstance(node,nodes.Paragraph):
        tag = "<Paragraph>"
        etag = "</Paragraph>"
    elif isinstance(node,nodes.CategoryLink):
        tag = "<Category>"
        etag = "</Category>"
    elif isinstance(node,nodes.Section):
        tag = "<Section>"
        etag = "</Section>"
    elif isinstance(node,(nodes.Ref,nodes.NamespaceLink, nodes.InterwikiLink, nodes.LangLink)):
        return
    elif isinstance(node,nodes.TagNode) and node.tagname == "ref":
        return
        
    if tag:
        text.append("\n%s%s\n"%(" "*level,tag))
            
    try:
        if len(node.children):
            for child in node.children:
                extractText(child, text, level+1 )
        elif node.text:
            text.append(saxutils.escape(node.text))
        elif node.target:
            text.append(saxutils.escape(node.target))
    except Exception, e:
        text.append("Error"+str(e))
        
    if etag:
        text.append("\n%s%s\n"%(" "*level,etag))
            
    if not level:
        return "".join(text)
    else:
        return
                       
def striptags( string, rep= " " ):
    return re.sub("(?s)<.*?>",rep,string)
    
def infobox_end( string, pos ):
    intag = 1
    while pos+1 < len(string):
        if string[pos] == "}" and string[pos+1] == "}":
            intag -= 1
        elif string[pos] == "{" and string[pos+1] == "{":
            intag += 1
            pos += 1
        if not intag:
            break   
        pos += 1
    else:
        return -1
    return pos

def stripmacros( string, rep = "" ):
    return re.sub("(?s)\{\{.*?\}\}",rep,string)
    
def nopunct( instr ):
    retstr = ""
    for k in range(0,len(instr)):
        if not instr[k] in string.punctuation:
            retstr += instr[k]
    return retstr

def extractPage( wiki_text_n, path, wiki_text, verbose = False ):
    try:
        page = extractText(parse_txt(wiki_text))
        music_info = music_re.search(page)
        if music_info:
            music_info_end = infobox_end(page,music_info.end())
            if music_info_end > 0:
                infobox = page[music_info.start()+2:music_info_end]
                if verbose:
                    print "Page:",wiki_text_n
                    print "Infobox:",infobox
                infobox = "".join(infobox.split("\n"))
                infobox = "".join(infobox.split("\r"))
                infobox = stripmacros(infobox," ")
                if verbose:
                    print "Infobox 1:",infobox
                infobox = infobox.split("|")
                if verbose:
                    for ib in infobox:
                        print "Line: [%s]\n"%(ib)
                attrs = "<Metadata MyRadioType=\"" + music_info.group(2) + "\" "
                ibattrs = {}
                for info in infobox:
                    item = info.split("=",1)
                    if len(item) == 2:
                        key = nopunct(item[0]).strip().replace(" ","_")
                        value = item[1].strip()
                        if value.endswith("}}"):
                            value = value[:-2]
                        ibattrs[key] = saxutils.quoteattr(striptags(saxutils.unescape(value),","))
                for (key,value) in ibattrs.items():
                    attrs += " %s=%s"%(key,value)
                attrs += "/>\n"
                if verbose:
                    print "Extracting:",attrs
                page = page[:music_info.start()] + page[music_info_end:]
                page = "<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n<Document>\n" + attrs + page + "</Document>\n"
                page = stripmacros(page)
                codecs.open(os.path.join(path,"%08d.xml"%(wiki_text_n)),"w","utf-8","replace").write(page)
    except Exception, e:  
        if verbose:
            print "Error at %d was %s"%(wiki_text_n,str(e))
        codecs.open(os.path.join(path,"%08d.raw"%(wiki_text_n)),"w","utf-8","replace").write(wiki_text)
        
if __name__ == "__main__":
    wiki_text = codecs.open(sys.argv[1],"r","utf-8","replace").read()
    extractPage(0,".",wiki_text,True)
