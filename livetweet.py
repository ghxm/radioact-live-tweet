import argparse
import configparser
import glob
import twitter_auth
import tweepy
import os
import json
import re
import sys
import wombot_fortunes
import random
import time

if sys.version_info[0] > 2:
    import urllib.request as urlreq
else:
    import urllib2 as urlreq


auth = tweepy.OAuthHandler(twitter_auth.api_key, twitter_auth.api_key_secret)
auth.set_access_token(twitter_auth.access_token, twitter_auth.access_token_secret)

api = tweepy.API(auth)

try:
    api.verify_credentials()
    print("Authentication Successful")
except:
    sys.exit(1)
    print("Authentication Error")

def tweet(station_name, stream_url, state, fortune = False):

    if state == "online":
        text = "{station_name} is live!\nIf you're listening tune in: {stream_url}\n\nHop in the chat: https://chuntoo.chatango.com/".format(station_name = station_name, stream_url = stream_url)
    elif state == "offline":
        text = "{station_name} is offline.".format(station_name = station_name)

    if fortune:
        text += "\nHave a free wombot fortune: " + random.choice(wombot_fortunes.fortunecookie)

    try:
        if api.update_status (text):
            print(text + '\n' + "Tweet posted")
    except tweepy.errors.TweepyException as e:
        raise e





def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--station', type=str, help='only check these stations', default="chuntfm")
    parser.add_argument('-o', '--offline', action="store_true", help='send tweet when station goes offline')
    parser.add_argument('-c', '--channel', type=str, help='only check these stations', default="live")
    parser.add_argument('-d', '--debug', action='store_true', help='debug mode')
    parser.add_argument('-f', '--fortune', action='store_true', help='Add a random fortune')
    parser.add_argument('-r', '--delay', type=int, help='Sleep before tweeting to make sure online is longer than x seconds')
    parser.add_argument('-w', '--writeOut', type=str, help='Write out json file to path instead of tweeting')

    args = parser.parse_args()

    # read in config.ini
    config = configparser.ConfigParser()
    configpath = glob.glob(os.path.dirname(os.path.abspath(__file__)) + '/config.ini')
    config.read(configpath)

    def getStationInfo(station, channel):

        response = urlreq.urlopen(config['DEFAULT']['web_api_url'])
        html = response.read().decode("ISO-8859-1")

        ra_stations = json.loads(re.split("<[/]{0,1}script.*?>", html)[1])

        if args.station not in ra_stations.keys():
            print("Station not found")
            sys.exit(1)

        s_station = ra_stations[station]

        s_channel = [stream for stream in s_station.get('stream_url') if stream[0] == channel][0]

        state = s_channel[2]

        return ({'station': args.station,
         'prettyName': s_station.get('title'),
         'streamName': s_channel[0],
         'streamUrl': s_channel[1],
         'status': state})



    station_info = getStationInfo(args.station, args.channel)

    state = station_info['status'].strip()

    if args.writeOut and not args.debug:

        try:
            print('Writing status to file: ' + args.writeOut + "/" + args.station + '.json')

            with open(args.writeOut + "/" + args.station + '.json', 'w') as outfile:
                json.dump(station_info, outfile)
        except Exception as e:
            print('Error writing status to file: ' + args.writeOut + "/" + args.station + '.json')
            print(e)

    if state == config['DEFAULT']['last_state']:
        print("State has not changed since last tweet")
        sys.exit(1)
    else:
        print('Sleeping to make sure')
        start = time.time()
        while time.time() - start < args.delay:
            time.sleep(args.delay/5)
            config.read(configpath)
            if config['DEFAULT']['last_tweeted'] == state and config['DEFAULT']['last_state'] == state:
                print("State has has already been tweeted, exiting")
                sys.exit(1)
            if (getStationInfo(args.station, args.channel)['status'] != state):
                print('State changed, exiting...')
                sys.exit(1)
        if state == "offline" and not args.offline:
            config['DEFAULT']['last_state'] = state
            with open(configpath[0], 'w') as configfile:
                config.write(configfile)
            print("Station is offline, offline tweet option is not enabled")
            sys.exit(1)
        print('Sleeping done, state unchanged')

    config['DEFAULT']['last_state'] = state

    if not args.debug:

        print('Tweeting: ' + str(state))

        try:

            tweet(station_name = station_info['prettyName'], stream_url=station_info['streamUrl'], state=state, fortune=args.fortune)
            # write state to config.ini
            config['DEFAULT']['last_tweeted'] = state


            print('All good')
        except Exception as e:
            print('Error!: ')
            print(str(e))

        print('Writing config...')
        with open(configpath[0], 'w') as configfile:
            config.write(configfile)


if __name__ == "__main__":
    main()
