from discord.ext import commands


class CheckError(commands.CommandError):
    def __init__(self, id):
        self.id = id

    def __str__(self):
        return self.id
