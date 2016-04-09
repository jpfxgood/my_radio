#!/usr/bin/python
import datetime
import dateutil
from dateutil import parser
import pprint
import os

today = datetime.datetime.now()
tomorrow = today + datetime.timedelta(days=1)
today = today.replace(tzinfo=None)
tomorrow = tomorrow.replace(tzinfo=None)

todaydate = today.date()
tomorrowdate = tomorrow.date()

def parseRrule( rule ):
    parts = rule.split(";")
    rule = {}
    for k in parts:
        (name, value) = k.split("=")
        rule[name] = value
    return rule

def parseVobj( scal, name ):
    objs = {}
    name = None
    value = None
    while True:
        line = scal.readline()
        if line == None:
            break
        if line[0] == ' ':
            line = line.rstrip()
            if objs.get(name,None):
                objs[name].append(line[1:])
            else:
                objs[name] = [line[1:]]
            continue

        tuple = line.split(":",1)
        if len(tuple) == 2:
            name = tuple[0]
            value = tuple[1]
        else:
            name = tuple[0]
            value= ""
        name = name.strip()
        value = value.strip()
        if name.find(";"):
            parts = name.split(";",1)
            if len(parts) > 1:
                name = parts[0]
        if name == "BEGIN":
            if objs.get(value,None):
                objs[value].append(parseVobj(scal, value))
            else:
                objs[value] = [parseVobj(scal,value)]
        elif name == "END":
            break
        else:
            if value:
                if objs.get(name,None):
                    objs[name].append(value)
                else:
                    objs[name] = [value]
    return objs

def parse( infile ):
    infile = os.path.expanduser(infile)
    scal = open(infile,"r")
    objs = {}
    while True:
        line = scal.readline()
        if line == None:
            break
        line = line.strip()
        if not line:
            break
        (name,value) = line.split(":",1)
        if name == 'BEGIN' and value == 'VCALENDAR':
            objs[value] = parseVobj(scal, value)
        else:
            break
    return objs

def getP(cal,prop):
    return cal.get(prop,[])

def matchDate( dtstart,dtend,rrule,today, tomorrow ):
    if not rrule:
        if today >= dtstart and tomorrow <= dtend:
            return True
    else:
        freq = rrule['FREQ']
        if freq == 'DAILY':
            until = rrule.get('UNTIL',None)
            if until:
                until = parser.parse(until)
                if today >= dtstart and today <= until:
                    return True
                else:
                    return False
            else:
                return True
        elif freq == 'WEEKLY':                   
            interval = 1
            if 'INTERVAL' in rrule:
                interval = int(rrule['INTERVAL'])
            byday = rrule['BYDAY']
            days = byday.split(",")
            byday = []
            for d in days:
                byday.append( ["MO","TU","WE","TH","FR","SA","SU"].index(d) )
                
            if today > dtstart:
                if today.weekday() in byday or tomorrow.weekday() in byday:
                    if interval == 1:
                        return True
                    diff = today - dtstart
                    if not ((diff.days+7)/7)%interval:
                        return True
                    else:
                        return False
            elif today == dtstart:
                return True
            else:
                return False
        elif freq == 'YEARLY':
            # TODO: yearly might be needed, but it's only timezones right now
            pass
        else:
            return False

def get_appointments( infile ):
    apps = []
    cal = parse( infile )

    for ve in cal['VCALENDAR']['VEVENT']:
        rrule = getP(ve,'RRULE')
        if rrule:
            rrule = parseRrule( "".join(rrule) )
        dtstart_str = getP(ve,'DTSTART')[0]
        dtend_str = getP(ve,'DTEND')[0]
        dtstart = parser.parse(dtstart_str).replace(tzinfo=None)
        dtend = parser.parse(dtend_str).replace(tzinfo=None)
        if matchDate(dtstart,dtend,rrule,today,tomorrow):
            apps.append(ve)

    return apps

def time_script( time_obj ):
    hours = { 0:"twelve",1:"one",2:"two",3:"three",4:"four",5:"five",6:"six",7:"seven",8:"eight",9:"nine",10:"ten",11:"eleven" }
    minutes = { 0:"",
                1:"one",
                2:"two",
                3:"three",
                4:"four",
                5:"five",
                6:"six",
                7:"seven",
                8:"eight",
                9:"nine",
                10:"ten",
                11:"eleven",
                12:"twelve",
                13:"thirteen",
                14:"fourteen",
                15:"fifteen",
                16:"sixteen",
                17:"seventeen",
                18:"eighteen",
                19:"nineteen",
                20:"twenty",
                30:"thirty",
                40:"forty",
                50:"fifty" }
    rets = hours[time_obj.hour % 12]
    if time_obj.minute < 10:
        if not time_obj.minute:
            rets = rets + " oh clock"
        else:
            rets = rets + " oh " + minutes[time_obj.minute]
    elif time_obj.minute < 20:
        rets = rets + " " +  minutes[time_obj.minute]
    elif time_obj.minutes >= 20:
        high = (time_obj.minute / 10)*10
        low = time_obj.minute % 10
        rets = rets + " " + minutes[high]
        if low:
            rets = rets + " " + minutes[low]

    return rets

def to_script( ap ):                   
    start_time = time_script(parser.parse(getP(ap,'DTSTART')[0]).time())
    if getP(ap,'SUMMARY'):
        summary = getP(ap,'SUMMARY')[0]
    else:
        summary = "An appointment."
        
    if getP(ap,'DESCRIPTION'):
        description = getP(ap,'DESCRIPTION')[0]
    else:
        description = None
                          
    if description:
        rs = "You have an appoitment at %s today about %s. The full description is: %s." % (start_time, summary, description)
    else:
        rs = "You have an appoitment at %s today about %s." % (start_time, summary )
        
    return rs

def get_calendar( infile = "~/.evolution/calendar/local/system/calendar.ics", verbose=False ):
    script = ""

    for ap in get_appointments( infile ):
        script = script + to_script(ap) + "\n"
   
    if verbose:
        print "Calendar Script",script
    return script
