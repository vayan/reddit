#!/usr/bin/env python

# Generate spritesheets and css for linking scrolls in /r/scrolls
#
# Thx to scrollsguide for the API !
# usage : python updatescrolls.py reddit_user reddit_pass subreddit
#
#

import urllib
import urllib2
import cStringIO
import json
import sys
from PIL import Image
import math
import string
import praw
import os
import time
import htmlentity2ascii
import cssmin

if len(sys.argv) < 4:
    print("Usage : %s reddit_user reddit_pass subreddit" % sys.argv[0])
    sys.exit(11)

base_api = "http://a.scrollsguide.com/"
user = sys.argv[1]
password = sys.argv[2]
subr_name = sys.argv[3]
spritesheetname = "spritesheet"
type_img = "jpg"
json_file= 'scrolls.json'


def getUrl(url):
    # google chrome user agent

    use_chrome_useragent = True
    if use_chrome_useragent:
        request = urllib2.Request(url)
        request.add_header("User-Agent", "Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36")
        f = urllib2.urlopen(request)
    else:
        f = urllib.urlopen(url)

    data = f.read()
    f.close()
    return data


def newImg(x, y):
    img = Image.new(
        mode='RGBA',
        size=(x, y),
        color=(0, 0, 0))
    return img


def get_all_scrolls(limit=0):  # limit number of dl for debug and being nice with the bandwidth of kbasten
    print("== Getting raw scrolls data...")
    scrolls = []

    sgapi_scrolls = json.loads(getUrl(base_api+"scrolls"))
    if sgapi_scrolls['msg'] == 'fail':  # error API request
        sys.exit(11)
    sg_scrolls = sgapi_scrolls['data']
    for scroll in sg_scrolls:
        if (limit != 0) and (len(scrolls) >= limit):
            return scrolls
        img_url = '%simage/screen?%s&size=small' % (base_api, urllib.urlencode({'name': scroll['name']}))  # img api url
        scrolls.append({"name": scroll['name'], "img_url": img_url, "id": scroll['id']})  # only get the usefull data
    print("Done!")
    return scrolls


def download_images(scrolls):  # store all image in list
    print("== Getting all images...\nStarting..")
    nb_sc = len(scrolls)
    i = 1
    for scroll in scrolls:
        done = False
        while not done:
            try:
                scroll['image'] = Image.open(cStringIO.StringIO(getUrl(scroll['img_url'])))
                done = True
            except IOError:
                print(scroll['img_url'])
                print("Rate limit exceeded - sleeping for 5s and trying again")
                print("------------------------------------------------------")
                time.sleep(5)
        print("%d/%d %s" % (i, nb_sc, scroll['name']))
        i += 1
    print("Done! got %s images\nStarting spritesheet" % len(scrolls))


def upload_spritesheets(nb_spritesheets, spritesheetname, type_img, remove = False):
    print ("Starting spritesheet upload...\nConnecting to reddit")
    r = praw.Reddit(user_agent='img css uploader [praw]')
    r.login(user, password)
    subreddit = r.get_subreddit(subr_name)
    print("Connected!\nUploading images...")
    for i in xrange(0, nb_spritesheets+1):
        filename = "%s-%d.%s" % (spritesheetname, i, type_img)
        print("uploading " + filename)
        subreddit.upload_image(filename, "%s-%d" % (spritesheetname, i))
        if remove: #keep them for caching purpose
            os.remove(filename)
    print("All done!")


def update_css(css):
    print ("Starting update css...\nConnecting to reddit")
    splitkey = "/**botcss**/"
    r = praw.Reddit(user_agent='css updater [praw]')
    r.login(user, password)
    print("Connected!\nUpdating css...")
    subreddit = r.get_subreddit(subr_name)

    # wtf T_T why htmlentity2ascii ? idk bug without...
    cur_css = htmlentity2ascii.convert(subreddit.get_stylesheet()['stylesheet'].split(splitkey, 1)[0])
    print('minimizing css before upload..')
    newcss = '%s\n%s\n%s\n' % (cssmin.cssmin(cur_css, False), splitkey, cssmin.cssmin(css, False))
    save_css(newcss)
    subreddit.set_stylesheet(newcss)
    print ('Done!')
    return newcss

def save_css(css):
    with open('spritesheetdata.css', 'w') as f:
        f.write(css)


def gen_css(spritesheetname, scrolls):
    statichover = ".content a[href*=\"##\"]:hover{font-size: 0em; height: 375px; width: 210px; z-index: 6;}"
    staticafter = ".content a[href*=\"##\"]::after{content: \"[error: scrolls not found]\";margin-left: 1px;  font-size: 0.6em; color: rgb(255,137,0);}"
    staticallrules = ".content a[href*=\"##\"]{display: inline-block; cursor:default; clear: both; padding-top:5px; margin-right: 2px;}"
    css, all_css, all_css_hover, all_css_after = "", "\n", "", ""
    for scroll in scrolls:
        sprite_name = "%s-%d" % (spritesheetname, scroll['sprite_id'])
        name = string.lower(scroll['name']).replace(" ", "").replace(",","")
        #all_css += ".content a[href=\"##" + name + "\"], "  # css rules for all scrolls
        #all_css_hover += ".content a[href=\"##" + name + "\"]:hover, "
        #all_css_after += ".content a[href=\"##" + name + "\"]::after, "
        css += (".content a[href=\"##" + name + "\"]:hover {background-image: url(%%" + sprite_name + "%%);  background-position: -"+str(scroll['pos'][0])+"px -" + str(scroll['pos'][1]) + "px; }\n")
        css += (".content a[href=\"##" + name + "\"]::after {content: \"[" + scroll['name'] + "]\";}\n")
    all_css = all_css[:-2] + staticallrules
    all_css_hover = all_css_hover[:-2] + statichover
    all_css_after = all_css_after[:-2] + staticafter
    css = all_css + "\n" + all_css_hover + "\n" + all_css_after + css
    return css


def spritesheeter(scrolls):
    nb_per_sheet, quality_jpeg = 20, 90
    loc_y, loc_x, i, img_process, cur_spritesheet = 0, 0, 0, 0, 0
    download_images(scrolls)
    image_w, image_h = scrolls[0]['image'].size
    perline = (int)(round(math.sqrt(nb_per_sheet)))  # 'perfect size' spritesheet
    master_w = image_w * perline
    master_h = image_h * perline
    spritesheet = newImg(master_w, master_h)
    for scroll in scrolls:
        spritesheet.paste(scroll['image'], (loc_x, loc_y))  # paste image in spritesheet
        scroll['sprite_id'], scroll['pos'] = cur_spritesheet, (loc_x, loc_y)  # store data for css rules
        loc_x += image_w
        i += 1
        if i == perline:
            loc_x, i = 0, 0
            loc_y += image_h
        img_process += 1
        if img_process == (perline*perline):  # change of spritesheet to avoid big files
            print ("Want save %d spritesheet" % cur_spritesheet)
            spritesheet.save("%s-%d.%s" % (spritesheetname, cur_spritesheet, type_img), quality=quality_jpeg)  # save file
            spritesheet = newImg(master_w, master_h)
            loc_y, loc_x, img_process = 0, 0, 0  # reset everything
            cur_spritesheet += 1
            print ("Saved! Continue..")
    print("Last spritesheet...")
    spritesheet.save("%s-%d.%s" % (spritesheetname, cur_spritesheet, type_img), quality=quality_jpeg)  # save the scrolls left
    print("All done ! Gen css")
    return cur_spritesheet


def save_scrolls(scrolls):
    # Save scrolls data to disk, so you don't have to download it again
    # you might have to clear the image data first:
    for scroll in scrolls:
        del scroll['image']
    scrolls_json = json.dumps(scrolls)
    with open(json_file, 'w') as f:
        f.write(scrolls_json)

def load_scrolls():
    with open(json_file) as f:
        scrolls_json = f.read()
    return json.loads(scrolls_json)

def main():
    try :
        print ("Try to load data from cache")
        scrolls = load_scrolls()
        css = gen_css(spritesheetname, scrolls)
        print ("worked !")
        save_css(css)
        css = update_css(css)
        save_css(css)
    except IOError :
        print ("Didn't work..reload from server !")
        main_download()

def main_download():
    scrolls = get_all_scrolls()
    nb_spritesheet = spritesheeter(scrolls)
    save_scrolls(scrolls)
    upload_spritesheets(nb_spritesheet, spritesheetname, type_img)
    css = gen_css(spritesheetname, scrolls)
    css = update_css(css)
    save_css(css)

if __name__ == '__main__':
    main()
