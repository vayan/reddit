#!/usr/bin/env python

import praw
import sys

# USAGE :
#
# python updatecss.py reddit_pseudo reddit_pass subreddit_name path_to_css
#
# ex python updatecss.py trolo lo scrolls /path/to/style.css
#
# TODO : get the tocopuincss.txt from the spritesheet script and add it to the css
#


def css_update(user_agent='sidebar ladder updater [mellort python module]',
                     user='user', password='pass', subr_name='subreddit',
                     cssfile='style.css'):
    print ('Starting css update...')
    print ('Get css from file')
    s = open(cssfile, 'r').read()
    print ('Connecting to reddit...')
    r = praw.Reddit(user_agent=user_agent)
    r.login(user, password)
    subreddit = r.get_subreddit(subr_name)
    print ('Updating css ...')
    subreddit.set_stylesheet(s)
    print ('Done!')


def main():
    css_update(user_agent='css updater [praw]', user=sys.argv[1], password=sys.argv[2], subr_name=sys.argv[3], cssfile=sys.argv[4])

if __name__ == '__main__':
    main()
