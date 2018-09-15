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

    @commands.command(pass_context=True)
    @checks.is_owner()
    async def emtest(self, ctx):
        """Test code"""

        timestamp = datetime.datetime.today()
        auth = ctx.message.author

        embedmsg = discord.Embed(title="{} greeted {} to the server\n\n".format(ctx.message.author.mention, ctx.message.author.name),
                                        colour=discord.Colour(0x54d824),
                                        # description="This server is currently on `{}` of setup".format(stage),
                                        timestamp = timestamp)
        embedmsg.set_footer(text = "{}'s (Greeter) ID: `{}` | {}'s (New member) ID `{}`".format(auth.name, auth.id, auth.mention, auth.id))

        await self.bot.say(embed=embedmsg)

    @commands.command(pass_context=True)
    @checks.admin_or_permissions(administrator=True)
    async def emtest1(self, ctx):
        """Test code"""

        timestamp = datetime.datetime.today()
        auth = ctx.message.author

        embedmsg = discord.Embed(#title="{} greeted {}\n\n".format(greetuser.mention, newuser.mention),
                                        colour=discord.Colour.green(),
                                        description="{} was given the {} role".format(ctx.message.author.name, ctx.message.author.top_role),
                                        timestamp = timestamp)
        embedmsg.set_author(name="{} greeted {} to the server\n\n".format(ctx.message.author.mention, ctx.message.author.name,
                            icon_url=auth.avatar_url))
        embedmsg.set_footer(text = "Greeter {}'s ID: `{}` | New member {}'s ID `{}`".format(auth.name, auth.id, auth.name, auth.id))

        await self.bot.say(embed=embedmsg)

    @commands.command(pass_context=True)
    @checks.is_owner()
    async def emtest2(self, ctx):
        """Test code"""

        timestamp = datetime.datetime.today()

        embedmsg = discord.Embed(title="{} greeted {} to the server\n\n".format(ctx.message.author.mention, ctx.message.author.name),
                                        colour=discord.Colour(0x54d824),
                                        # description="This server is currently on `{}` of setup".format(stage),
                                        timestamp = timestamp)

        await self.bot.say(embed=embedmsg)

    def embed_set_author_name(embed: discord.Embed, channel_name: str, member_name: str, system_name: str, avatar_url: str):
    name = "#{}: {}".format(channel_name, member_name)
    if system_name:
        name += " ({})".format(system_name)

    embed.set_author(name=name, icon_url=avatar_url or discord.Embed.Empty)



def setup(bot: commands.Bot):
    n = test(bot)
    bot.add_cog(n)
