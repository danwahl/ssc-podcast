from datetime import datetime
from io import BytesIO
import os
import pytz
import re
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


def get_audio(text):
    response = polly_client.synthesize_speech(
        VoiceId='Matthew', Engine='neural', OutputFormat='mp3', Text=text)
    seg = BytesIO()
    seg.write(response['AudioStream'].read())
    seg.seek(0)
    return seg


if __name__ == '__main__':
    # setup nltk tokenizer
    # uncomment following line on first run
    # nltk.download('punkt')
    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

    # setup polly client
    # todo(dan): move keys to separate file
    polly_client = boto3.Session(
        aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
        region_name='us-west-2').client('polly')

    # setup urllib pool manager
    http = urllib3.PoolManager()

    # get and parse archives
    res = http.request('GET', SSC_ARCHIVES)
    soup = BeautifulSoup(res.data, "html.parser")

    # get divs containing post links, iterate through list in reverse order
    divs = soup.find_all('div', attrs={'class': 'sya_postcontent'})
    for div in divs[::-1]:
        # get post url
        url = link = div.find('a', href=True)['href']

        # get post name and build podcast filename
        name = url.split('/')[-2]
        filename = name + '.mp3'

        # check if filename already exists in podcasts folder, skip if so
        if filename in os.listdir(PODCASTS_PATH):
            continue
        else:
            print(name)

        # get post and parse
        res = http.request('GET', url)
        soup = BeautifulSoup(res.data, "html.parser")

        # get post content, get author, title, date, and time
        post = soup.find('div', attrs={'id': re.compile(r'post\-\d+')})
        author = post.find('a', attrs={'class': 'url fn n'}).text
        title = post.find('h1', attrs={'class': 'pjgm-posttitle'}).text
        date = post.find('span', attrs={'class': 'entry-date'}).text
        time = post.find(
            'div', attrs={
                'class': 'pjgm-postmeta'}).find('a').get('title')

        # create timezone aware datetime object from date and time
        dt = datetime.strptime(' '.join([date, time]), '%B %d, %Y %I:%M %p')
        dtz = pytz.timezone("US/Pacific").localize(dt)

        # initialize pydub object, add introduction
        podcast = AudioSegment.silent(PARAGRAPH_SILENCE)
        intro = title + '\r\n\r\nPosted on ' + date + ' by' + author
        podcast += AudioSegment.from_mp3(get_audio(intro))
        podcast += AudioSegment.silent(PARAGRAPH_SILENCE)

        # split post into paragraphs, iterate through list
        paragraphs = post.find_all('p')
        for paragraph in paragraphs:
            # split paragraph into sentences, iterate through each
            sentences = tokenizer.tokenize(paragraph.text)
            for sentence in sentences:
                # add sentence audio and silence to podcast
                podcast += AudioSegment.from_mp3(get_audio(sentence))
                podcast += AudioSegment.silent(duration=SENTENCE_SILENCE)
            # add slightly longer pause between paragraphs
            podcast += AudioSegment.silent(PARAGRAPH_SILENCE -
                                           SENTENCE_SILENCE)

        # export podcast, get file duration and length
        podcast.export(
            PODCASTS_PATH +
            filename,
            format='mp3',
            tags={
                'artist': author,
                'title': title})
        duration = round(podcast.duration_seconds)
        length = os.stat(PODCASTS_PATH + filename).st_size

        # generate markdown text and write to post
        markdown = '''---\nlayout: podcast\ntitle: "%s"\nauthor: %s\ndescription: %s\ndate: %s\nlength: %d\nduration: %d\nguid: %s\n---''' % (
            title, author, url, dtz.strftime('%Y-%m-%d %H:%M:%S %Z'), length, duration, name)
        with open(POSTS_PATH + dtz.strftime('%Y-%m-%d-') + name + '.md', 'w') as f:
            f.write(markdown)

        break
