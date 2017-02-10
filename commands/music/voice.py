import asyncio
import glob
import discord
import traceback


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
        self.stop = False
        self.current = None
        self.voice = None
        self.bot = bot
        self.cog = cog
        self.songlist = []
        self.skip_votes = {0: []}
        self.blocking_call = asyncio.Event()
        self.audio_player = None

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

    def safe_after(self):
        try:
            coro = self.audio_player()  # self.bot.send_message(self.current.channel, "done playing")
            fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
            fut.result(0)
            return
        except Exception as e:
            pass  # traceback.print_tb(e.__traceback__)

    async def disconnect(self):
        await self.voice.disconnect()
        try:
            del self.cog.voice_states[self.server.id]
        except:
            pass

    def unblock(self):
        self.bot.loop.call_soon_threadsafe(self.blocking_call.set)

    async def audio_player_task(self):
        while True:
            self.current = self.songlist.pop(0)
            self.current.player = await self.create_player()
            try:
                if not self.stop:
                    await self.bot.send_message(self.current.channel, "Now playing")
                    await self.bot.send_message(self.current.channel, embed=self.current.embed())
            except discord.HTTPException:
                try:
                    await self.bot.send_message(self.current.channel, embed=self.current)
                except:
                    pass
            self.blocking_call.clear()
            self.current.player.start()
            await self.blocking_call.wait()
            if self.stop:
                await self.disconnect()
            elif len(self.songlist) == 0:
                await self.disconnect()
            elif len(self.voice.channel.voice_members) < 2:
                if self.current.requester.voice_channel is not None:
                    await self.voice.move_to(self.current.requester.voice_channel)
                else:
                    await self.disconnect()

    async def create_player(self):
        entry = self.current
        await entry.player.download()
        args = glob.glob('cache/{}.*'.format(entry.player.display_id))[0]
        player = self.voice.create_ffmpeg_player(args, before_options="-nostdin", options="-vn -b:a 128k",
                                                 after=self.unblock)

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

    def start(self):
        if not self.is_playing():
            self.audio_player = self.bot.loop.create_task(self.audio_player_task())
