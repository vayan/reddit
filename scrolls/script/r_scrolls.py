#!/usr/bin/env python

import time
import praw
import urllib
import sys
import json

#bot to update ladder in sidebar
#usage : python r_scrolls.py reddit_pseudo reddit_pass


def ladder_update(  user_agent='sidebar ladder updater for rscrolls [praw]', user='user', 
                    password='pass', subr_name='subreddit', sentinel='[~s~](/s)'):

    print ('Starting ladder update... ')

    r = praw.Reddit(user_agent=user_agent)
    r.login(user, password)
    subreddit = r.get_subreddit(subr_name)
    settings = subreddit.get_settings()

    # Grab current description
    subr_desc = settings['description'].split(sentinel, 1)[0]

    print ('Get data from scrolls guide')

    f = urllib.urlopen("http://a.scrollsguide.com/ranking?limit=10&fields=name,rating,rank")
    sg_api = f.read()
    f.close()

    sg_api_parse = json.loads(sg_api)
    top10 = ""

    if sg_api_parse['msg'] == 'success':
        for player in sg_api_parse['data']:
            top10 = "%s * %s (%d) \n" % (top10, player['name'], player['rating'])

        top10 = '\n\n**Ladder (top 10)**\n\n' + top10 + '\n\n[More at SG/ranking](http://scrollsguide.com/ranking)\n\n'

        print top10

        # Set the update message
        lastUpdated = "[Last updated at %s](/smallText)\n\n" % time.strftime('%H:%M:%S UTC', time.gmtime())

        # Update subreddit description
        newDescription = '%s%s%s%s' % (subr_desc, sentinel,  top10, lastUpdated)

        print ('Updating sidebar... with ', newDescription)

        try:
            subreddit.update_settings(description=newDescription)
        except praw.errors.APIException, err:
            print('Error', err)

        print ('Done!')
    else:
        print ('Fail')


def main():
    while True:
        ladder_update(  user_agent='sidebar ladder updater for rscrolls [praw]',
                        user=sys.argv[1], password=sys.argv[2], subr_name='scrolls')
        time.sleep(15 * 60)  # every 15 minutes

if __name__ == '__main__':
    main()
