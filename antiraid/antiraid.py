from discord.ext import commands
from cogs.utils.dataIO import dataIO
from collections import defaultdict
from __main__ import send_cmd_help, settings
from .utils import checks
import discord
import os

default_settings = {
    "anti-log" : None,
    "slowmode_channels" : []
}

class Antiraid:
    '''Antiraid toolkit.'''

    def __init__(self, bot):
        self.bot = bot
        settings = dataIO.load_json("data/antiraid/settings.json")
        self.settings = defaultdict(lambda: default_settings.copy(), settings)

    @commands.group(pass_context=True, no_pm=True)
    @checks.serverowner_or_permissions(administrator=True)
    async def antiraid(self, ctx):
        """Antiraid settings."""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)


    @antiraid.group(pass_context=True, no_pm=True)
    async def slowmode(self, ctx):
        """Slowmode settings."""
        if ctx.invoked_subcommand is None or \
                isinstance(ctx.invoked_subcommand, commands.Group):
            await send_cmd_help(ctx)
            return

    @slowmode.command(name="list", pass_context=True, no_pm=True)
    async def _slowmode_list(self, ctx):
        """List the channels currently in slowmode."""
        if ctx.invoked_subcommand is None:
            server = ctx.message.server
            schannels = self.settings[server.id].get("slowmode_channels", [])
            schannels = [discord.utils.get(server.channels, id=sc) for sc in schannels]
            schannels = [sc.name for sc in schannels if sc is not None]
            if schannels:
                await self.bot.say("The channels currently set on this server are:\n\n" + ",".join(schannels))
            else:
                await self.bot.say("There are currently no channels in slowmode.")


    @slowmode.command(name="add", pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def _slowmode_add(self, ctx, *channel: discord.Channel):
        """Adds channels to the servers slowmode list."""
        server = ctx.message.server
        serverchannels = [x.id for x in server.channels]
        channels = [r for r in channel if str(r.id) in serverchannels]
        schannels = self.settings[server.id].get("slowmode_channels", [])
        schannels = [discord.utils.get(server.channels, id=sc) for sc in schannels]
        schannels = [sc.id for sc in schannels if sc is not None]

        ctmp = {
        "worked" : [],
        "listed" :[],
        "listed_names" : [],
        "noperm" : []
        }

        msg = "\n**Slowmode notices:**\n"

        #for schannels in serverchannels:
        #    ctmp["listed"].append(schannels)

        for channel in channels:
            if channel.id in schannels:
                ctmp["listed_names"].append(channel.name)
            elif channel.permissions_for(server.me).manage_messages == True:
                self.settings[server.id]["slowmode_channels"].append(channel.id)
                ctmp["worked"].append(channel.name)
            else:
                ctmp["noperm"].append(channel.name)
        self.save()

        if ctmp["worked"]:
            msg += "\n:white_check_mark: The following channel(s) are now in slowmode:\n\n```diff\n+ " + "\n+ ".join(ctmp["worked"]) + "```"
        if ctmp["listed_names"]:
            msg += "\n:eight_spoked_asterisk: The following channel(s) are already in slowmode:\n\n```diff\n+ " + "\n+ ".join(ctmp["listed_names"]) + "```"
        if ctmp["noperm"]:
            msg += "\n:anger:I do not have the perms to add the following channel(s) you gave me! These are not in slowmode!:anger:\n\n```diff\n- " + "\n- ".join(ctmp["noperm"]) + "```"

        await self.bot.say(msg)

    def save(self):
        dataIO.save_json("data/antiraid/settings.json", self.settings)

def check_folder():
    if not os.path.exists('data/antiraid'):
        print('Creating data/antiraid folder...')
        os.makedirs('data/antiraid')

def check_files():
    ignore_list = {"SERVERS": [], "CHANNELS": []}

    files = {
        "settings.json"       : {}
    }

    for filename, value in files.items():
        if not os.path.isfile("data/antiraid/{}".format(filename)):
            print("Creating empty {}".format(filename))
            dataIO.save_json("data/antiraid/{}".format(filename), value)

def setup(bot):
    check_folder()
    check_files()
    n = Antiraid(bot)
    bot.add_cog(n)
