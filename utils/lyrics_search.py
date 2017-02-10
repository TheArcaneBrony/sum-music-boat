import urllib.parse
import urllib.request
import json
import socket
import requests

from bs4 import BeautifulSoup


def get_lyrics(song_url):
    page = requests.get(song_url)
    html = BeautifulSoup(page.text, 'html.parser')
    # remove script tags that they put in the middle of the lyrics
    [h.extract() for h in html('script')]
    # at least Genius is nice and has a tag called 'lyrics'!
    lyrics = html.find('lyrics').get_text()
    return lyrics


def search(search_term, client_access_token='0BMySNDi4mkoYFno6cXI0hGdUB_m-wMR0ZYkGn-Blnp_WEYLrbyJE7vRTcLQrs7f'):
    output = []
    querystring = 'http://api.genius.com/search?q=' + urllib.parse.quote(search_term) + '&page=1'
    request = urllib.request.Request(querystring)
    request.add_header('Authorization', 'Bearer ' + client_access_token)
    request.add_header('User-Agent',
                       'curl/7.9.8 (i686-pc-linux-gnu) libcurl 7.9.8 (OpenSSL 0.9.6b) (ipv6 enabled)')
    while True:
        try:
            response = urllib.request.urlopen(request,
                                              timeout=4)  # timeout set to 4 seconds; automatically retries if times out
            raw = response.read().decode()
        except socket.timeout:
            print('Timeout raised and caught')
            continue
        break
    json_obj = json.loads(raw)
    body = json_obj['response']['hits']

    num_hits = len(body)
    if num_hits == 0:
        return 'No results for: ' + search_term
    elif num_hits == 1:
        result = body[0]
        return {
            'result_id': result['result']['id'],
            'title': result['result']['title'],
            'url': result['result']['url'],
            'path': result['result']['path'],
            'thumbnail':  result['result']['song_art_image_thumbnail_url'],
            'header_image_url': result['result']['header_image_url'],
            'annotation_count': result['result']['annotation_count'],
            'pyongs_count': result['result']['pyongs_count'],
            'primaryartist_id': result['result']['primary_artist']['id'],
            'primaryartist_name': result['result']['primary_artist']['name'],
            'primaryartist_url': result['result']['primary_artist']['url'],
            'primaryartist_imageurl': result['result']['primary_artist']['image_url'],
            'lyrics': get_lyrics(result['result']['url'])
        }
    for result in body:
        _output = {
            'result_id': result['result']['id'],
            'title': result['result']['title'],
            'url': result['result']['url'],
            'path': result['result']['path'],
            'thumbnail':  result['result']['song_art_image_thumbnail_url'],
            'header_image_url': result['result']['header_image_url'],
            'annotation_count': result['result']['annotation_count'],
            'pyongs_count': result['result']['pyongs_count'],
            'primaryartist_id': result['result']['primary_artist']['id'],
            'primaryartist_name': result['result']['primary_artist']['name'],
            'primaryartist_url': result['result']['primary_artist']['url'],
            'primaryartist_imageurl': result['result']['primary_artist']['image_url'],
        }
        output.append(_output)

    return output
