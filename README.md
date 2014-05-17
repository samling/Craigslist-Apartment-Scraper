Craigslist-Apartment-Scraper
============================

Search Craigslist for apartments meeting certain criteria and have the results emailed to you.


Everyone who's ever tried to search for an apartment on Craigslist knows how frustrating it can
be to wade through non-local results or the same ad reposted endlessly. This script does a
passable job at sifting through the crap to return only results that fit the designated
criteria.

Currently the script is VERY LOCALIZED as I created it specifically to find apartments locally.
I repeat: this will not be useful to you unless you live in southern California. However,
my immediate plans include refactoring and expanding to include all basic Craigslist features
as well as some additional features, like the ability to include/exclude certain locations or words
from search results.

In order for the email function to work properly, create a file called private.py with the following
schema:

outbound_email = 'yourusername@example.com'
outbound_un = 'yourusername'
outbound_pw = 'password'

The script uses gmail's SMTP server to send emails. To set this up properly, go to:

Gmail settings -> Accounts and Import -> Other Google Account settings -> "Security" tab
in the new window that opens up -> App passwords settings

and create a new application-specific password for this script. Place that in outbound_pw and you're
set to go!

