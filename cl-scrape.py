from bs4 import BeautifulSoup
from cStringIO import StringIO
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders
from functools import partial
from shutil import move
import argparse
import commands
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

# Take some command line arguments
parser = argparse.ArgumentParser(description="Search Craigslist apartment listings and get the results emailed to you.")
parser.add_argument("-m", "--minprice", metavar="L", type=int, nargs="?", default='0', help="The minimum price for apartment listings (integer; default: 0)")
parser.add_argument("-M", "--maxprice", metavar="H", type=int, nargs="?", default='10000000', help="The maximum price for apartment listings (integer; default: far too much)")
parser.add_argument("-b", "--bedrooms", metavar="B", type=int, nargs="?", default='0', help="Minimum number of bedrooms (integer; default: 0)")
parser.add_argument("-t", "--type", metavar="T", type=int, nargs="?", default='0', help="Type of housing (integer 1-12; default: 0")
parser.add_argument("-c", "--cats", metavar="C", choices=('Y', 'N'), nargs="?", default='N', help="Whether or not cats are allowed (Y/N; default: N)")
parser.add_argument("-d", "--dogs", metavar="D", choices=('Y', 'N'), nargs="?", default='N', help="Whether or not dogs are allowed (Y/N; default: N)")
parser.add_argument("-p", "--pics", metavar="P", choices=('Y', 'N'), nargs="?", default="0", help="Whether the result has a picture or not (Y/N; default: N)")
parser.add_argument("-l", "--limit", metavar="L", type=int, nargs="?", default="15", help="Number of results to return (integer; default: 15)")
args = parser.parse_args()

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
    r = requests.get("http://santabarbara.craigslist.org/search/apa?minAsk="+str(args.minprice)+"&maxAsk="+str(args.maxprice)+"&bedrooms="+str(args.bedrooms)+"&pets_cat="+str(catDict[args.cats])+"&pets_dog="+str(dogDict[args.dogs])+"&hasPic="+str(picDict[args.pics]))

    # Normalize unicode data and convert to ASCII to avoid weirdness
    s = unicodedata.normalize('NFKD', r.text).encode('ascii', 'ignore')

    # List of locations to ignore
    ignored = ["LOMPOC", "SANTA MARIA", "GOLETA", "ISLA VISTA", "CARPINTERIA", "CARLSBAD", "OXNARD", "CLEMENTE", "BUELLTON", "VANDENBERG", "BAKERSFIELD", "LOS ANGELES"]

    # Today's month/day, i.e. 'May 16'
    date = time.strftime("%B %d")

    # Use BeautifulSoup to parse HTML data
    soup = BeautifulSoup(s)
    content = soup.find('div', 'content')
    ads = content.findAll('p', 'row', limit=args.limit)

    # Write the results out to a file
    f.write("Searching for rooms between $"+str(args.minprice)+" and $"+str(args.maxprice)+" with "+str(args.bedrooms)+"+ bedrooms\n")
    if(catDict[args.cats])=='purrr':
        f.write("Cats are ALLOWED\n")
    else:
        f.write("Cats may not be allowed\n")
    if(dogDict[args.dogs])=='wooof':
        f.write("Dogs are ALLOWED\n")
    else:
        f.write("Dogs may not be allowed\n")
    f.write("Housing type is set to "+typeDict[args.type]+"\n")
    f.write("Pictures are "+picDict[args.pics]+"\n")
    f.write("Showing up to "+str(args.limit)+" result(s)\n")
    f.write("\n\n")


    # Loop through each ad and prettify the info
    for ad in ads:
        date = ad.contents[5].span.text
        tagline = ad.contents[5].a.text
        price = ad.contents[7].span.text
        # For some reason this errors out if you let it collect all the ads on a page, yet still gets all the data
        try:
            loc = ad.contents[7].select("small")[0].text
        except IndexError:
            loc = ""

        if any(ignored_loc in loc.upper() for ignored_loc in ignored):
            pass
        else:
            # Write out to results
            f.write(date+' - '+tagline+' - '+price+'\n')
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

send_mail(outbound_email, ["samlingx@gmail.com"], "Craigslist Scrape Results "+time.strftime("%m/%d/%y %H:%M:%S"), data, [], "smtp.gmail.com:587")
