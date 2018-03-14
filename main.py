#!/usr/bin/python2.7

import sys
import urllib
import urlparse
from datetime import datetime, timedelta
import json
import os.path
import time
import wwe

# Set some basic details and login
email = 'YOUR EMAIL HERE'
password = 'YOUR PASSWORD HERE'
# Available options are: 4500, 3000, 2400, 1800, 1200, 800
quality = '4500'

wwe_network = wwe.Network(email, password)
wwe_network.login()

# Get the show the user wants
show_link = wwe.get_user_input_show()

# Open the link for the show
json_response = urllib.urlopen(show_link[0])
show_link_json = json.loads(json_response.read())

# Generate a Kodi NFO file for the show/PPV/collection
get_nfo = getattr(wwe, 'get_'+show_link[1]+'_nfo')(show_link[0])


# Gets the first show from the users selection

show_video_id = show_link_json['list'][1]['itemTags']['media_playback_id']

# Make a name for the video from the headline + date
video_name = show_link_json['list'][1]['headline'] + '-' + show_link_json['list'][1]['itemTags']['event_date'][0].split('T')[0]
video_name = wwe.clean_name(video_name)
print video_name
# Get the video
wwe_network.get_video_url(show_video_id, video_name, '4500')

# And finally, logout
wwe_network.logout()
