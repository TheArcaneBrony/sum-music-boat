import youtube_dl
import functools
import glob
import random

from langdetect import detect
from functools import partial


class Extract:

    def __init__(self, loop, thread_pool=None):
        self.loop = loop
        self.thread_pool = thread_pool
        self.info = None
        self.title = None
        self.url = None
        self.yt = None
        self.display_id = None
        self.webpage_url = None
        self.thumbnail = None
        self.upload_url = None
        self.download_url = None
        self.views = None
        self.is_live = None
        self.likes = None
        self.dislikes = None
        self.duration = None
        self.fmt_duration = None
        self.uploader = None
        self.description = None

    async def download(self):
        opts = {
            'default_search': 'auto',
            'force_ipv4': True,
            'source_address': '0.0.0.0',
            'playlist_items': '0',
            'playlist_end': '0',
            'noplaylist': True,
            'outtmpl': 'cache/%(id)s.%(ext)s',
            'no_warnings': True,
            'quiet': True
        }
        ydl = youtube_dl.YoutubeDL(opts)
        in_cache = glob.glob('cache/{}.*'.format(self.info['display_id']))
        if len(in_cache) == 0:
            await self.loop.run_in_executor(self.thread_pool, functools.partial(ydl.download, [self.webpage_url]))

async def extract(url, loop, in_playlist, shuffle=False, thread_pool=None):
    opts = {
        'default_search': 'auto',
        'force_ipv4': True,
        'source_address': '0.0.0.0',
        'playlistend': 50,
        'no_warnings': True,
        'quiet': True
    }
    obj_list = []
    omitted = []
    ydl = youtube_dl.YoutubeDL(opts)
    func = functools.partial(ydl.extract_info, url, download=False)
    info = await loop.run_in_executor(thread_pool, func)

    if 'entries' in info:
        info = info['entries']
    else:
        info = [info]

    if not in_playlist and len(info) > 1:
        return 1

    for i in info:
        if not i['duration'] > 3600:
            extract_obj = Extract(loop, thread_pool)
            extract_obj.info = i

            extract_obj.url = url
            extract_obj.yt = ydl
            extract_obj.display_id = i.get('display_id')
            extract_obj.thumbnail = i.get('thumbnail')
            extract_obj.webpage_url = i.get('webpage_url')
            extract_obj.download_url = i.get('download_url')
            extract_obj.views = i.get('view_count')
            extract_obj.is_live = bool(i.get('is_live'))
            extract_obj.likes = i.get('like_count')
            extract_obj.dislikes = i.get('dislike_count')
            extract_obj.duration = i.get('duration')
            extract_obj.fmt_duration = "{0[0]}m {0[1]}s".format(divmod(extract_obj.duration, 60))
            extract_obj.uploader = i.get('uploader')

            is_twitch = 'twitch' in url
            if is_twitch:
                # twitch has 'title' and 'description' sort of mixed up.
                extract_obj.title = i.get('description')
                extract_obj.description = None
            else:
                extract_obj.title = i.get('title')
                extract_obj.description = i.get('description')

            try:
                output = await loop.run_in_executor(thread_pool, partial(detect, extract_obj.title))
                if output == 'ar':
                    return 'ew it\'s an arab server'
            except:
                pass
            obj_list.append(extract_obj)
        else:
            omitted.append(i['title'])

    if shuffle:
        random.shuffle(obj_list)

    return [obj_list, omitted]
