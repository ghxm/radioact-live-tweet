import argparse
import configparser
import glob
import twitter_auth
import tweepy
import os
import json
import re
import sys

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

def tweet(station_name, stream_url, state):

    if state == "online":
        text = "{station_name} is live!\nIf you're listening tune in: {stream_url}\n\nHop in the chat: https://chuntoo.chatango.com/".format(station_name = station_name, stream_url = stream_url)
    elif state == "offline":
        text = "{station_name} is offline.".format(station_name = station_name)

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

    args = parser.parse_args()

    # read in config.ini
    config = configparser.ConfigParser()
    configpath = glob.glob(os.path.dirname(os.path.abspath(__file__)) + '/config.ini')
    config.read(configpath)

    response = urlreq.urlopen(config['DEFAULT']['web_api_url'])
    html = response.read().decode("ISO-8859-1")

    ra_stations = json.loads(re.split("<[/]{0,1}script.*?>", html)[1])

    if args.station not in ra_stations.keys():
        print("Station not found")
        sys.exit(1)

    station = ra_stations[args.station]

    channel = [stream for stream in station.get('stream_url') if stream[0] == args.channel][0]

    state = channel[2]

    if state == config['DEFAULT']['last_tweeted']:
        print("State has not changed since last tweet")
        sys.exit(1)
    elif state == "offline" and not args.offline:
        print("Station is offline, offline tweet option is not enabled")
        sys.exit(1)

    print('Tweeting: ' + str(state))

    if not args.debug:

        try:
            tweet(station_name = station['title'], stream_url=channel[1], state=state)
            # write state to config.ini
            config['DEFAULT']['last_tweeted'] = state

            print('Writing config...')

            with open(configpath[0], 'w') as configfile:
                config.write(configfile)

            print('All good')
        except Exception as e:
            print('Error!: ')
            print(str(e))


if __name__ == "__main__":
    main()
