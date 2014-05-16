import requests
from HTMLParser import HTMLParser
import re
import itertools
import time
import unicodedata
from bs4 import BeautifulSoup

# Boolean for determining if inside <p> tags
inP = False

# Python equivalent of cURL to Craigslist specifying a specific search criteria:
# <= 2300/mo, 2+ bedrooms, cats ok
r = requests.get("http://santabarbara.craigslist.org/search/apa?maxAsk=2300&bedrooms=2&pets_cat=purrr")

# Normalize the request data to normal ASCII and ignore weird unicode characters that cause issues
s = unicodedata.normalize('NFKD', r.text).encode('ascii', 'ignore')

# Ignore results from these locations
ignored = ["LOMPOC", "SANTA MARIA", "GOLETA", "ISLA VISTA", "CARPINTERIA", "CARLSBAD", "OXNARD", "CLEMENTE", "BUELLTON", "VANDENBERG", "BAKERSFIELD", "LOS ANGELES"]

# Today's month/day
date = time.strftime("%B %d")

# Our parser class
class Parser(HTMLParser):

    # Handle start/end tags and data in the middle
    def handle_starttag(self, tag, attrs):
        global inP
        if tag.upper() == "P":
            inP = True
    def handle_endtag(self, tag):
        global inP
        if tag.upper() == "P":
            inP = False
    def handle_data(self, data):
        global inP
        if inP:
            if re.match(r'^\s*$', data):
                # Ignore blank lines with no data
                pass
            #elif not any(ignored_loc in data.upper() for ignored_loc in ignored):
            else:
                for line in data.split('\n'):
                    #if line.startswith(date):
                    print line

# Run everything
parser = Parser()
parser.feed(s)
