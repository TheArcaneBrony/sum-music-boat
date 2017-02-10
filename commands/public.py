import discord
import requests
import random
import urllib3
import re

from discord.ext import commands
from utils import channel_check

HELP = ['''
options included in [] are optional

General cmds for fgts:
**.help**: returns help command
**.randint [start | end]**: rolls a random number in the specified range, if no numbers are specified, roll a random number between 0 and 100
**.cal expression**: calculates an arithemetical expression
**.lookup ip**: lookup an ip
**.discrim [user]**: looks up if *user*'s discriminator is in the bot's user database, will assume *user* is the message author if *user* is not given
**.define word**: looks up a definition for the word in urban dictionary
**.invite**: for inviting the bot
**.botinfo**: tf do u think?
**.serverinfo**: returns some info about the server
**.userinfo [user]**: returns some info about the user, will assume *user* is the message author if *user* is not given
**mention me or call my name**: to have a nice chat with me
**.rule34**: :smirk:
''', '''Music cmds:
**.play [shuffle *for playlists only*] name of song/url**: play a song with url or song name. Searches on yt for the song if no url not specified. Use this to summon bot aswell.
**.skip [count]**: vote to skip a song. Skip over *count* songs if count is given
**.pause**: pause the song
**.resume**: resume the song
**.stop**: stops the bot from playing, and makes it leave the channel
**.current**: shows info about the current song
**.songlist**: shows all the queued songs to be played
**.lyrics [song]**: searches for the lyrics of a song on https://genius.com, will use the current playing song if *song* is omitted.

Advanced cmds that need advanced perms:
**.logging**: enable or disable logging. If enabled, the bot will send server logs to a channel named logs. Logs include: message delete/edit, member join/leave and member ban/unban
**.createinvite**: creates an instant invite in the current server
**.ban fgt**: ban a fgt
**.kick fgt**: replace ban with kick^
**.clear**: sends 1000 lines of NULL chars to clear the chat
**.purge [member] [amount]**: this takes a lot to explain xd. Go to https://www.himebot.xyz for help
**.serverprefix [prefix]**: changes the . prefix to the prefix specified. Though you can still execute commands by mentioning the bot or calling its name
''', '''Misc stuff:
**don't want people spamming nsfw stuff?**: simply make a channel named `nsfw`, this will make it so that they can only use nsfw commands in that channel
**don't want random plebs using music?**: you can choose who can execute music commands by adding a role named `himebot_music` in your server. This will make it so that only people with the role can execute music commands, apart from .current and .songlist
''']

INVITE = '''
Invite me here
https://discordapp.com/oauth2/authorize?client_id=232916519594491906&scope=bot&permissions=536063039

My server
https://discord.gg/b9RCGvk
'''

NUDES = [
    'https://goo.gl/8jjmeR'
]


def r34(query):
    http = urllib3.PoolManager()
    request = http.request(
        'GET', 'http://cloud.rule34.xxx/index.php?page=dapi&s=post&q=index&tags={}&limit=1000'.format(query)).data.decode()
    links = [i for i in re.findall('cloudimg\.rule34[^"]+', request) if 'thumbnails' not in i]
    if len(links) > 0:
        return 'http://' + random.choice(links)
    return 'couldn\'t match the query'


class Public:

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def say(self, ctx, *, msg):
        await self.bot.say(msg)

    @commands.command(pass_context=True)
    async def help(self, ctx):
        for i in HELP:
            await self.bot.send_message(ctx.message.author, i)

    @commands.command(pass_context=True)
    async def lookup(self, ctx, ip):
        verify = ip.replace('.', '')
        if verify.isdigit():
            r = requests.get(
                'http://ip-api.com/json/{}'.format(ip), allow_redirects=True).json()

            data = discord.Embed(
                description='Information about this IP',
                color=discord.Color(value='16727871')
            )

            r = {key: str(val) for key, val in r.items()}

            data.add_field(name='Country', value=r['country'])
            data.add_field(name='City', value=r['city'])
            data.add_field(name='Zipcode', value=r['zip'])
            data.add_field(name='Region', value=r['region'])
            data.add_field(name='Timezone', value=r['timezone'])
            data.add_field(name='Latitude', value=r['lat'])
            data.add_field(name='Longitude', value=r['lon'])
            data.add_field(name='ISP', value=r['isp'])
            data.add_field(name='Org', value=r['org'])

            data.set_author(name=ip, url='http://ip-api.com/{}'.format(ip))

            try:
                await self.bot.say(embed=data)
            except discord.HTTPException:
                await self.bot.say('I need to be able to send embedded links')
        else:
            await self.bot.say('you dumb or wat, is that an ip?')

    @commands.command(pass_context=True)
    async def discrim(self, ctx, member: discord.Member = None):
        '''Finds a username that you can use to change discrim'''

        d = ctx.message.author if member is None else member
        f = discord.utils.find(lambda x: x.discriminator == d.discriminator and not x.id == d.id,
                               self.bot.get_all_members())
        if f is not None:
            if member is None:
                await self.bot.say(
                    'If you change your username to `{}` then you will get a new discriminator'.format(f.name))
            else:
                await self.bot.say(
                    'If they change their username to `{}` then they will get a new discriminator'.format(f.name))
        else:
            if member is None:
                await self.bot.say('I couldn\'t find anyone with your discriminator in my database')
            else:
                await self.bot.say('I couldn\'t find anyone with %s\'s discriminator in my database' % member)

    @commands.command(pass_context=True)
    async def define(self, ctx, *, word):
        if ' ' in word:
            word = word.replace(' ', '+')

        try:
            r = requests.get(
                'http://api.urbandictionary.com/v0/define?term={}'.format(word), allow_redirects=True).json()
            definition = r['list'][0]['definition']
            example = r['list'][0]['example']

            data = discord.Embed(colour=discord.Colour(value='16727871'))

            data.add_field(name='Definition', value=str(definition), inline=False)
            data.add_field(name='Example', value=str(example))
            data.set_footer(text='Definition from Urban Dictionary', icon_url='https://encrypted-tbn3.gstatic.com/images?q=tbn:ANd9GcRo8KLHlAQXYao2X7D1G5rFS03GUG59KMNOP22RYHPqvmmBHREKctHRog')

            try:
                await self.bot.say(embed=data)
            except discord.HTTPException:
                await self.bot.say('I need to be able to send embedded links')
        except:
            await self.bot.say('no definition found for this word')

    @commands.command(pass_context=True)
    async def randint(self, ctx, start: int=0, end: int=100):
        await self.bot.say(random.randint(start, end))

    @commands.command(pass_context=True)
    async def cal(self, ctx, *, exp):
        args = ''.join(exp.split())
        disallowed = ['**', '/0', '-0', '+0']
        allowed = '0123456789\/*-+.() '
        wl_fail = False
        bl_fail = False

        for i in args:
            if i not in allowed:
                wl_fail = True

        for i in disallowed:
            if i in args:
                bl_fail = True

        if wl_fail or bl_fail:
            await self.bot.say('did you just try to eval bomb me u dickhead')
        else:
            try:
                data = discord.Embed(colour=discord.Colour(value='16727871'))

                data.add_field(name='Input', value=str(args), inline=False)
                data.add_field(name='Output', value=str(eval(args)))

                try:
                    await self.bot.say(embed=data)
                except discord.HTTPException:
                    await self.bot.say('I need to be able to send embedded links')
            except SyntaxError:
                await self.bot.say('wtf did you enter??')

    @commands.command(pass_context=True, no_pm=True)
    async def serverinfo(self, ctx):
        server = ctx.message.server
        online = len([m.status for m in server.members
                      if m.status == discord.Status.online or
                      m.status == discord.Status.idle])
        total_users = len(server.members)
        text_channels = len([x for x in server.channels
                             if x.type == discord.ChannelType.text])
        voice_channels = len(server.channels) - text_channels
        created_at = server.created_at.strftime('%d %b %Y %H:%M')

        data = discord.Embed(
            description='Server ID: ' + server.id,
            colour=discord.Colour(value='16727871'))
        data.add_field(name='Region', value=str(server.region))
        data.add_field(name='Users online',
                       value='{}/{}'.format(online, total_users))
        data.add_field(name='Total Text Channels', value=str(text_channels))
        data.add_field(name='Total Voice Channels', value=str(voice_channels))
        data.add_field(name='Roles', value=str(
            len([i.name for i in server.roles if i.name != '@everyone'])))
        data.add_field(name='Owner', value=str(server.owner))
        data.add_field(name='Created at', value=created_at)

        if server.icon_url:
            data.set_author(name=server.name, url=server.icon_url)
            data.set_thumbnail(url=server.icon_url)
        else:
            data.set_author(name=server.name)

        try:
            await self.bot.say(embed=data)
        except discord.HTTPException:
            await self.bot.say('I need to be able to send embedded links')

    @commands.command(pass_context=True)
    async def userinfo(self, ctx, member: discord.Member = None):

        if member is None:
            member = ctx.message.author

        name = member.name
        discriminator = member.discriminator
        game = member.game if member.game else None
        nick = member.nick
        id = member.id
        created_at = '{}'.format(member.created_at.strftime('%d %b %Y %H:%M'))
        joined_at = '{}'.format(member.joined_at.strftime('%d %b %Y %H:%M'))
        roles = ', '.join([i.name for i in member.roles if i.name != '@everyone']) if not len(member.roles) < 2 else None

        data = discord.Embed(
            description='User ID: ' + id,
            colour=discord.Color(value='16727871')
        )

        data.add_field(name='Discriminator', value=discriminator)
        data.add_field(name='Nickname', value=nick)
        data.add_field(name='Playing or streaming', value=game)
        data.add_field(name='Account created at', value=created_at)
        data.add_field(name='Joined this server at', value=joined_at)
        data.add_field(name='Roles', value=roles, inline=False)

        if member.avatar_url:
            data.set_author(name=name, url=member.avatar_url)
            data.set_thumbnail(url=member.avatar_url)
        else:
            data.set_author(name=name)

        try:
            await self.bot.say(embed=data)
        except discord.HTTPException:
            await self.bot.say('I need to be able to send embedded links')

    @commands.command()
    async def invite(self):
        data = discord.Embed(colour=discord.Color(value='16727871'))

        data.add_field(name='Invite me here', value='https://discordapp.com/oauth2/authorize?client_id=232916519594491906&scope=bot&permissions=536063039')
        data.add_field(name='My server', value='https://discord.gg/b9RCGvk')
        await self.bot.say(embed=data)

    @commands.command()
    @channel_check('nsfw')
    async def nudes(self):
        await self.bot.say(random.choice(NUDES))

    @commands.command(pass_context=True)
    @channel_check('nsfw')
    async def rule34(self, ctx, *, term):
        future = await self.bot.loop.run_in_executor(None, r34, term.replace(' ', '_'))
        await self.bot.say(future)


def setup(bot):
    bot.add_cog(Public(bot))
