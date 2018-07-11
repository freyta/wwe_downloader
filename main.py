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

wwe_network = wwe.Network(email, password)
wwe_network.login()

# Get the show the user wants
show_link = getattr(wwe, 'get_user_input_show_' + episodes_wanted)()


if not show_link[1]=="single_tvshow":
    # Open the link for the show
    json_response = urllib.urlopen(show_link[0])
    show_link_json = json.loads(json_response.read())


# If it isn't a collection, show available episodes to download
if(not show_link[1]=="collection"):
    if(episodes_wanted == "year"):
        video_ids = wwe.download_multiple(show_link[0])
        # If it is a TV Show
        if show_link[1]=="tvshow":
            for(videoid, showname, date) in zip(video_ids[0], video_ids[1], video_ids[2]):
                # Clean up the video name a bit
                showname = wwe.clean_name(showname)
                showname = showname+"."+date
                # Get the video
                wwe_network.get_video_url(videoid, showname, quality)
        # We want to download a PPV
        else:
            for(videoid, showname, year) in zip(video_ids[0], video_ids[1], video_ids[2]):
                # Clean up the video name a bit
                showname = wwe.clean_name(showname + "." + year.split('-')[0])
                
                # Get the video
                wwe_network.get_video_url(videoid, showname, quality)
    # We just want to download a single episode
    else:
        # If it is a TV Show
        if show_link[1]=="single_tvshow":
            # Clean up the video name a bit
            showname = wwe.clean_name(show_link[2])
            showname = showname + "." + show_link[3]
            # Get the video
            wwe_network.get_video_url(show_link[0], showname, quality)
        # We want to download a PPV
        else:
            video_ids = wwe.download_multiple(show_link[0])
            for(videoid, showname, year) in zip(video_ids[0], video_ids[1], video_ids[2]):
                # Clean up the video name a bit
                showname = wwe.clean_name(showname + "." + year.split('-')[0])
                # Get the video
                wwe_network.get_video_url(videoid, showname, quality)
# We must be a collection
else:
    video_ids = wwe.download_collection(show_link[0])
    counter = 0
    for(videoid, showname) in zip(video_ids[0], video_ids[1]):
        # Clean up the video name a bit
        showname = wwe.clean_name(showname)
        showname = str(counter) + "." + showname
        
        # Get the video
        wwe_network.get_video_url(videoid, showname, quality)
        counter = counter + 1
wwe_network.logout()
