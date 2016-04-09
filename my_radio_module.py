#!/usr/bin/python

import os

def hasalnum( name ):
    """ true if there are text or numbers """
    for c in name:
        if c.isalnum():
            return True
    return False

def nopunct( name ):
    """ remove the punctuation from a string """
    retname = ""
    inSpace = False
    for c in name:
        if c.isspace():
            if inSpace:
                continue
            inSpace = True
            retname = retname + " "
        elif c.isalnum() or c in [".",",","!","/",":","-","'","%"]:
            inSpace = False
            retname = retname + c
    return retname

def normalize( name ):
    """ normalize names to be uppercase and having no punctuation and converting runs of spaces to singe underscores """
    name = name.strip().upper()
    retname = ""
    inSpace = False
    for c in name:
        if c.isspace():
            if inSpace:
                continue
            inSpace = True
            retname = retname + "_"
        elif c.isalnum():
            inSpace = False
            retname = retname + c
    return retname

def escape( text ):
    """ escape characters that have meaning in regular expressions """
    ret = ""
    for k in text:
        if k in [".","\\","?","*","[","]","(",")","+"]:
            ret = ret + "\\" + k
        else:
            ret = ret + k
    return ret

def safeRemove( path ):
    if os.path.exists(path):
        os.remove(path)
