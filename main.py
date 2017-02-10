import discord
import aiohttp
import asyncio
import xmlrpc.client
import traceback
import time
import langdetect
import json

from functools import partial
from discord.ext import commands
from utils import str_split
from cleverbot import Cleverbot
from utils import CheckError
from concurrent.futures import ThreadPoolExecutor

startup_extensions = ['commands.private', 'commands.mod_cmds',
                      'commands.public', 'commands.smod_cmds',
                      'commands.music.music', 'commands.logging',
                      'commands.repl', 'main_ext']
session = aiohttp.ClientSession()


async def update(bot):
    payload = json.dumps({
        'shard_id': bot.shard_id,
        'shard_count': bot.shard_count,
        'server_count': len(bot.servers)
    })
    payload2 = {
        'token': 'iAJ9cq7Lv4',
        'servers': bot.get_cfg()['servers']
    }
    headers = {
        'Authorization': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySUQiOiIyMTY4NDcxMzMxOTY2ODEyMTciLCJyYW5kIjo4NzMsImlhdCI6MTQ3ODQzMzY2N30.x-iXS4JEWPuGEp83VTau1jKCEcgY6jG_CswR9uoOceI',
        'content-type': 'application/json'
    }
    await session.post('https://bots.discord.pw/api/bots/{0}/stats'.format(
        bot.user.id), data=payload, headers=headers)
    await session.post('https://bots.discordlist.net/api.php', data=payload2)


class Bot(commands.Bot):
    def __init__(self):
        commands.Bot.__init__(self, #shard_id=int(sys.argv[1]), shard_count=int(sys.argv[2]),
                              command_prefix=self.get_prefix)
        self.proxy = xmlrpc.client.ServerProxy('http://localhost:8000/')
        self.instances = {}
        self.uptime = time.time()
        self.thread_pool = ThreadPoolExecutor(max_workers=4)

    @property
    def log(self):
        with open('log.json') as f:
            data = json.load(f)
            f.close()
            return data

    def get_prefix(self, bot, message):
        default = [',', 'hime ', 'Hime ', 'himebot ', 'Himebot ', commands.when_mentioned(bot, message)]
        if message.channel.is_private:
            return default
        if message.server.id in self.log['prefixes']:
            return [self.log['prefixes'][message.server.id]] + default[1:]
        return default

    async def on_ready(self):
        self.remove_command('help')
        await self.change_presence(game=discord.Game(name='.help | .invite'))
        print('Logged in as {}, {}'.format(self.user.name, self.user.id))
        for extension in startup_extensions:
            try:
                self.load_extension(extension)
            except ImportError as e:
                print('Failed to load extension {}: {}: {}'.format(
                    extension, e.__class__.__name__, e))
        for i in self.servers:
            try:
                if langdetect.detect(i.name) == 'ar':
                    self.leave_server(i)
            except:
                pass
        await update(self)
        self.loop.run_in_executor(None, session.close)
        while 1:
            self.push_cfg()
            await asyncio.sleep(30)

    async def on_message(self, message):
        msg = message.content.lower()
        ch = message.channel

        if message.author.bot:
            return
        try:
            if msg.split()[0][1:] in dir(self.cogs['SMod']) + dir(self.cogs['Private']):
                if msg.split()[0][0] == '.' and msg.split()[0][1:] not in ['e', 'px', 'x']:
                    try:
                        await self.delete_message(message)
                    except:
                        pass
        except:
            pass
        if msg.startswith('ayy') and len(msg) == 3:
            await self.send_message(ch, 'lmao')
        if msg.startswith('wew') and len(msg) == 3:
            await self.send_message(ch, 'lad')
        if '<@232916519594491906>' in msg:
            msg = msg.replace('<@232916519594491906>', 'hime')
        if 'hime' in msg:
            if message.author.id not in self.instances.keys():
                future = self.loop.run_in_executor(None, partial(Cleverbot, 'himebot'))
                self.instances[message.author.id] = await future

            question = msg.split(' ', 1)[1] if msg.startswith('hime') else msg
            future = self.loop.run_in_executor(
                None, self.instances[message.author.id].ask, question)
            answer = await future

            await self.send_message(message.channel, answer)

        await self.process_commands(message)

    async def on_command_error(self, error, ctx):
        channel = ctx.message.channel
        if isinstance(error, commands.MissingRequiredArgument):
            msg = await self.send_message(channel, 'missing arg(s) dumbfook')
            await asyncio.sleep(3)
            await self.delete_message(msg)
        if isinstance(error, commands.CheckFailure):
            msg = await self.send_message(channel, 'u ain\'t got perms fgt')
            await asyncio.sleep(3)
            await self.delete_message(msg)
        if isinstance(error, commands.BadArgument):
            msg = await self.send_message(channel, 'bad arguments, look at .help for halp')
            await asyncio.sleep(3)
            await self.delete_message(msg)
        if isinstance(error, commands.NoPrivateMessage):
            msg = await self.send_message(channel, 'that command is not '
                                                   'available in DMs.')
            await asyncio.sleep(3)
            await self.delete_message(msg)
        if isinstance(error, commands.CommandOnCooldown):
            msg = await self.send_message(channel, 'you cannot use that command right now')
            await asyncio.sleep(3)
            await self.delete_message(msg)
        if isinstance(error, CheckError):
            if error.id == 'musicError':
                msg = await self.send_message(channel, 'you must have a role named himebot_music in order to use that command')
                await asyncio.sleep(5)
                await self.delete_message(msg)
            elif error.id == 'nsfw':
                msg = await self.send_message(channel, 'you can only use this command in the nsfw channel')
                await asyncio.sleep(5)
                await self.delete_message(msg)

        channel = discord.utils.get(self.get_all_channels(), id='232190536231026688')
        if channel is not None:
            traceback_msg = ''''''.join(
                traceback.format_exception(error.__class__.__name__, error, error.__traceback__))
            output = str_split(traceback_msg)
            for out in output:
                await self.send_message(channel, out)
            await self.send_message(channel, 'Origin: {}'.format(ctx.message.server))

    def get_cfg(self):
        return self.proxy.get_cfg()

    def push_cfg(self):
        cfg = {
            'channels': len([i for i in self.get_all_channels()]),
            'servers': len(bot.servers),
            'members': len([i for i in self.get_all_members()]),
            'playing_on': len([self.cogs['Music'].voice_states[k].current for k in self.cogs[
                'Music'].voice_states if self.cogs['Music'].voice_states[k].current is not None])
        }
        self.proxy.add_to_cfg(cfg, self.shard_id)

    def start_bot(self):
        self.run('token')

    async def start_bot_async(self):
        await self.start('token')


bot = Bot()
bot.start_bot()
