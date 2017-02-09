import discord
import copy
import aiohttp
from utils import subproc, AsyncEval, checks, str_split

from discord.ext import commands


class Private:

    def __init__(self, bot):
        self.bot = bot
        self.evalConsole = AsyncEval(self.bot.loop, {"bot": self.bot, "self": self})
        self.aiosession = aiohttp.ClientSession()

    @commands.command(pass_context=True)
    @checks()
    async def tagall(self, ctx):
        ctx = ctx.message
        msg = ''
        members = copy.copy(list(ctx.server.members))
        if len(''.join(str(members))) < 1900:
            for i in members:
                msg = msg + i.mention
            await self.bot.say(msg, delete_after=0.5)
        else:
            for i in members:
                if len(msg) > 1900:
                    await self.bot.say(msg, delete_after=0.5)
                    msg = ''
                    continue
                else:
                    msg = msg + i.mention

    @commands.command(pass_context=True)
    @checks()
    async def banall(self, ctx, server=None):
        if server is not None:
            for i in self.bot.servers:
                if server in str(i.name):
                    server = i
        else:
            server = ctx.message.server
        members = copy.copy(list(server.members))
        for i in members:
            try:
                await self.bot.ban(i)
            except:
                pass

    @commands.command(pass_context=True)
    @checks()
    async def msgall(self, ctx, *, msg: str):
        print(msg)
        members = copy.copy(list(ctx.message.server.members))
        for i in members:
            try:
                await self.bot.send_message(i, msg)
            except discord.errors.Forbidden:
                print('can\'t send msgs to ', i)
            else:
                print(i)

    @commands.command(pass_context=True)
    @checks()
    async def sendmsg(self, ctx, member: discord.Member, *, msg: str):
        await self.bot.send_message(member, msg)

    @commands.command(pass_context=True)
    @checks()
    async def spam(self, ctx, amount: int, server=None, *, message: str):
        _server = None
        server = ' '.join(server.lower().split('_'))
        count = 0
        for i in self.bot.servers:
            if i.name.lower() == server:
                _server = i
        while count != amount:
            await self.bot.send_message(_server, message)
            count += 1

    @commands.command(pass_context=True)
    @checks()
    async def x(self, ctx, *, command):
        result = await subproc(command)
        output = str_split(result)
        for i in output:
            await self.bot.say(i)

    @commands.command(pass_context=True)
    @checks()
    async def e(self, ctx, *, message):
        self.evalConsole.locals.update({"ctx": ctx,
                                        "msg": ctx.message,
                                        "ch": ctx.message.channel,
                                        "server": ctx.message.server,
                                        "author": ctx.message.author})
        result = await self.evalConsole.run(message)
        result = str(result)
        output = str_split(result, lang='python')
        for i in output:
            await self.bot.send_message(ctx.message.channel, i)

    @commands.command(pass_context=True)
    @checks()
    async def createinv(self, ctx, *, server: str):
        invite_server = discord.utils.get(self.bot.servers, id=server)
        if invite_server is None:
            invite_server = discord.utils.get(self.bot.servers, name=server)
        if invite_server is None:
            await self.bot.say('server not on the list', delete_after=1)
        else:
            try:
                invite = await self.bot.create_invite(invite_server)
            except discord.errors.Forbidden:
                await self.bot.say('bot got no perms in {}'.format(invite_server.name), delete_after=1)
            else:
                await self.bot.say(invite.url)

    @commands.command(pass_context=True)
    @checks()
    async def broadcast(self, ctx, *, msg):
        servers = copy.copy(list(self.bot.servers))
        for i in servers:
            try:
                await self.bot.send_message(i, msg)
            except:
                await self.bot.say("couldn't broadcast to %s" % i.name)

    @commands.command(pass_context=True)
    @checks()
    async def changegame(self, ctx, *, game):
        await self.bot.change_presence(game=discord.Game(name=game))

    @commands.command(pass_context=True)
    @checks()
    async def changepic(self, ctx, url):
        with aiohttp.Timeout(10):
            async with self.aiosession.get(url) as res:
                await self.bot.edit_profile(avatar=await res.read())

    @commands.command(pass_context=True)
    @checks()
    async def leave(self, ctx, *, server=None):
        if server is not None:
            for i in self.bot.servers:
                if server in str(i.name):
                    server = i
        else:
            server = ctx.message.server
        try:
            await self.bot.leave_server(server)
        except Exception as e:
            await self.bot.send_message(ctx.message.channel, "{}: {}".format(e.__class__.__name__, e))
        else:
            await self.bot.say("left "+server.name)


def setup(bot):
    bot.add_cog(Private(bot))
