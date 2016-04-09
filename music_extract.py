import sys
from xml.sax import parse, ContentHandler
import re
import os

music_re = re.compile(r"(\{\{Infobox\s+)(musical artist|Album)")
name_re = re.compile(r"([Nn]ame\s+\=)(.*)\n")
artist_re = re.compile(r"([Aa]rtist\s+\=)(.*)\n")
tag_re = re.compile(r"(\{\{|\[\[\[|\]\]\]|\[\[|\}\}|\]\]|\[|\]|\n|\||'''|''|===|==|<.*?>)")

class myCH( ContentHandler):

    def __init__(self):
        self.inPage = False
        self.inText = False
        self.collect = ""
        self.numpage = 0
        self.allpages = 0
        if not os.path.exists("music_extract"):
            os.mkdir("music_extract")

    def startElement(self,name,attrs):
        if name == "page":
            self.allpages = self.allpages + 1
            if not self.allpages % 1000:
                print self.allpages,self.numpage
            self.inPage = True
            self.inText = False
        elif self.inPage and name == "text":
            self.inText = True

    def endElement(self,name):
        if name == "page":
            self.inPage = False
            match = music_re.search(self.collect)
            if match:
                outfile = open("./music_extract/%08d.txt" % self.numpage, "w")
                self.numpage = self.numpage + 1
                kind = match.groups()[1]
                if kind.endswith("artist"):
                    kind = "Artist"
                elif kind.endswith("Album"):
                    kind = "Album"
                outfile.write(kind.encode("utf_8"))
                outfile.write("\n")
                name = name_re.search(self.collect)

                artist_name = ""
                if kind == "Album":
                    artist = artist_re.search(self.collect)
                    if artist:
                        artist_name = artist.groups()[1]

                if name:
                    title = name.groups()[1]
                    title = title.strip()
                    outfile.write(title.encode("utf_8"))
                    outfile.write("\n")
                    if kind == "Album":
                        outfile.write(artist_name.encode("utf_8"))
                        outfile.write("\n")
                    inTag = 0
                    inMarkup = 0
                    markup = []
                    for part in tag_re.split(self.collect):
                        part = part.strip()
                        if part == "[[" or part == "[[[" or part == "[":
                            inMarkup = inMarkup + 1
                            continue
                        elif part == "]]" or part == "]]]" or part == "]":
                            inMarkup = inMarkup - 1
                            if not inMarkup:
                                if markup:
                                    text = markup[-1]
                                    if text.startswith("http:"):
                                        text = ""
                                    elif text.startswith("en:"):
                                        text = text[3:]
                                    elif re.match("\w+\:",text):
                                        text = ""
                                    if text:
                                        outfile.write((text+" ").encode("utf_8"))
                                    markup = []
                            continue
                        elif part == "{{":
                            inTag = inTag + 1
                            continue
                        elif part == "}}":
                            inTag = inTag - 1
                            continue
                        elif part in ("'''","''","===","=="):
                            continue
                        elif part.startswith("<"):
                            continue

                        if inTag:
                            continue
                        elif inMarkup:
                            markup.append(part)
                            continue
                        elif part:
                            outfile.write((part+" ").encode("utf_8"))
                    outfile.write("\n")
            self.collect = ""
            self.inText = False
        elif name == "text":
            self.inText = False

    def characters(self,content):
        if self.inText:
            self.collect = self.collect + content


parse(sys.argv[1],myCH())
