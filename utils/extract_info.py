import youtube_dl
import functools
import glob
import random

from langdetect import detect
from functools import partial


class Extract:

    def __init__(self, loop):
        self.loop = loop
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
        self.uploader = None
        self.description = None

    async def download(self):
        opts = {
            'default_search': 'auto',
            'force_ipv4': True,
            'source_address': '0.0.0.0',
            "playlist_items": "0",
            "playlist_end": "0",
            "noplaylist": True,
            "outtmpl": 'cache/%(id)s.%(ext)s',
            "no_warnings": True,
            "quiet": True
        }
        ydl = youtube_dl.YoutubeDL(opts)
        in_cache = glob.glob("cache/{}.*".format(self.info['display_id']))
        if len(in_cache) == 0:
            await self.loop.run_in_executor(None, functools.partial(ydl.download, [self.webpage_url]))

async def extract(url, loop, in_playlist, shuffle=False):
    opts = {
        'default_search': 'auto',
        'force_ipv4': True,
        'source_address': '0.0.0.0',
        'playlistend': 50,
        "no_warnings": True,
        "quiet": True
    }
    obj_list = []
    omitted = []
    ydl = youtube_dl.YoutubeDL(opts)
    func = functools.partial(ydl.extract_info, url, download=False)
    info = await loop.run_in_executor(None, func)

    if "entries" in info:
        info = info["entries"]
    else:
        info = [info]

    if not in_playlist and len(info) > 1:
        return 1

    for i in info:
        if not i['duration'] > 3600:
            extractObj = Extract(loop)
            extractObj.info = i

            extractObj.url = url
            extractObj.yt = ydl
            extractObj.display_id = i.get('display_id')
            extractObj.thumbnail = i.get('thumbnail')
            extractObj.webpage_url = i.get('webpage_url')
            extractObj.download_url = i.get('download_url')
            extractObj.views = i.get('view_count')
            extractObj.is_live = bool(i.get('is_live'))
            extractObj.likes = i.get('like_count')
            extractObj.dislikes = i.get('dislike_count')
            extractObj.duration = i.get('duration')
            extractObj.uploader = i.get('uploader')

            is_twitch = 'twitch' in url
            if is_twitch:
                # twitch has 'title' and 'description' sort of mixed up.
                extractObj.title = i.get('description')
                extractObj.description = None
            else:
                extractObj.title = i.get('title')
                extractObj.description = i.get('description')

            try:
                output = await loop.run_in_executor(None, partial(detect, extractObj.title))
                if output == 'ar':
                    return "ew it's an arab server"
            except:
                pass
            obj_list.append(extractObj)
        else:
            omitted.append(i['title'])

    if shuffle:
        random.shuffle(obj_list)

    return [obj_list, omitted]
