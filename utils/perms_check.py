from discord.ext import commands
from utils.custom_exceptions import CheckError

IDS = '205346839082303488 119516995908534272'


def checks(_id=IDS):
    def _is(message, _id):
        if message.author.id in _id:
            return True
        else:
            print('RESTRICTED', message.author, message.content)
            return False

    return commands.check(lambda ctx: _is(ctx.message, _id))


def check(**perms):
    def predicate(ctx, perms):
        msg = ctx.message
        ch = msg.channel
        author = msg.author
        resolved = ch.permissions_for(author)

        return all(getattr(resolved, name, None) == value for name, value in perms.items())
    return commands.check(lambda ctx: predicate(ctx, perms))


def role_check(role='himebot_music'):
    def inner_role_check(ctx):
        role_inserver = role in [i.name for i in ctx.message.server.roles]
        if role_inserver:
            if role not in [i.name for i in ctx.message.author.roles]:
                raise CheckError('musicError')
        return True
    return commands.check(inner_role_check)


def channel_check(channel):
    def innner_channel_check(ctx):
        if channel in [i.name.lower() for i in ctx.message.server.channels]:
            if not ctx.message.channel.name.lower() == channel:
                raise CheckError(channel)
        return True
    return commands.check(innner_channel_check)