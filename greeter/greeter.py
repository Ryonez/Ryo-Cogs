from discord.ext import commands
from cogs.utils.dataIO import dataIO
from __main__ import send_cmd_help, settings
from .utils import checks
import datetime
import discord
import os
from collections import defaultdict

server_template = {
    "greeterroleid" : None,
    "memberroleid" : None,
    "greetlogchid" : None,
    "greetmsg" : None,
    "enabled" : False
}

class Greet:

    def __init__(self, bot):
        self.bot = bot
        setpath = os.path.join('data', 'greet', 'settings.json')
        settings = dataIO.load_json(setpath)
        self.settings = defaultdict(lambda: server_template.copy(), settings)

    @commands.group(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def greet(self, ctx, user: discord.User):
        """The greeter command, passed a role to greet someone into the server."""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
            return

        if self.settings[server.id].get("enabled"):

            #Setup vars
            server = ctx.message.server
            mrole = discord.utils.get(server.roles, id=self.settings[server.id].get("mrolesid"))

            if ctx.message.author is self._isgreeter_(server, ctx.author):
                timestamp = datetime.datetime.today()
                try:
                    await self.bot.add_roles(user, mrole)
                    await self._log_("Success", timestamp, server, ctx.author, user)
                except discord.Forbidden:
                    await self._log_("Forbidden", timestamp, server)
                    return



    def _isgreeter_(self, server, user):
        # Check if the given user has the greeter role.
        groleid = self.settings[server.id].get("greeterrole")

        if groleid is None:
            return False
        else:
            for r in user.roles:
                if r.id == groleid:
                    return True
            return False

    def _log_(self, status, timstamp, server, greetuser = None, newuser = None):
        # Loggint for the greeter cog.
        logch = discord.utils.get(server.channels, id=self.settings[server.id].get("greetlogchid"))



        if status != "Success":
            embedmsg = discord.Embed(title="{} greeted {} to the server\n\n",
                                         colour=discord.Colour(0x54d824),
                                         # description="This server is currently on `{}` of setup".format(stage),
                                         timestamp)

    def save(self):
        setpath = os.path.join('data', 'greet', 'settings.json')
        dataIO.save_json(setpath, self.settings)


def check_folder():
    path = os.path.join('data', 'greet')
    if not os.path.exists(path):
        print('Creating ' + path + '...')
        os.makedirs(path)

def check_files():

    files = {
        "settings.json": {}
    }
    datapath = os.path.join('data', 'greet')
    for filename, value in files.items():
        path = os.path.join(datapath, filename)
        if not os.path.isfile(path):
            print("Path: {}".format(path))
            print("Creating empty {}".format(filename))
            dataIO.save_json(path, value)


def setup(bot):
    check_folder()
    check_files()
    n = Greeter(bot)
    bot.add_cog(n)