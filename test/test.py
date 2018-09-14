from discord.ext import commands
from .utils import checks
import datetime
import discord
import os
from collections import defaultdict

class test:
    '''test'''

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @checks.is_owner()
    async def emtest(self, ctx):
        """Loads a cog

        Example: load mod"""

        if ctx.invoked_subcommand is None:
            return

        timestamp = datetime.datetime.today()

        embedmsg = discord.Embed(title="{} greeted {} to the server\n\n".format(ctx.author.name, ctx.author.name),
                                        colour=discord.Colour(0x54d824),
                                        # description="This server is currently on `{}` of setup".format(stage),
                                        timestamp = timestamp)

        await self.bot.say(embed=embedmsg)




def setup(bot: commands.Bot):
    n = test(bot)
    bot.add_cog(n)
