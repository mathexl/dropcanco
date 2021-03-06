import re
import sys
import urllib
import requests
import random
from subprocess import Popen, PIPE
from requests_oauthlib import OAuth1


def authenticate():
    # Yes our keys were hard coded in here.
    # No they are no longer active, so you don't have to dig through our commits.
    return OAuth1('consumer_key',
          client_secret='client_secret',
          resource_owner_key='resource_owner_key',
          resource_owner_secret='resource_owner_secret'
    )


def tweet(status):
    oauth = authenticate()
    status = urllib.quote_plus(re.sub('<[^>]*>', '', status[:140]))
    response = requests.post(url="https://api.twitter.com/1.1/statuses/update.json?status=%s" % status, auth=oauth).json()
    print(response)


def run(f, **kwargs):
    # connect
    process = Popen('mysql dropcan -u%s -p%s -h $(sudo docker inspect mysql | grep IPAddress | grep -o "[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*")' % ("garbageman", "password"), stdout=PIPE, stdin=PIPE, shell=True)
    args = ""
    base = "~/twitterbot/"
    if len(sys.argv) == 3:
        base = sys.argv[2]

    for key in kwargs:
        args += 'set @%s=\'%s\'; \n' % (key, re.escape(kwargs[key]))
    return re.sub('\\n', ' ', " ".join(process.communicate(args + ('source %sscripts/%s.sql' % (base, f)))[0].split("\n")[3:]))


def post():
    tweet(run('to'))


def discover():
    oauth = authenticate()
    response = requests.get(url="https://api.twitter.com/1.1/search/tweets.json?q=%40dropcanco", auth=oauth).json()
    for status in response.get('statuses', []):

        text = re.sub('<[^>]*>', '', status['text'])
        text = re.sub(r"(https?://\S+\.?\S+\.\S+)", r"<a href='\1'>\1</a>", text)
        text = re.sub(r"(\#[a-zA-Z0-9]*)", r"<b class='hastag'>\1</b>", text)
        text = re.sub(r"(\@[a-zA-Z0-9]*)", r"<b class='at'>\1</b>", text)

        run('read', status=text, setting="twitter", )


def follow():

    if not len(sys.argv) is 3:
        print("Bad.")
        return

    oauth = authenticate()

    # Weight your hashtags for randomness
    hashtags = ["trash","trash","trash","garbage","rubbish","dropcan"]
    hashtag = hashtags[random.randint(0, len(hashtags) - 1)]
    response = requests.get(url="https://api.twitter.com/1.1/search/tweets.json?q=%23" + hashtag, auth=oauth).json()

    # Just once
    for status in response.get('statuses', []):
        if not (status['user']['protected'] and status['user']['following']):
            follower = status['user']['id']

            # Just some hardcoded twitter endpoints
            url = {
                "retweet"   :"https://api.twitter.com/1.1/statuses/retweet/%d.json" % status["id"],
                "favorite"  :"https://api.twitter.com/1.1/favorites/create.json?id=%d" % status["id"]
            }.get(sys.argv[2])
            requests.post(url=url, auth=oauth)
            requests.post(url="https://api.twitter.com/1.1/friendships/create.json?user_id=%d&follow=true" % follower, auth=oauth)
            break

# Yay for functional hacks
({
    "post"     :post,
    "discover" :discover,
    "follow"   :follow
}.get(sys.argv[1]))()
