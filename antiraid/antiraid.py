from discord.ext import commands
from cogs.utils.dataIO import dataIO
from collections import defaultdict
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
        """Antiraid settings"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)


    @antiraid.command(pass_context=True, no_pm=True)
    async def slowmode(self, ctx):
        """Slowmode settings"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
            server = ctx.msg.server
            schannels = self.settings[server.id].get("slowmode_channels", [])
            schannels = [discord.utils.get(server.channels, id=sc) for sc in schannels]
            schannels = [sc.name for sc in schannels if sc is not None]
            if sc:
                await self.bot.say("The channels currently set on this server are:\n\n" + ",".join(sc))


    @slowmode.command(name='add' pass_context=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def _add_schannel(self, ctx, *channels: discord.Channel)
        """Adds channels to the servers slowmode list."""
        server=ctx.message.server
        schannels = [discord.utils.get(server.channels, id=sc) for sc in schannels]
        ctmp[works] : []
        ctmp[failed] : []
        if ctx.invoked_subcommand is None:
            await send.msg.server(ctx)
        else
            for channel in schannels:
                if has_permissions = channel.permissions_for(server.me).manage_messages
                self.settings[server.id][slowmodechannels].append.channel
                ctmp[works].append(channel)
            else
                ctmp[failed].append(channel)
        if ctmp[failed] is [] and ctmp[works] is not []:
            await self.bot.say("The following channels are now in slowmode:\n\n```diff{}"+"```".format"\n+ []".join(ctmp(works)))
        else if ctmp[failed] is not [] and ctmp[works] is not []:
            await self.bot.say("The following channels are now in slowmode:\n\n```diff{}```\n\n I do not have permissions to add the following channels, they have not in slowmode!\n\n```diff{}```".format("\n+ []".join(ctmp[works], "\n- []".join(ctmp[failed]))
        else
            await self.bot.say("I do not have the perms to add any of the the channels you gave me! These are not in slowmode!\n\n```diff{}```".format("\n- []".join(ctmp[works], "\n+ []".join(ctmp[failed]))


def check_folder():
    if not os.path.exists('data/antiraid'):
        print('Creating data/seen folder...')
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
    n = Antiraid(bot)
    bot.add_cog(n)
