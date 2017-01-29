from discord.ext import commands
from utils.custom_exceptions import RoleCheckError


def checks(_id='205346839082303488 119516995908534272'):
    def _is(message, _id):
        if message.author.id in _id:
            return True
        else:
            print('RESTRICTED', message.author, message.content)
            return False

    return commands.check(lambda ctx: _is(ctx.message, _id))


def predicate(ctx, perms):
    msg = ctx.message
    ch = msg.channel
    author = msg.author
    resolved = ch.permissions_for(author)

    return all(getattr(resolved, name, None) == value for name, value in perms.items())


def check(**perms):
    return commands.check(lambda ctx: predicate(ctx, perms))


def role_check(role='himebot_music'):
    def inner_role_check(ctx):
        role_inserver = role in [i.name for i in ctx.message.server.roles]
        if role_inserver:
            if role not in [i.name for i in ctx.message.author.roles]:
                raise RoleCheckError('musicError')
        return True
    return commands.check(inner_role_check)
