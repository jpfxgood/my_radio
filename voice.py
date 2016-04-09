import sys
import os
import urllib2
import urllib
import time
import hashlib

cached_words = 0
tts_words = 0

def wavcache_hash( text, voice ):
    h = hashlib.md5()
    h.update(voice)
    h.update(text.encode('utf-8','ignore'))
    return os.path.join("wavcache",h.hexdigest()+".wav")
    

def wavcache_get( text, voice ):
    hname = wavcache_hash( text, voice )
    if not os.path.exists("wavcache"):
        os.mkdir("wavcache")
        return ""

    if os.path.exists(hname):
        return hname
    else:
        return ""
     
def wavcache_put( text, voice, wavfile ):
    hname =  wavcache_hash( text, voice )
    open(hname, "wb").write(open(wavfile,"rb").read())
    
    
remote = False
local = "text2wave"
if remote:
    accountId = None
    password = None
    
    def parse_response( response ):
        retvals = {}
        parts = response.split()
        for p in parts:
            if "=" in p:
                namevalue = p.split("=",1)
                retvals[namevalue[0]] = namevalue[1][1:-1]
        return retvals
    
    def try_request( url, args=None, tries = 3):
        while tries:
            try:
                if args:
                    r = urllib2.urlopen(url,
                        urllib.urlencode (args))
                else:
                    r = urllib2.urlopen(url)
    
                response =  r.read()
                r.close()
                return response
            except:
                time.sleep(0.1)
                tries -= 1
        raise Exception("Failed after 3 attempts! ")
    
    def neospeech_request ( args ):
        return parse_response(try_request('https://tts.neospeech.com/rest_1_1.php',args))
    
    def text2wav( text, wavfile, verbose = False, voice="julie" ):
        global tts_words
        global cached_words
        wc = len(text.split(" "))
        cache_name = wavcache_get( text, voice )
        if cache_name:
            cached_words = cached_words + wc
            open(wavfile,"wb").write(open(cache_name,"rb").read())
            if verbose:
                print "cached_words, tts_words:",cached_words,tts_words
            return
            
        tts_words = tts_words + wc
        if verbose:
            print "cached_words, tts_words:",cached_words,tts_words
        
        voicemap = { "kate":"TTS_KATE_DB", "julie":"TTS_JULIE_DB", "paul":"TTS_PAUL_DB", "bridget":"TTS_KATE_DB" }
        ret = neospeech_request(((  'method','ConvertSimple'),
                        ('email','jpfx@jlgoodwin.com'),
                        ('accountId',accountId),
                        ('loginKey','LoginKey'),
                        ('loginPassword',password),
                        ('voice',voicemap[voice]),
                        ('outputFormat','FORMAT_WAV'),
                        ('sampleRate','16'),
                        ('text',text.encode('utf-8','ignore'))))
    
        if verbose:
            print ret
        if ret['resultCode'] != '0':
            raise Exception("ConvertSimple failed! "+str(ret)+" "+voice+" "+text)
    
        url = None
        conversionNumber = ret['conversionNumber']
        while not url:
            ret = neospeech_request(((  'method','GetConversionStatus'),
                            ('email','jpfx@jlgoodwin.com'),
                            ('accountId',accountId),
                            ('conversionNumber',conversionNumber)))
    
            if verbose:
                print ret
            if ret['resultCode'] != '0':
                raise Exception("GetConversionStatus failed! "+str(ret)+" "+voice+" "+text)
    
            if ret['statusCode'] == '5':
                raise Exception("Conversion failed! "+str(ret)+" "+voice+" "+text)
    
            if ret['statusCode'] == '4':
                url = ret['downloadUrl']
            else:
                time.sleep(0.1)
    
        if verbose:
            print url
    
        open(wavfile,"wb").write(try_request(url))
        wavcache_put(text,voice,wavfile)
else:              
    if local == "text2wave":
        import subprocess
        def text2wav( text, wavfile, verbose = False, voice="julie" ):
            global tts_words
            global cached_words
            wc = len(text.split(" "))
            voicemap = { "kate":"voice_rab_diphone", "julie":"voice_ked_diphone", "paul":"voice_kal_diphone", "bridget":"voice_kal_diphone" }
            cache_name = wavcache_get( text, voice )
            if cache_name:
                cached_words = cached_words + wc
                open(wavfile,"wb").write(open(cache_name,"rb").read())
                if verbose:
                    print "cached_words, tts_words:",cached_words,tts_words
                return
            tts_words = tts_words + wc
            if verbose:
                print "cached_words, tts_words:",cached_words,tts_words              
            open(wavfile+".txt","w").write(text.encode('utf-8','ignore'))
            cmd = ["/bin/bash","-c","text2wave -o '%s' -eval '(%s)'< '%s.txt'" % (wavfile, voicemap[voice], wavfile)]
            if verbose:
                ret = subprocess.call(cmd)
            else:
                ret = subprocess.call(cmd,
                stdin = open("/dev/null","r"),
                stdout = open("/dev/null","w"),
                stderr = open("/dev/null","w"),
                close_fds = True)
#            ret =  ttsapi.toSpeech( "james-mediacenter", text.encode('utf-8','ignore'), voicemap[voice], wavfile )
            if verbose:
                print ret, voicemap[voice], voice, wavfile
            wavcache_put(text,voice,wavfile)
            
    else:
        import ttsapi
        def text2wav( text, wavfile, verbose = False, voice="julie" ):
            global tts_words
            global cached_words
            wc = len(text.split(" "))
            voicemap = { "kate":100, "julie":100, "paul":101, "bridget":500 }
            cache_name = wavcache_get( text, voice )
            if cache_name:
                cached_words = cached_words + wc
                open(wavfile,"wb").write(open(cache_name,"rb").read())
                if verbose:
                    print "cached_words, tts_words:",cached_words,tts_words
                return
            tts_words = tts_words + wc
            if verbose:
                print "cached_words, tts_words:",cached_words,tts_words
            ret =  ttsapi.toSpeech( "james-mediacenter", text.encode('utf-8','ignore'), voicemap[voice], wavfile )
            if verbose:
                print ret, voicemap[voice], voice, wavfile
            wavcache_put(text,voice,wavfile)
    
if __name__ == '__main__':
    text2wav("This is a my radio test output!", "bridget_test.wav", True, "bridget")
    text2wav("This is a my radio test output!", "paul_test.wav", True, "paul")
    text2wav("This is a my radio test output!", "julie_test.wav", True, "julie")
    text2wav("This is a my radio test output!", "kate_test.wav", True, "kate")
