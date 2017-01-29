import discord
import json

from discord.ext import commands
from utils import check


class Logging:
    def __init__(self, bot):
        self.bot = bot
        self.json = bot.log
        self.log_config = {}
        self.update()

    def update(self):
        for i in self.json['servers']:
            self.log_config[i] = discord.utils.get(self.bot.get_all_channels(), server__id=i, name='logs')

    @commands.command(pass_context=True)
    @check(manage_server=True)
    async def logging(self, ctx):

        channel = discord.utils.get(ctx.message.server.channels, name='logs', type=discord.ChannelType.text)

        if channel is None:
            await self.bot.say('no text channel named logs')
            return

        if ctx.message.server.id not in self.json['servers']:
            self.json['servers'].append(ctx.message.server.id)
            await self.bot.say('logging is now enabled on this server')
        else:
            self.json['servers'].remove(ctx.message.server.id)
            await self.bot.say('logging is now disabled on this server')

        with open('log.json', 'w') as file:
            json.dump(self.json, file, indent=4)

        self.update()

    async def on_message_delete(self, message):
        if message.server.id in self.log_config.keys():
            logs = self.log_config[message.server.id]
            to_send = ':x: **Message deleted**: {0.author}: {0.content}'.format(message)
            await self.bot.send_message(logs, to_send)

    async def on_message_edit(self, before, after):
        if after.server.id in self.log_config.keys():
            logs = self.log_config[after.server.id]
            if before.content != after.content:
                to_send = ':speech_left: **Message edited**: {0.author}: ~~{0.content}~~ | {1.content}'.format(before, after)
                await self.bot.send_message(logs, to_send)

    async def on_member_join(self, member):
        if member.server.id in self.log_config.keys():
            logs = self.log_config[member.server.id]
            to_send = ':bust_in_silhouette::arrow_right: **User joined**: {0}'.format(member)
            await self.bot.send_message(logs, to_send)

    async def on_member_remove(self, member):
        if member.server.id in self.log_config.keys():
            logs = self.log_config[member.server.id]
            to_send = ':bust_in_silhouette::arrow_left: **User left**: {0}'.format(member)
            await self.bot.send_message(logs, to_send)

    async def on_member_ban(self, member):
        if member.server.id in self.log_config.keys():
            logs = self.log_config[member.server.id]
            to_send = ':bust_in_silhouette::x: **User banned**: {0}'.format(member)
            await self.bot.send_message(logs, to_send)

    async def on_member_unban(self, server, user):
        if server.id in self.log_config.keys():
            logs = self.log_config[server.id]
            to_send = ':bust_in_silhouette::white_check_mark: **User unbanned**: {0}'.format(user)
            await self.bot.send_message(logs, to_send)


def setup(bot):
    bot.add_cog(Logging(bot))
