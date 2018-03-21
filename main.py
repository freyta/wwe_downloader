#!/usr/bin/python2.7

import sys
import urllib
import urlparse
from datetime import datetime, timedelta
import json
import os.path
import time
import argparse
import wwe


parser = argparse.ArgumentParser()
parser.add_argument("-t","--type", help="download a single episode or year [options: \"year\" or \"single\"]", default="single")
args = parser.parse_args()
if (args.type == "year"):
    episodes_wanted = args.type
else:
    episodes_wanted = "single"

# Set some basic details and login
email = 'YOUR EMAIL HERE'
password = 'YOUR PASSWORD HERE'
# Available options are: 4500, 3000, 2400, 1800, 1200, 800
quality = '4500'

# Login to the network
wwe_network = wwe.Network(email, password)
wwe_network.login()

# Get the show the user wants
show_link = getattr(wwe, 'get_user_input_show_' + episodes_wanted)()


# Open the link for the show
json_response = urllib.urlopen(show_link[0])
show_link_json = json.loads(json_response.read())


# If it isn't a collection, show available episodes to download
if(not show_link[1]=="collection"):
    video_ids = wwe.download_multiple(show_link[0])
    #video_ids = [u'1886974483'] (url = http://network.wwe.com/video/v1886974483)
    
    # If it is a TV Show
    if show_link[1]=="tvshow":
        for(videoid, showname, date) in zip(video_ids[0], video_ids[1], video_ids[2]):
            # Create an useable name
            showname = wwe.clean_name(showname)
            showname = showname+".-."+date
            # Get the video
            wwe_network.get_video_url(videoid, showname, quality)
    else:
        for(videoid, showname) in zip(video_ids[0], video_ids[1]):
            # Create an useable name
            showname = wwe.clean_name(showname)
            showname = showname+".-."+date
            # Get the video
            wwe_network.get_video_url(videoid, showname, quality)
            
# Finally logout
wwe_network.logout()
