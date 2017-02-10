import discord
from discord.ext import commands
from utils import checks


class SMod(object):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    @checks()
    async def spurge(self, ctx):
        params = ctx.message.content.split()
        member = None
        amount = 100

        for i in params:
            try:
                if isinstance(int(i), int):
                    amount = i
            except:
                pass

        if len(ctx.message.mentions) > 0:
            member = ctx.message.mentions[0]

        try:
            await self.bot.purge_from(ctx.message.channel, limit=int(amount), before=ctx.message, check=lambda e: member is None or e.author == member)
        except ValueError:
            await self.bot.say('wtf that\'s not an int', delete_after=1)
        except TypeError:
            await self.bot.say('did you tag the fgt u wanna purge from?', delete_after=1)
        except discord.errors.Forbidden:
            print('ran this')
            await self.bot.say('bot got no perms', delete_after=1)

    @commands.command()
    @checks()
    async def sclear(self):
        try:
            await self.bot.say('\0\n' * 1000)
        except:
            pass

    @commands.command(pass_context=True)
    @checks()
    async def sban(self, ctx, *, member: discord.Member=None):

        try:
            await self.bot.ban(member)
        except discord.Forbidden:
            await self.bot.say('bot ain\'t got perms yo', delete_after=1)
        except discord.HTTPException:
            await self.bot.say('fgt didn\'t get banned', delete_after=1)
        except AttributeError:
            await self.bot.say('which fgt to ban??', delete_after=1)
        else:
            await self.bot.say('banned this fgt', delete_after=1)

    @commands.command(pass_context=True)
    @checks()
    async def skick(self, ctx, *, member: discord.Member=None):

        try:
            await self.bot.kick(member)
        except discord.Forbidden:
            await self.bot.say('bot ain\'t got perms yo', delete_after=1)
        except discord.HTTPException:
            await self.bot.say('fgt didn\'t get kicked', delete_after=1)
        except AttributeError:
            await self.bot.say('which fgt to kick??', delete_after=1)
        else:
            await self.bot.say('kicked this fgt', delete_after=1)


def setup(bot):
    bot.add_cog(SMod(bot))
