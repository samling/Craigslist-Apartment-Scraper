#!/usr/local/bin/python

import os
import ConfigParser

Config = ConfigParser.ConfigParser()

cfgfile = open("config.cfg", 'w')

Config.add_section('SearchParams')
Config.set('SearchParams', 'MinPrice', os.environ["MIN_PRICE"])
Config.set('SearchParams', 'MaxPrice', os.environ["MAX_PRICE"])
Config.set('SearchParams', 'BedroomNo', os.environ["BEDROOM_NO"])
Config.set('SearchParams', 'HousingType', os.environ["HOUSING_TYPE"])
Config.set('SearchParams', 'Cats', os.environ["CATS"])
Config.set('SearchParams', 'Dogs', os.environ["DOGS"])
Config.set('SearchParams', 'Pics', os.environ["PICS"])
Config.set('SearchParams', 'Limit', os.environ["LIMIT"])

Config.write(cfgfile)

cfgfile.close()
