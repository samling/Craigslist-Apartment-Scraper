from bs4 import BeautifulSoup
from cStringIO import StringIO
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders
import commands
import smtplib
import os
import sys
import requests
import unicodedata
import time
import argparse

# Import private untracked credentials; continue anyway if not found, but email won't work
try:
    from private import *
except ImportError:
    pass

# Take some command line arguments
parser = argparse.ArgumentParser(description="Search Craigslist apartment listings and get the results emailed to you.")
parser.add_argument("maxprice", metavar="P", type=int, nargs="?", default='10000000', help="The maximum price for apartment listings (default: far too much)")
parser.add_argument("bedrooms", metavar="B", type=int, nargs="?", default='0', help="Minimum number of bedrooms (default: 0)")
parser.add_argument("cats", metavar="C", choices=('Y', 'N'), nargs="?", default='N', help="Whether or not cats are allowed (default: N)")
parser.add_argument("limit", metavar="L", type=int, nargs="?", default="15", help="Number of results to return (default: 15)")
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

# Translate Y/N into the correct GET variable
def yn(arg):
    ua = str(arg).upper()
    if ua == 'Y':
        return "purrr" 
    else:
        return ""

with open('results.txt', 'w') as f:

    # Get unicode response from Craigslist GET request
    r = requests.get("http://santabarbara.craigslist.org/search/apa?maxAsk="+str(args.maxprice)+"&bedrooms="+str(args.bedrooms)+"&pets_cat="+str(yn(args.cats)))

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
    f.write("Searching for rooms up to $"+str(args.maxprice)+" with "+str(args.bedrooms)+"+ bedrooms\n")
    if(yn(str(args.cats)))=='purrr':
        f.write("Cats are ALLOWED\n")
    else:
        f.write("Cats are NOT (explicitly) ALLOWED\n")
    f.write("Showing up to "+str(args.limit)+" result(s)")
    f.write("\n\n")


    for ad in ads:
        date = ad.contents[5].span.text
        tagline = ad.contents[5].a.text
        price = ad.contents[7].span.text
        loc = ad.contents[7].select("small")[0].text

        if any(ignored_loc in loc.upper() for ignored_loc in ignored):
            pass
        else:
            # Print to stdout
            f.write(date+' - '+tagline+' - '+price+'\n')
            f.write(loc+'\n')
            for link in ad.findAll('a', limit=1):
                url = link.get('href')
                f.write('View ad on CL: http://santabarbara.craigslist.org/' + url +'\n')
            f.write("\n")

with open("results.txt", "r") as results:
    data = results.read()
send_mail(outbound_email, ["samlingx@gmail.com"], "Craigslist Scrape Results", data, [], "smtp.gmail.com:587")
