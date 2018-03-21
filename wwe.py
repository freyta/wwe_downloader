#!/usr/bin/python2.7

import re
import os
import subprocess
import requests
from urllib import unquote
import m3u8
from xml.dom.minidom import parseString
import sys
import urllib
import urlparse
from datetime import datetime, timedelta
import json


# Array of the shows URL names and their real names
shows = ["wwe", "ecw", "wcw", "in_ring", "original", "collections", "vault"]
show_real = ["WWE PPV", "ECW PPV", "WCW PPV", "In Ring", "Originals", "Collections", "Vault"]


# Some of the needed URLs
PRE_LOGIN_URL = "https://secure.net.wwe.com/enterworkflow.do?flowId=account.login"
LOGIN_URL = "https://secure.net.wwe.com/workflow.do"
LOGOUT_URL = "https://secure.net.wwe.com/enterworkflow.do?flowId=registration.logout"
VIDEO_URL = "https://ws.media.net.wwe.com/ws/media/mf/op-findUserVerifiedEvent/v-2.3"


SOAPCODES = {
    "1": "OK",
    "-1000": "Requested Media Not Found",
    "-1500": "Other Undocumented Error",
    "-2000": "Authentication Error",
    "-2500": "Blackout Error",
    "-3000": "Identity Error",
    "-3500": "Sign-on Restriction Error",
    "-4000": "System Error",
}


class Network:

    def __init__(self, user, password):
        self.user = user
        self.password = password
        self.user_uuid = ''
        self.cookies = None
        self.logged_in = False

    def login(self):
        print (self.user, self.password)
        with requests.Session() as s:

            s.get(PRE_LOGIN_URL)

            auth_values = {'registrationAction': 'identify',
                           'emailAddress': self.user,
                           'password': self.password}

            s.post(LOGIN_URL, data=auth_values)

            try:
                self.user_uuid = unquote(s.cookies['mai']).split('useruuid=')[1].replace('[', '').replace(']', '')
                self.cookies = s.cookies
                self.logged_in = True
            except:
                raise ValueError('Login was unsuccessful.')

    def set_cookies(self, cookies):
        self.user_uuid = unquote(cookies['mai']).split('useruuid=')[1].replace('[', '').replace(']', '')
        self.cookies = cookies
        self.logged_in = True

    def get_video_url(self, content_id, new_name, bit_rate):
        if not self.logged_in:
            self.login()

        query_values = {
            'contentId': content_id,
            'fingerprint': unquote(self.cookies['fprt']),
            'identityPointId': self.cookies['ipid'],
            'playbackScenario': 'HTTP_CLOUD_WIRED',
            'platform': 'WEB_MEDIAPLAYER_5',
        }

        with requests.Session() as s:
            s.cookies = self.cookies
            response = s.get(VIDEO_URL, params=query_values).content
            parsed_response = parseString(response)

            status_code = parsed_response.getElementsByTagName('status-code')[0].childNodes[0].data

            if status_code != "1":
                print(SOAPCODES[status_code])
                
            media_auth_v2 = (parsed_response.getElementsByTagName("session-info")[0]
                             .childNodes[0]
                             .childNodes[0]
                             .attributes.get("value").nodeValue)

            cookies_string = ';'.join([x + '=' + y for x, y in self.cookies.items()])
            cookies_string += ';mediaAuth_v2=' + media_auth_v2

            # TODO: Where does this come from... and is it important? Currently
            # it is just copy and pasted from what I see in my local cookie!
            cookies_string += ';actionxCookie=%7B%22fired%22%3Atrue%7D'

            m3u8_url = parsed_response.getElementsByTagName('url')[0].childNodes[0].data
            
            m3u8_object = m3u8.loads(s.get(m3u8_url).content)
            bandwidth_and_uri = []
            for playlist in m3u8_object.playlists:
                bandwidth_and_uri.append((playlist.stream_info.bandwidth / 1000, playlist.uri))
                

            bandwidth_and_uri.sort(cmp=lambda a, b: b[0] - a[0])

            uri = bandwidth_and_uri[0][1]

            bit_rate_int = int(bit_rate.replace("K", ""))
            for bandwidth, potential_uri in bandwidth_and_uri:
                if bandwidth > bit_rate_int:
                    uri = potential_uri

            stream_url = (m3u8_url[:m3u8_url.rfind('/') + 1] + uri)

            subprocess.call('ffmpeg -user_agent "Mozilla/5.0 (X11; Linux x86_64; rv:10.0) Gecko/20100101 Firefox/10.0" -headers "Cookie: ' + cookies_string + '" -i ' + stream_url + ' -c copy ' + new_name + '.ts -y', shell=True)
            subprocess.call('ffmpeg -i ' + new_name + '.ts -c copy ' + new_name + '.mp4 -y', shell=True)
            
    def logout(self):
        with requests.Session() as s:
            s.cookies = self.cookies
            response = s.get(LOGOUT_URL)
            pattern = re.compile(r'You are now logged out.')
            
            if not re.search(pattern, response.text):
                print("Logout was unsuccessful.")
            else:
                print("Logged out")
                
                
                

def get_user_input_show_single():
    listcounter = 0

    for shows_zip, show_real_zip in zip(shows, show_real):
        print "Option: " + str(listcounter) + " - " + show_real_zip
        listcounter = listcounter + 1

    show_option = raw_input("Choose a show number from above\n")
    show_option = int(show_option)

    if(show_option >= listcounter):
        print("Oops, you chose an invalid show. Quitting..")
        sys.exit()
    elif(int(show_option) < 0):
        print("Oops, you chose an invalid show. Quitting..")
        sys.exit()

    # Clear the screen after their choice
    os.system('clear')


    # Get a list of shows from option
    show_list = get_show_list(shows[show_option])
    
    # Set a list counter
    listcounter = 0

    for search_name, show_name in zip(show_list[0], show_list[1]):
        print("Option " + str(listcounter) + ": - " + show_name)
        listcounter = listcounter + 1

    # Get the user input for which show to get the year from
    user_show = raw_input("Choose a show number from above\n")
    user_show = int(user_show)
    
    # If the input is higher than the amount of shows we have..
    if(int(user_show) >= listcounter):
        print("Oops, you chose an invalid show. Quitting..")
        sys.exit()
    elif(int(user_show) < 0):
        print("Oops, you chose an invalid show. Quitting..")
        sys.exit()
        
    # Get readable names for the shows
    user_show_pretty = show_list[1][user_show]
    user_search_pretty = show_list[0][user_show][0]

    # Clear the screen after their choice
    os.system('clear')
    
    # Make sure we don't try to find a year for Collections
    if(show_real[show_option] == "Collections"):
        return_link = "http://network.wwe.com/gen/content/tag/v1/show_name/r/" + user_search_pretty + "/jsonv4.json"
    else:
        print "Choose a year for the show \"" + user_show_pretty + "\""
        year = get_show_year(show_list[0][user_show])


        # Reset the list counter to 0
        listcounter = 0

        for show_year in zip(year[0]):
            print("Option " + str(listcounter) + ": - " + show_year[0])
            listcounter = listcounter + 1

        # Get the user input for which show to get the year from
        user_year = raw_input("Choose a year from above\n")

        user_year = int(user_year)

        user_year_pretty = year[0][user_year]

        # If the input is higher than the amount of shows we have..
        if(int(user_year) >= listcounter):
            print("Oops, you chose an invalid show. Quitting..")
            sys.exit()
        elif(int(user_year) < 0):
            print("Oops, you chose an invalid show. Quitting..")
            sys.exit()

        return_link = "http://network.wwe.com/gen/content/tag/v1/show_name/"+ user_year_pretty + "/r/" + user_search_pretty + "/jsonv4.json"
    
    if "PPV" in show_real[show_option]:
        show_type = "ppv"
    elif "Collection" in show_real[show_option]:
        show_type = "collection"
    else:
        show_type = "tvshow"
    return return_link, show_type
    
    
    
def get_user_input_show_year():

    ########################
    # Start of which company
    ########################
    listcounter = 0
    user_show = 0

    for shows_zip, show_real_zip in zip(shows, show_real):
        print "Option: " + str(listcounter) + " - " + show_real_zip
        listcounter = listcounter + 1

    show_option = raw_input("Choose a show number from above\n")
    show_option = int(show_option)

    if(show_option >= listcounter):
        print("Oops, you chose an invalid show. Quitting..")
        sys.exit()
    elif(int(show_option) < 0):
        print("Oops, you chose an invalid show. Quitting..")
        sys.exit()

    # Clear the screen after their choice
    os.system('clear')
    ######################
    # End of which company
    ######################
    # Start of which show
    ######################
    
    # If we don't want a PPV
    if((shows[show_option] != "ecw") and (shows[show_option] != "wcw") and (shows[show_option] != "wwe")): 
        # Get a list of shows from option
        show_list = get_show_list(shows[show_option])
        
        # Set a list counter
        listcounter = 0

        for search_name, show_name in zip(show_list[0], show_list[1]):
            print("Option " + str(listcounter) + ": - " + show_name)
            listcounter = listcounter + 1

        # Get the user input for which show to get the year from
        user_show = raw_input("Choose a show number from above\n")
        user_show = int(user_show)
        
        # If the input is higher than the amount of shows we have..
        if(int(user_show) >= listcounter):
            print("Oops, you chose an invalid show. Quitting..")
            sys.exit()
        elif(int(user_show) < 0):
            print("Oops, you chose an invalid show. Quitting..")
            sys.exit()
            
        # Get readable names for the shows
        user_show_pretty = show_list[1][user_show]
        user_search_pretty = show_list[0][user_show][0]

        # Clear the screen after their choice
        os.system('clear')
    else:
        # Since we want a PPV just skip
        user_show_pretty = show_real[show_option]
        user_show = "PPV"
        pass
    
    ######################
    # End of which show
    ######################
    # Start of which year
    ######################
        
    # Make sure we don't try to find a year for Collections
    if(show_real[show_option] == "Collections"):
        return_link = "http://network.wwe.com/gen/content/tag/v1/show_name/r/" + user_search_pretty + "/jsonv4.json"
    else:
        print "Choose a year for the show \"" + user_show_pretty + "\""

        # Reset the list counter to 0
        listcounter = 0
        # If we chose a PPV
        if "PPV" in show_real[show_option]:
            
            year = get_whole_year(shows[show_option])

            for show_year in zip(year[0]):
                print("Option " + str(listcounter) + ": - " + show_year[0])
                listcounter = listcounter + 1
                
        # Since we chose a TV show
        else:
            year = get_show_year(show_list[0][user_show])

            for show_year in zip(year[0]):
                print("Option " + str(listcounter) + ": - " + show_year[0])
                listcounter = listcounter + 1
        
        
        # Get the user input for which show to get the year from
        user_year = raw_input("Choose a year from above\n")
        # Convert the input to an integer
        user_year = int(user_year)
        # Get the actual year from the shows array above
        user_year_pretty = year[0][user_year]
        
        # If the input is higher than the amount of shows we have..
        if(int(user_year) >= listcounter):
            print("Oops, you chose an invalid show. Quitting..")
            sys.exit()
        elif(int(user_year) < 0):
            print("Oops, you chose an invalid show. Quitting..")
            sys.exit()
        
        # If we are trying to watch a PPV
        if (user_show == "PPV"):
            return_link = "http://network.wwe.com/gen/content/tag/v1/franchise/"+ user_year_pretty + "/r/" + shows[show_option] + "/jsonv4.json"
        else:
            return_link = "http://network.wwe.com/gen/content/tag/v1/show_name/"+ user_year_pretty + "/r/" + user_search_pretty + "/jsonv4.json"
    
    if "PPV" in show_real[show_option]:
        show_type = "ppv"
    elif "Collection" in show_real[show_option]:
        show_type = "collection"
    else:
        show_type = "tvshow"
    return return_link, show_type
    
    
def get_show_list(show):

    seo_name        = []
    show_name       = []
    episode_title   = []
    year            = []

    # Example link: http://network.wwe.com/gen/content/tag/v1/section/in_ring/jsonv4.json
    json_response = urllib.urlopen("http://network.wwe.com/gen/content/tag/v1/section/" + show + "/jsonv4.json")
    event = json.loads(json_response.read())


    # Get a list of videos to download from the JSON file
    for i in event['list']:
        # The event has the type set as wwe-asset.
        # wwe-show is where all the information for the comapny is. i.e. thumbnails and years etc
        if i['type'] == 'wwe-show':
            # Get the search name for a show (wwe-superstars, wwe-nxt, wwe-talking-smack etc)
            seo_name.append(i['itemTags']['show_name'])
            # Get the shows headline which is usually episode number or PPV event (Nitro 288, Summerslam 2003 etc)
            show_name.append(i['title'])
    return seo_name, show_name
    
def get_show_year(show):

    year = []

    # Example link: http://network.wwe.com/gen/content/tag/v1/show_name/r/backlash/jsonv4.json

    json_response = urllib.urlopen("http://network.wwe.com/gen/content/tag/v1/show_name/r/" + show[0] + "/jsonv4.json")
    event = json.loads(json_response.read())

    for i in event['list']:
        if i['type'] == 'wwe-show':
            year.append(i['itemTags']['year'])
            
    return year
    
def get_whole_year(show):

    year = []

    # Example link: http://network.wwe.com/gen/content/tag/v1/franchise/r/wwe/jsonv4.json
    json_response = urllib.urlopen("http://network.wwe.com/gen/content/tag/v1/franchise/r/" + show + "/jsonv4.json")
    event = json.loads(json_response.read())

    for i in event['list']:
        if i['type'] == 'wwe-section':
            year.append(i['itemTags']['year'])
    return year

        
# link needs to be similar to http://network.wwe.com/gen/content/tag/v1/show_name/r/table_for_3/jsonv4.json
def get_tvshow_nfo(link):
    print link
    json_response = urllib.urlopen(link)
    show = json.loads(json_response.read())
    
    if show['list'][0]['type'] == 'wwe-show':
    
        # The show title
        title = show['list'][0]['title']
        # Get the TV Rating
        tv_rating = next(iter(show['itemTagLibrary']['tv_rating'] or []), None)
        # Get the show franchise for the studio
        franchise = next(iter(show['itemTagLibrary']['franchise'] or []), None).upper()
        print franchise
        # Get the show plot
        for key in show['list'][0]:
            print key
            if (key == 'blurb'):
                plot = show['list'][0]['blurb']
            if (key == 'bigblurb'):
                plot = show['list'][0]['bigblurb']
            else:
                plot = ""
        
        # Get the year
        date = show['list'][0]['userDate'].split('-')[0]
        
        
        # Make the nfo a bit friendlier
        nfo_name = title + '.' + date
        nfo_name = clean_name(nfo_name)
        
        
        
        with open(nfo_name + '.nfo', 'w') as f:
            print >> f,  ' <tvshow>\n\
       <title>' + title + '</title>\n\
       <showtitle>' + title + '</showtitle\n\
       <plot>' + plot + '</plot>\n\
       <tagline></tagline>\n\
       <mpaa>' + tv_rating + '</mpaa>\n\
       <genre>Wrestling</genre>\n\
       <year>' + date + '</year>\n\
       <studio>' + franchise + '</studio>\n\
</tvshow>'
        return "Saved the nfo"
        
        
        
        
# link needs to be similar to http://network.wwe.com/gen/content/tag/v1/show_name/2000/r/backlash/jsonv4.json
def get_ppv_nfo(link):
    print link
    json_response = urllib.urlopen(link)
    show = json.loads(json_response.read())
    
    if show['list'][1]['type'] == 'wwe-asset':
    
        # The show title
        title = show['list'][1]['headline']
        # Get the TV Rating
        tv_rating = next(iter(show['itemTagLibrary']['tv_rating'] or []), None)
        # Get the show franchise for the studio
        franchise = next(iter(show['itemTagLibrary']['franchise'] or []), None).upper()
        # Get the show outline
        outline = show['list'][1]['bigblurb']
        # Get the show plot
        plot = show['list'][1]['notes']
        
        # Get the year
        date = show['list'][1]['userDate'].split('-')[0]
        
        # Make the nfo a bit friendlier
        nfo_name = title + '.' + date
        nfo_name = clean_name(nfo_name)
        
        with open(nfo_name + '.nfo', 'w') as f:
            print >> f,  ' <tvshow>\n\
       <title>' + title + '</title>\n\
       <showtitle>' + title + '</showtitle>\n\
       <outline>' + outline + '</outline>\n\
       <plot>' + plot + '</plot>\n\
       <tagline></tagline>\n\
       <mpaa>' + tv_rating + '</mpaa>\n\
       <genre>Wrestling</genre>\n\
       <year>' + date + '</year>\n\
       <studio>' + franchise + '</studio>\n\
</tvshow>'
        return "Saved the nfo"


# link needs to be similar to http://network.wwe.com/gen/content/tag/v1/show_name/r/234493012/jsonv4.json
def get_collection_nfo(link):
    json_response = urllib.urlopen(link)
    show = json.loads(json_response.read())
    
    if show['list'][0]['type'] == 'collection':
    
        # The show title
        title = show['list'][0]['title']
        # Get the TV Rating
        tv_rating = next(iter(show['itemTagLibrary']['tv_rating'] or []), None)
        # Get the show franchise for the studio
        franchise = next(iter(show['itemTagLibrary']['franchise'] or []), None).upper()
        # Get the show outline
        outline = show['list'][0]['blurb']
        
        # Get the year
        date = show['list'][1]['userDate'].split('-')[0]
        
        
        # Make the nfo a bit friendlier
        nfo_name = clean_name(title)
        print title
        
        with open(nfo_name + '.nfo', 'w') as f:
            print >> f,  ' <tvshow>\n\
       <title>' + title + '</title>\n\
       <showtitle>' + title + '</showtitle>\n\
       <outline>' + outline + '</outline>\n\
       <plot>' + outline + '</plot>\n\
       <tagline></tagline>\n\
       <mpaa>' + tv_rating + '</mpaa>\n\
       <genre>Wrestling</genre>\n\
       <year>' + date + '</year>\n\
       <studio>' + franchise + '</studio>\n\
</tvshow>'
        return "Saved the nfo"
    else:
        return "Error: Link wasn't for a collection"
                
def download_multiple(jsonlink):

    show_id         = []
    show_name       = []
    show_date       = []

    # Example link: http://network.wwe.com/gen/content/tag/v1/franchise/1989/r/wwe/jsonv4.json
    json_response = urllib.urlopen(jsonlink)
    #json_response = open("1.json")
    event = json.loads(json_response.read())

    # Count how many episodes are in the list ignoring the first entry
    episodes = len(event['list'])-1

    # Get a list of videos to download from the JSON file
    for i in event['list']:
        # The event has the type set as wwe-asset.
        # wwe-show is where all the information for the comapny is. i.e. thumbnails and years etc
        if i['type'] == 'wwe-asset':
            # Get the event ID for the URL i.e. http://network.wwe.com/video/v31303817
            show_id.append(i['itemTags']['media_playback_id'][0])
            show_name.append(i['show_name'])
            show_date.append(i['userDate'].split('T')[0])
            

    return show_id, show_name, show_date

def clean_name(name):
    # Make the nfo a bit friendlier
    name = name.replace(" ",".")
    name = name.replace("/",".")
    name = name.replace("'",".")
    name = name.replace("?",".")
    name = name.replace("!",".")
    name = name.replace(":","")
    name = name.replace("<",".")
    name = name.replace(">",".")
    name = name.replace("|",".")
    name = name.replace("/",".")
    name = name.replace("\\",".")
    name = name.replace("\"","")
    name = name.replace("'","")
    name = name.replace("*",".")
    name = name.replace("#",".")
    return name
