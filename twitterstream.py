from __future__ import division
import sys
import oauth2 as oauth
import urllib2 as urllib
import json
from collections import defaultdict
import serial

access_token_key = <INSERT TOKEN KEY>
access_token_secret = <INSERT TOKEN SECRET>

consumer_key = <INSERT CONSUMER KEY>
consumer_secret = <INSERT CONSUMER SECRET>

_debug = 0

oauth_token = oauth.Token(key=access_token_key, secret=access_token_secret)
oauth_consumer = oauth.Consumer(key=consumer_key, secret=consumer_secret)

signature_method_hmac_sha1 = oauth.SignatureMethod_HMAC_SHA1()

http_method = "GET"

http_handler = urllib.HTTPHandler(debuglevel=_debug)
https_handler = urllib.HTTPSHandler(debuglevel=_debug)

'''
Construct, sign, and open a twitter request
using the hard-coded credentials above.
'''

def twitterreq(url, method, parameters):
    req = oauth.Request.from_consumer_and_token(oauth_consumer, token=oauth_token, http_method=http_method, http_url=url, parameters=parameters)
    req.sign_request(signature_method_hmac_sha1, oauth_consumer, oauth_token)
    headers = req.to_header()
    
    if http_method == 'POST':
        encoded_post_data = req.to_postdata()
    else:
        encoded_post_data = None
        url = req.to_url()
    opener = urllib.OpenerDirector()
    opener.add_handler(http_handler)
    opener.add_handler(https_handler)
    
    response = opener.open(url, encoded_post_data)
    
    return response

def fetchsamples(sent_file):
    # Create a dictionary of sentimental terms
    lexicon = defaultdict(int)
    for line in sent_file:
        term, emotion  = line.strip().split(",")  
        lexicon[term] = emotion

    # Establish serial connection
    ser = serial.Serial("/dev/tty.usbserial-A5012SCP", 9600)

    # Download Twitter stream
    url = "https://stream.twitter.com/1/statuses/sample.json"
    parameters = []
    response = twitterreq(url, "GET", parameters)
    
    count = 0

    fear = 0
    happy = 0
    ambiguous = 0
    shame = 0
    sadness = 0
    anger = 0
    surprise = 0
    zen = 0
    courage = 0

    fear_prev = 0
    happy_prev = 0
    ambiguous_prev = 0
    shame_prev = 0
    sadness_prev = 0
    anger_prev = 0
    surprise_prev = 0
    zen_prev = 0
    courage_prev = 0

    for line in response:
        tweet = json.loads(line.strip())
        tweet.setdefault("text",None) # Setting default value to None if the tweet doesn't have text
        txt = tweet["text"]
        if txt and tweet["user"]["lang"] == "en": # Only consider tweets containing text and coming from English-speaking users
            count += 1
            for term in txt.split():
                emo = lexicon[term]
                if emo in ["negative-fear", "anxiety"]:
                    fear += 1
                elif emo in ["compassion","love","joy","levity"]:
                    happy += 1
                elif emo in ["ambiguous-emotion","neutral-emotion",None]:
                    ambiguous += 1
                elif emo == "shame":
                    shame += 1
                elif emo in ["sadness","despair"]:
                    sadness += 1
                elif emo in ["ingratitude","general-dislike"]:
                    anger += 1
                elif emo in ["surprise","daze"]:
                    surprise += 1
                elif emo in ["humility","calmness"]:
                    zen += 1
                elif emo == "fearlessness":
                    courage += 1
                    
            if count == 2000:
                
                fear_deriv = abs(fear - fear_prev)
                happy_deriv = abs(happy - happy_prev)
                ambiguous_deriv = abs(ambiguous - ambiguous_prev)
                shame_deriv = abs(shame - shame_prev)
                sadness_deriv = abs(sadness - sadness_prev)
                anger_deriv = abs(anger - anger_prev)
                surprise_deriv = abs(surprise - surprise_prev)
                zen_deriv = abs(zen - zen_prev)
                courage_deriv = abs(courage - courage_prev)

                total = fear_deriv + happy_deriv + ambiguous_deriv + shame_deriv + sadness_deriv + anger_deriv + surprise_deriv + zen_deriv + courage_deriv

                print "fear: " + str(fear_deriv)
                print "happy: " + str(happy_deriv)
                print "ambiguous: " + str(ambiguous_deriv)
                print "shame: " + str(shame_deriv)
                print "sadness: " + str(sadness_deriv)
                print "anger: " + str(anger_deriv)
                print "surprise: " + str(surprise_deriv)
                print "zen: " + str(zen_deriv)
                print "courage: " + str(courage_deriv)

                red = int((fear_deriv*35 + happy_deriv*254 + ambiguous_deriv*28 + shame_deriv*250 + sadness_deriv*49 + anger_deriv*222 + surprise_deriv*230 + zen_deriv*255 + courage_deriv*153)/total)
                green = int((fear_deriv*139 + happy_deriv*204 + ambiguous_deriv*144 + shame_deriv*159 + sadness_deriv*130 + anger_deriv*45 + surprise_deriv*85 + zen_deriv*255 + courage_deriv*52)/total)
                blue = int((fear_deriv*69 + happy_deriv*92 + ambiguous_deriv*153 + shame_deriv*181 + sadness_deriv*189 + anger_deriv*38 + surprise_deriv*13 + zen_deriv*255 + courage_deriv*4)/total)

                print "red: " + str(red)
                print "green: " + str(green)
                print "blue: " + str(blue) + "\n"

                ser.write("%i,%i,%i\n" % (red, green, blue))

                total_prev = total
                fear_prev = fear
                happy_prev = happy
                ambiguous_prev = ambiguous
                shame_prev = shame
                sadness_prev = sadness
                anger_prev = anger
                surprise_prev = surprise
                zen_prev = zen
                courage_prev = courage

                # Reinitialize the values
                count = 0
                fear = 0
                happy = 0
                ambiguous = 0
                shame = 0
                sadness = 0
                anger = 0
                surprise = 0
                zen = 0
                courage = 0

if __name__ == '__main__':
    sent_file = open(sys.argv[1])
    fetchsamples(sent_file)