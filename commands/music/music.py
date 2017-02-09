import discord
import json

from discord.ext import commands
from .voice import VoiceState, VoiceEntry
from utils import extract, checks, role_check, search, str_split, get_lyrics

if not discord.opus.is_loaded():
    discord.opus.load_opus('opus')

INIT0 = '205346839082303488'


class Music:
    """Voice related commands.
    Works in multiple servers at once.
    """

    def __init__(self, bot):
        self.bot = bot
        self.voice_states = {}

    def get_voice_state(self, server):
        state = self.voice_states.get(server.id)
        if state is None:
            state = VoiceState(server, self.bot, self)
            self.voice_states[server.id] = state

        return state

    async def create_voice_client(self, channel):
        state = self.get_voice_state(channel.server)
        voice = await self.bot.join_voice_channel(channel)
        state.voice = voice

    def __unload(self):
        for state in self.voice_states.values():
            try:
                state.audio_player.cancel()
                if state.voice:
                    self.bot.loop.create_task(state.voice.disconnect())
            except:
                pass

    async def summon(self, ctx):
        """Summons the bot to join your voice channel."""
        state = self.get_voice_state(ctx.message.server)
        if state.voice is None:
            try:
                state.voice = await self.bot.join_voice_channel(ctx.message.author.voice_channel)
            except discord.ClientException:
                await self.bot.voice_client_in(ctx.message.server).disconnect()
                state.voice = await self.bot.join_voice_channel(ctx.message.author.voice_channel)
        else:
            await state.voice.move_to(ctx.message.author.voice_channel)

    @commands.command(pass_context=True)
    @checks()
    async def playlistadd(self, ctx, *, server_id):
        _id = server_id if server_id is not None else ctx.message.server.id
        log = self.bot.log
        if _id not in log["playlist_servers"]:
            log["playlist_servers"].append(_id)
        else:
            await self.bot.say("this server is already in the list")
            return
        with open("log.json", "w") as file:
            json.dump(log, file, indent=4)
        await self.bot.say("adding %s to playlist servers" % (ctx.message.server.name if server_id is None else _id))

    @commands.command(pass_context=True, no_pm=True)
    @role_check()
    async def play(self, ctx, *, song: str):
        state = self.get_voice_state(ctx.message.server)
        shuffle = False
        in_playlist = ctx.message.server.id in self.bot.log['playlist_servers'] or ctx.message.author.id == INIT0
        if "shuffle" in song.split()[0]:
            shuffle = True
            song = song[8:]
        if "init0" in song:
            song = "https://www.youtube.com/playlist?list=PLzME6COik-H9hSsEuvAf26uQAN228ESck&disable_polymer=true"
            in_playlist = True
        try:
            summoned_channel = ctx.message.author.voice_channel
            if summoned_channel is None:
                await self.bot.say('You are not in a voice channel.')
                return
            entry = await extract(song, self.bot.loop, in_playlist, shuffle)
            if entry == 1:
                await self.bot.say('your server has not been registered to play playlists')
                return
            if entry == "ew it's an arab server":
                await self.bot.leave_server(ctx.message.server)
                await state.disconnect()
                return
            if entry[1]:
                await self.bot.say('some songs have been omitted due to duration, the omitted titles are')
                await self.bot.say("\n".join(entry[1]))
            if len(entry[0]) < 1:
                return
        except Exception as e:
            fmt = 'An error occurred while processing this request: ```py\n{}: {}\n```'
            await self.bot.send_message(ctx.message.channel, fmt.format(e.__class__.__name__, e))
            raise e

        else:
            if state.voice is None or not state.is_playing():
                try:
                    await self.summon(ctx)
                except Exception as e:
                    await self.bot.say('Error: {}, {}'.format(e.__class__.__name__, e))
                    raise Exception
            duration = 0
            ventry = None
            for i in entry[0]:
                duration += i.duration
                ventry = VoiceEntry(ctx.message, i)
                state.songlist.append(ventry)
            if len(entry[0]) > 1:
                entry_msg = "Enqueued {0} songs with a running time of {1[0]}m {1[1]}s".format(len(entry[0]), divmod(duration, 60))
            else:
                entry_msg = "Enqueued "+str(ventry)
            await self.bot.say(entry_msg)
            state.start()

    @commands.command(pass_context=True, no_pm=True)
    @role_check()
    async def pause(self, ctx):
        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            player.pause()
        else:
            await self.bot.say('not playing anything')
            return
        await self.bot.say('paused current song')

    @commands.command(pass_context=True, no_pm=True)
    async def resume(self, ctx):
        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            player.resume()
        else:
            await self.bot.say('not playing anything')
            return
        await self.bot.say('resumed current song')

    @commands.command(pass_context=True, no_pm=True)
    @commands.cooldown(1, 5, commands.BucketType.server)
    @role_check()
    async def stop(self, ctx):
        server = ctx.message.server
        state = self.voice_states[server.id] if server.id in self.voice_states.keys() else None

        if state is None:
            await self.bot.say('not playing anything')
            return

        if state.current.requester.id == INIT0 and ctx.message.author.id != INIT0:
            await self.bot.say("nah this song is good")
            return

        if ctx.message.author.server_permissions.mute_members or 'himebot_music' in [i.name for i in
                                            ctx.message.author.roles] or ctx.message.author.id == INIT0:
            state.stop = True
            try:
                await state.disconnect()
            except:
                pass
            if server.id in self.voice_states.keys():
                self.voice_states[server.id].voice.disconnect()
                del self.voice_states[server.id]
            elif self.bot.voice_client_in(server) is not None:
                await self.bot.voice_client_in(server).disconnect()
            await self.bot.say('stopped the current player')
        else:
            await self.bot.say('not enuff perms')

    @commands.command(pass_context=True, no_pm=True)
    @role_check()
    async def skip(self, ctx, count=0):
        """Vote to skip a song. The song requester can automatically skip.
        3 skip votes are needed for the song to be skipped.
        """

        if count < 0:
            await self.bot.say('skip count needs to be greater than, or 0')
            return

        state = self.get_voice_state(ctx.message.server)
        if not state.is_playing():
            await self.bot.say('Not playing any music right now...')
            return

        voter = ctx.message.author
        if voter not in state.voice.channel.voice_members and voter.id != INIT0:
            await self.bot.say('you are not in the current playing voice channel')
            return

        if state.current.requester.id == INIT0 and voter.id != INIT0:
            await self.bot.say('nah this song is good')
            return

        if count not in state.skip_votes.keys():
            state.skip_votes[count] = []
        if voter.id not in state.skip_votes[count]:
            state.skip_votes[count].append(voter.id)
            total_votes = len(state.skip_votes[count])
            if count == 0:
                if voter == state.current.requester or voter.id == INIT0:
                    await self.bot.say('Requester requested skipping song...')
                    await state.skip(count)
                    return
                elif total_votes >= state.votes_needed:
                    await self.bot.say('Skip vote passed, skipping song...')
                    await state.skip(count)
                else:
                    await self.bot.say('Skip vote added, currently at {}/{}'.format(total_votes, state.votes_needed))
            else:
                upcoming = [i for i in state.songlist[:count] if i.requester != voter]
                if len(upcoming) == 0 or voter.id == INIT0:
                    await self.bot.say('Requester requested skipping over %s song(s)...' % count)
                    await state.skip(count)
                    return
                elif total_votes >= state.votes_needed:
                    await self.bot.say('Skip vote passed, skipping over %s song(s)' % count)
                    await state.skip(count)
                else:
                    await self.bot.say(
                        'Skip vote added for skipping {} songs, currently at {}/{}'.format(count, total_votes,
                                                                                           state.votes_needed))
        else:
            await self.bot.say('You have already voted to skip this song.')

    @commands.command(pass_context=True, no_pm=True)
    async def current(self, ctx):
        state = self.get_voice_state(ctx.message.server)
        if state.current is None:
            await self.bot.say('Not playing anything.')
        else:
            skip_count = len(state.skip_votes[0])
            data = state.current.embed().add_field(
                name="Skip count", value="{}/{}".format(skip_count, state.votes_needed))
            try:
                await self.bot.say(embed=data)
            except discord.HTTPException:
                await self.bot.say("I need to be able to send embedded links")

    @commands.command(pass_context=True, no_pm=True)
    async def lyrics(self, ctx, *, song=None):
        if song is None:
            state = self.get_voice_state(ctx.message.server)
            if state.voice is not None:
                response = await self.bot.loop.run_in_executor(None, search, state.current.player.title)
            else:
                await self.bot.say("not playing anything currently, please specify a song")
                return
        else:
            response = await self.bot.loop.run_in_executor(None, search, song)

        if "lyrics" not in response and type(response) is not str:
            data = discord.Embed(
                color=discord.Color(value="16727871"),
                description="Select a song from below to get the lyrics for"
            )
            count = 0
            for i in response:
                count += 1
                data.add_field(name="{}. {}".format(count, i["primaryartist_name"]), value=i["title"], inline=False)
            try:
                await self.bot.say(embed=data)
            except discord.HTTPException:
                await self.bot.say("I need to be able to send embedded links")
            user_resp = await self.bot.wait_for_message(author=ctx.message.author, channel=ctx.message.channel)
            try:
                response = response[int(user_resp.content)-1]
                lyrics = await self.bot.loop.run_in_executor(None, get_lyrics, response["url"])
            except:
                await self.bot.say("please select a number between 1 and "+str(count))
            else:
                data = discord.Embed(
                    color=discord.Color(value="16727871"),
                )
                data.set_thumbnail(url=response["thumbnail"])
                data.set_author(name="Lyrics for "+response["title"])
                data.set_footer(text="Lyrics from genius.com")
                if len(lyrics) < 1200:
                    data.add_field(name="Lyrics", value=lyrics)
                else:
                    lyrics = str_split(lyrics)
                    try:
                        await self.bot.say(embed=data)
                    except discord.HTTPException:
                        await self.bot.say("I need to be able to send embedded links")
                    for i in lyrics:
                        await self.bot.say(i.replace("`", ""))
                    return
                try:
                    await self.bot.say(embed=data)
                except discord.HTTPException:
                    await self.bot.say("I need to be able to send embedded links")

        elif "lyrics" in response:
            lyrics = response["lyrics"]
            data = discord.Embed(
                color=discord.Color(value="16727871"),
            )
            data.set_thumbnail(url=response["thumbnail"])
            data.set_author(name="Lyrics for " + response["title"])
            data.set_footer(text="Lyrics from genius.com")
            if len(lyrics) < 1200:
                data.add_field(name="Lyrics", value=lyrics)
            else:
                lyrics = str_split(lyrics)
                try:
                    await self.bot.say(embed=data)
                except discord.HTTPException:
                    await self.bot.say("I need to be able to send embedded links")
                for i in lyrics:
                    await self.bot.say(i.replace("`", ""))
                return
            try:
                await self.bot.say(embed=data)
            except discord.HTTPException:
                await self.bot.say("I need to be able to send embedded links")
        else:
            await self.bot.say(response)

    @commands.command(pass_context=True, no_pm=True)
    async def songlist(self, ctx):
        state = self.get_voice_state(ctx.message.server)
        skip_count = len(state.skip_votes[0])
        data = discord.Embed(
            color=discord.Color(value="16727871"),
            title="Songs up next"
        )
        if len(state.songlist) < 1:
            await self.bot.say("nothing is in the queue currently")
            return
        for i in state.songlist:
            data.add_field(name="{}. {}".format(state.songlist.index(
                i) + 1, i.player.title), value="Skip count: {}/{}".format(skip_count, state.votes_needed), inline=False)
        try:
            await self.bot.say(embed=data)
        except discord.HTTPException:
            await self.bot.say("I need to be able to send embedded links")


def setup(bot):
    bot.add_cog(Music(bot))
