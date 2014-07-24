#!/usr/local/bin/python

from bs4 import BeautifulSoup
from cStringIO import StringIO
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders
from functools import partial
from shutil import move
import commands
import ConfigParser
import hashlib
import logging
import os
import requests
import smtplib
import sys
import time
import unicodedata

# Set up logging
logging.basicConfig(filename=os.path.join(os.path.dirname(__file__), 'debug.log'), level=logging.DEBUG)

# Set up some variables
outbound_email = ''
outbound_un = ''
outbound_pw = ''

# Import private untracked credentials; continue anyway if not found, but email won't work
try:
    from private import *
except ImportError:
    pass

# Email results
def send_mail(send_from, send_to, subject, text, files=[], server="localhost"):
    assert type(send_to)==list
    assert type(files)==list

    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach( MIMEText(text) )

    for f in files:
        part = MIMEBase('application', "octet-stream")
        part.set_payload( open(f,"rb").read() )
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(f))
        msg.attach(part)

    smtp = smtplib.SMTP(server)
    smtp.starttls()
    smtp.login(outbound_un, outbound_pw)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.close()

# Compute MD5 hash
def md5sum(filename):
    with open(filename, mode='rb') as f:
        d = hashlib.md5()
        for buf in iter(partial(f.read, 128), b''):
            d.update(buf)
    return d.hexdigest()

# Parse config file
def ConfigSectionMap(section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1

# Retrieving our variables from our config file
Config = ConfigParser.ConfigParser()
Config.read("config.cfg")

e_min_price=ConfigSectionMap("SearchParams")['minprice']
e_max_price=ConfigSectionMap("SearchParams")['maxprice']
e_bedroom_no=ConfigSectionMap("SearchParams")['bedroomno']
e_housing_type=ConfigSectionMap("SearchParams")['housingtype']
e_cats=ConfigSectionMap("SearchParams")['cats']
e_dogs=ConfigSectionMap("SearchParams")['dogs']
e_pics=ConfigSectionMap("SearchParams")['pics']
e_limit=ConfigSectionMap("SearchParams")['limit']

# Housing type dict
typeDict = {
        0: "all types",
        1: "apartments",
        2: "condos",
        3: "cottages/cabins",
        4: "duplexes",
        5: "flats",
        6: "houses",
        7: "in-laws",
        8: "lofts",
        9: "townhouses",
        10: "manufactured",
        11: "assisted living",
        12: "land"
        }

dogDict = {
        "y": "wooof",
        "Y": "wooof",
        "n": "",
        "N": ""
        }

catDict = {
        "y": "purrr",
        "Y": "purrr",
        "n": "",
        "N": ""
        }

picDict = {
        "y": "ON",
        "Y": "ON",
        "n": "OFF",
        "N": "OFF"
        }


tmp = os.path.join(os.path.dirname(__file__), 'tmp/results')
res = os.path.join(os.path.dirname(__file__), 'results')

with open(tmp, 'w') as f:

    # Get unicode response from Craigslist GET request
    # Need to add 1 to maxprice because it seems to be "up to" instead of "up to and including"
    r = requests.get("http://santabarbara.craigslist.org/search/apa?minAsk="+str(e_min_price)+"&maxAsk="+str(e_max_price)+"&bedrooms="+str(e_bedroom_no)+"&pets_cat="+str(e_cats)+"&pets_dog="+str(e_dogs)+"&hasPic="+str(e_pics))

    # Normalize unicode data and convert to ASCII to avoid weirdness
    s = unicodedata.normalize('NFKD', r.text).encode('ascii', 'ignore')

    # List of locations to ignore
    ignored = ["LOMPOC", "SANTA MARIA", "GOLETA", "ISLA VISTA", "CARPINTERIA", "CARLSBAD", "OXNARD", "CLEMENTE", "BUELLTON", "VANDENBERG", "BAKERSFIELD", "LOS ANGELES", "SOLVANG", "SANTA YNEZ", "THE SWEEPS", "SOLVANG-SANTA YNEZ", "OJAI", "NIPOMO", "ABREGO RD", "WILLOW SPRINGS", "CAMARILLO", "EAST END"]

    # Today's month/day, i.e. 'May 16'
    date = time.strftime("%B %d")

    # Use BeautifulSoup to parse HTML data
    soup = BeautifulSoup(s)
    ban = soup.find('span', 'daybubbles')
    content = soup.find('div', 'content')
    ads = content.findAll('p', 'row', limit=int(e_limit))

    # Write the results out to a file
    f.write("Searching for rooms between $"+str(e_min_price)+" and $"+str(e_max_price)+" with "+str(e_bedroom_no)+"+ bedrooms\n")
    if(catDict[e_cats])=='purrr':
        f.write("Cats are ALLOWED\n")
    else:
        f.write("Cats may not be allowed\n")
    if(dogDict[e_dogs])=='wooof':
        f.write("Dogs are ALLOWED\n")
    else:
        f.write("Dogs may not be allowed\n")
    f.write("Housing type is set to "+typeDict[int(e_housing_type)]+"\n")
    f.write("Pictures are "+picDict[e_pics]+"\n")
    f.write("Showing up to "+str(e_limit)+" result(s)\n")
    f.write("\n\n")


    # Loop through each ad and prettify the info
    # Catch some exceptions since apparently these don't always work/Craigslist changes layout
    for ad in ads:
        try:
            date = unicodedata.normalize('NFKD', ban.text).encode('ascii', 'ignore')
        except:
            date = ""

        try:
            tagline = unicodedata.normalize('NFKD', ad.contents[3].a.text).encode('ascii', 'ignore')
        except:
            tagline = "(Title not available)"

        try:
            price = unicodedata.normalize('NFKD', ad.contents[3].find('span', 'price').text).encode('ascii', 'ignore')
        except:
            price = "(Price not available)"

        # For some reason this errors out if you let it collect all the ads on a page, yet still gets all the data
        try:
            loc = unicodedata.normalize('NFKD', ad.contents[3].find('span', 'pnr').small.text).encode('ascii', 'ignore')
        except:
            loc = "(Location not available)"

        if any(ignored_loc in loc.upper() for ignored_loc in ignored):
            pass
        else:
            # Write out to results
            #f.write(date+' - '+tagline+' - '+price+'\n')
            f.write(tagline+' - '+price+'\n')
            f.write(loc+'\n')
            for link in ad.findAll('a', limit=1):
                url = link.get('href')
                f.write('View ad on CL: http://santabarbara.craigslist.org/' + url +'\n')
            f.write("\n")

# Check MD5 and see if the temp file contains any new content
if os.path.isfile(res):
    prevmd5 = md5sum(res)
else:
    prevmd5 = ""
tmpmd5 = md5sum(tmp)

if tmpmd5 == prevmd5:
    # If the temp file is the same as the old file, don't bother emailing it
    # and get rid of the temp file
    if os.path.isfile(tmp):
        os.remove(tmp)
    logging.info(time.strftime("%m%d%y-%H%M%S: No new results"))
    sys.exit()
else:
    # If the temp file is different than the old file, email it to us,
    # remove the old file and replace it with the temp file
    if os.path.isfile(res):
        os.remove(res)
    move(tmp, res)
    logging.info(time.strftime("%m%d%y-%H%M%S: Wrote new file to ./results"))
    pass

with open(res, "r") as results:
    data = results.read()

send_mail(outbound_email, ["samlingx@gmail.com", "mattwr81@gmail.com"], "Craigslist Scrape Results "+time.strftime("%m/%d/%y %H:%M:%S"), data, [], "smtp.gmail.com:587")
