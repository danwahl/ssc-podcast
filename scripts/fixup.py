from datetime import datetime
from io import BytesIO
import os
import pytz
import re
import sys
import urllib3

from bs4 import BeautifulSoup
from pydub import AudioSegment
import boto3
import nltk.data

# silence timing, in ms
PARAGRAPH_SILENCE = 557
SENTENCE_SILENCE = 316

# relative directory paths
PODCASTS_PATH = '../podcasts/'
POSTS_PATH = '../_posts/'

# link to ssc archives
SSC_ARCHIVES = 'https://slatestarcodex.com/archives/'

# parsers
PARSERS = ("html.parser", "html5lib")


if __name__ == '__main__':
    num = 0

    # setup nltk tokenizer
    # uncomment following line on first run
    # nltk.download('punkt')
    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

    # setup urllib pool manager
    http = urllib3.PoolManager()

    # get and parse archives
    res = http.request('GET', SSC_ARCHIVES)
    soup = BeautifulSoup(res.data, 'html5lib')

    # get divs containing post links, iterate through list in reverse order
    divs = soup.find_all('div', attrs={'class': 'sya_postcontent'})
    for div in divs[::-1]:
        # get post url
        url = link = div.find('a', href=True)['href']

        # get post name and build podcast filename
        name = url.split('/')[-2]

        podcasts = {}
        for parser in PARSERS:
            # get post and parse
            res = http.request('GET', url)
            soup = BeautifulSoup(res.data, parser)

            # get post content, get author, title, date, and time
            post = soup.find('div', attrs={'id': re.compile(r'post\-\d+')})
            author = post.find('a', attrs={'class': 'url fn n'}).text
            title = post.find('h1', attrs={'class': 'pjgm-posttitle'}).text
            date = post.find('span', attrs={'class': 'entry-date'}).text
            time = post.find(
                'div', attrs={
                    'class': 'pjgm-postmeta'}).find('a').get('title')

            # create timezone aware datetime object from date and time
            dt = datetime.strptime(
                ' '.join([date, time]), '%B %d, %Y %I:%M %p')
            dtz = pytz.timezone("US/Pacific").localize(dt)

            # initialize podcast string, add introduction
            podcast = ""
            intro = title + '\r\n\r\nPosted on ' + date + ' by ' + author
            podcast += intro
            podcast += "\r\n\r\n"

            # split post into paragraphs, iterate through list
            paragraphs = post.find_all('p')
            for paragraph in paragraphs:
                # split paragraph by new lines, iterate through list
                for line in paragraph.text.split('\n'):
                    # split line into sentences, iterate through each
                    sentences = tokenizer.tokenize(line)
                    for sentence in sentences:
                        # add sentence and silence to podcast
                        podcast += sentence

            podcasts[parser] = podcast

        # uncomment to process single post
        if len(set(podcasts.values())) > 1:
            print(dtz.strftime('%Y-%m-%d,') + name + ",%.2f" % (len(podcasts[PARSERS[0]])/len(podcasts[PARSERS[1]])))
            num += 1

    # return 0 if podcasts added, otherwise 1
    sys.exit(0 if num else 1)
