import json
import aiohttp


class BotList(object):
    """Updates bots.discord.pw infomation"""

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.bot.loop.create_task(self.update())
        self.payload = json.dumps({
            "shard_id": self.bot.shard_id,
            "shard_count": self.bot.shard_count,
            "server_count": len(self.bot.servers)
        })
        self.payload2 = {
            "token": "iAJ9cq7Lv4",
            "servers": self.bot.get_cfg()["servers"]
            }
        self.headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySUQiOiIyMTY4NDcxMzMxOTY2ODEyMTciLCJyYW5kIjo4NzMsImlhdCI6MTQ3ODQzMzY2N30.x-iXS4JEWPuGEp83VTau1jKCEcgY6jG_CswR9uoOceI",
            "content-type": "application/json"
        }

    def __unload(self):
        self.bot.loop.create_task(self.session.close())

    async def update(self):
        await self.session.post("https://bots.discord.pw/api/bots/{0}/stats".format(
            self.bot.user.id), data=self.payload, headers=self.headers)
        await self.session.post("https://bots.discordlist.net/api.php", data=self.payload2)

    async def on_server_join(self, server):
        await self.update()

    async def on_server_leave(self, server):
        await self.update()


def setup(bot):
    bot.add_cog(BotList(bot))
