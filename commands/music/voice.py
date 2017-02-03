import asyncio
import glob
import discord


class VoiceEntry:
    def __init__(self, message, player):
        self.server = message.server.name
        self.requester = message.author
        self.channel = message.channel
        self.voice_channel = message.author.voice_channel
        self.player = player

    def __str__(self):
        fmt = '**{0.title}** uploaded by {0.uploader} and requested by {1.display_name}'
        duration = self.player.duration
        if duration:
            fmt += ' [length: {0[0]}m {0[1]}s]'.format(divmod(duration, 60))
        return fmt.format(self.player, self.requester)

    def embed(self):
        data = discord.Embed(
            color=discord.Color(value="16727871"),
            description=self.player.webpage_url
        )
        duration = self.player.duration
        data.add_field(name="Uploaded by", value=self.player.uploader)
        data.add_field(name="Requested by", value=self.requester.display_name)
        if duration:
            data.add_field(name="Duration", value='{0[0]}m {0[1]}s'.format(
                divmod(duration, 60)))
        data.set_author(name=self.player.title, url=self.player.webpage_url)
        data.set_thumbnail(url=self.player.thumbnail)
        data.set_footer(
            icon_url="https://images.discordapp.net/avatars/232916519594491906/42a9ab560aca4d5cdc50f37e7726005b.jpg",
            text="donate to hime for playlists and more at himebot.xyz")
        return data


class VoiceState:
    def __init__(self, server, bot, cog):
        self.server = server
        self.volume = 0.6
        self.stop = False
        self.current = None
        self.voice = None
        self.bot = bot
        self.cog = cog
        self.play_next_song = asyncio.Event()
        self.songs = asyncio.Queue()
        self.songlist = []
        self.skip_votes = {0: []}
        self.audio_player = self.bot.loop.create_task(self.audio_player_task())

    @property
    def votes_needed(self):
        return round(len([i.name for i in self.voice.channel.voice_members if i.name != self.bot.user.name]) * 0.6)

    @property
    def player(self):
        return self.current.player

    def is_playing(self):
        if self.voice is None or self.current is None:
            return False

        player = self.current.player
        try:
            return not player.is_done()
        except AttributeError:
            return False

    async def skip(self, count=0):
        self.skip_votes[count].clear()
        self.songlist = self.songlist[count:]
        if self.is_playing():
            self.player.stop()

        for i in range(count):
            await self.songs.get()

    def toggle_next(self):
        self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

    async def disconnect(self):
        if self.player is not None:
            self.player.stop()
        await self.voice.disconnect()
        self.audio_player.cancel()
        try:
            del self.cog.voice_states[self.server.id]
        except:
            pass

    async def create_player(self):
        entry = self.current
        # args = 'cache/{}.mp3'.format(entry.display_id)
        await entry.player.download()
        args = glob.glob('cache/{}.*'.format(entry.player.display_id))[0]
        player = self.voice.create_ffmpeg_player(args, before_options="-nostdin", options="-vn -b:v 128k", after=self.toggle_next)

        # TODO: find a way to iterate over this using getattr and setattr
        player.yt = entry.player.yt
        player.title = entry.player.title
        player.display_id = entry.player.display_id
        player.thumbnail = entry.player.thumbnail
        player.webpage_url = entry.player.webpage_url
        player.download_url = entry.player.download_url
        player.views = entry.player.views
        player.is_live = entry.player.is_live
        player.likes = entry.player.likes
        player.dislikes = entry.player.dislikes
        player.duration = entry.player.duration
        player.uploader = entry.player.uploader

        return player

    async def audio_player_task(self):
        while True:
            self.current = await self.songs.get()
            self.current.player = await self.create_player()
            self.play_next_song.clear()
            try:
                if not self.stop:
                    await self.bot.send_message(self.current.channel, "Now playing")
                    await self.bot.send_message(self.current.channel, embed=self.current.embed())
                self.songlist.pop(0)
            except:
                pass
            self.current.player.volume = self.volume
            self.current.player.start()
            await self.play_next_song.wait()
            if not self.songs.empty() or len(self.voice.channel.voice_members) < 2:
                if self.current.requester.voice_channel is not None:
                    await self.voice.move_to(self.current.requester.voice_channel)
                else:
                    await self.disconnect()
                    return
            else:
                await self.disconnect()
                return

