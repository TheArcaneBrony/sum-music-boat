import datetime
import time
import discord

from discord.ext import commands
from utils import checks, subproc


class MainExt:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @checks()
    async def load(self, extension_name: str):
        """Loads an extension."""
        try:
            self.bot.load_extension(extension_name)
        except (AttributeError, ImportError) as e:
            await self.bot.say("```py\n{}: {}\n```".format(e.__class__.__name__, e))
            return
        await self.bot.say(extension_name + " loaded")

    @commands.command()
    @checks()
    async def unload(self, extension_name: str):
        """Unloads an extension."""
        self.bot.unload_extension(extension_name)
        await self.bot.say(extension_name + " unloaded")

    @commands.command()
    @checks()
    async def reload(self, extension_name: str):
        self.bot.unload_extension(extension_name)
        try:
            self.bot.load_extension(extension_name)
        except (AttributeError, ImportError) as e:
            await self.bot.say("```py\n{}: {}\n```".format(e.__class__.__name__, e))
            return
        await self.bot.say(extension_name + " reloaded")

    @commands.command()
    async def botinfo(self):
        time_online = str(datetime.timedelta(seconds=int(time.time() - self.bot.uptime)))
        servers = self.bot.get_cfg()["servers"]
        channels = self.bot.get_cfg()["channels"]
        members = self.bot.get_cfg()["members"]
        playing_on = self.bot.get_cfg()["playing_on"]
        load = await subproc("cat /proc/loadavg")

        data = discord.Embed(
            description="A multifunctional discord bot made by init0#8366",
            colour=discord.Color(value="16727871"))

        data.add_field(name="Servers that i am in", value=str(servers))
        data.add_field(name="Uptime", value=time_online)
        data.add_field(name="Channels that i am in", value=channels)
        data.add_field(name="Total users encountered", value=members)
        data.add_field(name="Servers playing music on", value=str(playing_on))
        data.add_field(name="Load (ignore pls, not important)", value=load[:14])
        data.add_field(name="Shard", value=self.bot.shard_id)
        data.add_field(name="Shard count", value=self.bot.shard_count)

        data.set_author(name="himebot", url="https://himebot.xyz")
        data.set_thumbnail(url=self.bot.user.avatar_url)

        try:
            await self.bot.say(embed=data)
        except discord.HTTPException:
            await self.bot.say("I need to be able to send embedded links")


def setup(bot):
    bot.add_cog(MainExt(bot))
