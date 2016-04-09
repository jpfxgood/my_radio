#!/usr/bin/python
import feedparser
import re
import pprint

def no_tags( text ):
    return re.sub(r"\<.*?\>","",text)

def do_xlate( text, xlate ):
    for (pat,rep) in xlate:
        text = re.sub(pat,rep,text)
    return text

def removecr( string, dropline=False ):
    lines = string.split("\n")
    if dropline:
        lines = lines[0:-1]
    return " ".join(lines)
    
def news_script( article = "Headline: ",
                 feed = "http://feeds.boston.com/boston/news",
                 filt = None,
                 xlate = None,
                 dropline = True ):
    d = feedparser.parse(feed)

    max_entries = 100
    script = ""
    for a in d.entries:
        if filt and not re.match(filt,a.title):
            continue
        script = script + article + removecr(a.title) + ".\n"
        script = script + removecr(a.summary,dropline) + ".\n"
        max_entries = max_entries -1
        if not max_entries:
            break
    if xlate:
        return do_xlate(no_tags(script),xlate)
    else:
        return no_tags(script)

def get_news( feed = "http://feeds.boston.com/boston/news",verbose=False):
    content = news_script(feed=feed,filt="(?!AD\:)",xlate=[("\&\#\d\d\d\d;",""),])
    return content

def get_weather(feed = 'http://rss.weather.com/weather/rss/local/01915?cm_ven=LWO&cm_cat=rss&par=LWO_rss',verbose=False):
    content = news_script( article = "",
                   feed = feed,
                   filt = r"Current Weather.*|Your Weekend.*|Your 10\-Day.*",
                   xlate = [(r"\&deg\;\s*F"," degrees fahrenheit "),
                            ("Mon[:\s]","Monday "),
                            ("Tue[:\s]","Tuesday "),
                            ("Wed[:\s]","Wednesday "),
                            ("Thu[:\s]","Thursday "),
                            ("Fri[:\s]","Friday "),
                            ("Sat[:\s]","Saturday "),
                            ("Sun[:\s]","Sunday "),
                            ("\%"," percent "),
                            ("\&"," and "),
                            ("/",""),
                            ("PM\s"," evening "),
                            ("AM\s"," morning "),
                            (r"For .* details[\.\?]+",""),
                            (r"[\-]+","")],
                    dropline = False )
                            
    return content
    
if __name__ == '__main__':
    print get_news()
    print get_weather()
