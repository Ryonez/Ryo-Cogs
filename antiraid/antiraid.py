from discord.ext import commands
from cogs.utils.dataIO import dataIO
from collections import deque, defaultdict
from __main__ import send_cmd_help, settings
from .utils import checks
from datetime import datetime as dt, timedelta
import discord
import os
import copy

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
        self.sm_cache = {}

    @commands.group(pass_context=True, no_pm=True)
    @checks.serverowner_or_permissions(administrator=True)
    async def antiraid(self, ctx):
        """Antiraid settings."""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)


    @antiraid.group(pass_context=True, no_pm=True)
    async def slowmode(self, ctx):
        """Slowmode settings.\nChannels that have slowmode enabled will delete a users messages if they posted less than 5 seconds from their last one. This inculdes messages deleted via slowmode. \nNote, any user who has the "manage_messages" for the channel set to true is exempt from being slowed."""
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
                await self.bot.say("\n:eight_spoked_asterisk: The following channel(s) are in slowmode:\n\n```diff\n+ " + "\n+ ".join(schannels) + "```")
            else:
                await self.bot.say("There are currently no channels in slowmode.")


    @slowmode.command(name="enable", pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def _slowmode_enable(self, ctx, *channel: discord.Channel):
        """Adds channels to the servers slowmode list."""
        server = ctx.message.server
        serverchannels = [x.id for x in server.channels]
        channels = [r for r in channel if str(r.id) in serverchannels]
        schannels = self.settings[server.id].get("slowmode_channels", [])
        schannels = [discord.utils.get(server.channels, id=sc) for sc in schannels]
        schannels = [sc.id for sc in schannels if sc is not None]

        ctmp = {
        "worked" : [],
        "present" : [],
        "noperm" : []
        }

        msg = "\n**Slowmode notices:**\n"

        #for schannels in serverchannels:
        #    ctmp["listed"].append(schannels)

        for channel in channels:
            if channel.id in schannels:
                ctmp["present"].append(channel.name)
            elif channel.permissions_for(server.me).manage_messages == True:
                self.settings[server.id]["slowmode_channels"].append(channel.id)
                ctmp["worked"].append(channel.name)
            else:
                ctmp["noperm"].append(channel.name)
        self.save()

        if ctmp["worked"]:
            msg += "\n:white_check_mark: The following channel(s) are now in slowmode:\n\n```diff\n+ " + "\n+ ".join(ctmp["worked"]) + "```"
        if ctmp["present"]:
            msg += "\n:eight_spoked_asterisk: The following channel(s) are already in slowmode:\n\n```diff\n+ " + "\n+ ".join(ctmp["present"]) + "```"
        if ctmp["noperm"]:
            msg += "\n:anger:I do not have the perms to add the following channel(s) you gave me! These are not in slowmode!:anger:\n\n```diff\n- " + "\n- ".join(ctmp["noperm"]) + "```"

        await self.bot.say(msg)

    @slowmode.command(name="disable", pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def _slowmode_disable(self, ctx, *channel: discord.Channel):
        """Removes channels from the servers slowmode list."""
        server = ctx.message.server
        serverchannels = [x.id for x in server.channels]
        channels = [r for r in channel if str(r.id) in serverchannels]
        schannels = self.settings[server.id].get("slowmode_channels", [])

        ctmp = {
        "worked" : [],
        "cleanupf" : [],
        "nodata" : []
        }

        msg = "\n**Slowmode notices:**\n"

        #for schannels in serverchannels:
        #    ctmp["listed"].append(schannels)

        for channel in channels:
            try:
                self.settings[server.id]["slowmode_channels"].remove(channel.id)
                ctmp["worked"].append(channel.name)
            except ValueError:
                ctmp["nodata"].append(channel.name)

        #Check for and clean channals that no longer exist
        for c in schannels:
            if c not in serverchannels:
                try:
                    self.settings[server.id]["slowmode_channels"].remove(c)
                except ValueError:
                    ctmp["cleanupf"].append(c)

        self.save()

        if ctmp["worked"]:
            msg += "\n:white_check_mark: The following channel(s) are no longer in slowmode:\n\n```diff\n+ " + "\n+ ".join(ctmp["worked"]) + "```"
        if ctmp["nodata"]:
            msg += "\n:eight_spoked_asterisk: The following channel(s) weren't in slowmode, no changes needed:\n\n```diff\n+ " + "\n+ ".join(ctmp["nodata"]) + "```"
        if ctmp["cleanupf"]:
            msg += "\n:exclamation: There was and issue cleaning while preforming a self cleanup! This won't affect the anti raid system, but please contact my owner with the follow data so he can take care of it, thank you!\n\n```diff\n- " + "\n- ".join(ctmp["cleanupf"]) + "```"

        await self.bot.say(msg)

    async def check_slowmode(self, message):
        server = message.server
        channel = message.channel
        author = message.author
        ts = message.timestamp
        if server.id not in self.settings:
            return False
        if channel.id in self.settings[server.id]["slowmode_channels"]:
            if channel.id not in self.sm_cache:
                self.sm_cache[channel.id] = {}
                self.sm_cache[channel.id]["npermsc"] = 0
            if channel.permissions_for(author).manage_messages == True:
                return False
            if channel.permissions_for(server.me).manage_messages == False:
                if self.sm_cache[channel.id]["npermsc"] == 0:
                    await self.bot.send_message(channel, "\n**Slowmode notices:**\n:anger: I no longer have the perms to keep this channel in slowmode! Please restore the manage_messages perm to me, or remove this channel from slowmode!:anger:")
                    self.sm_cache[channel.id]["npermsc"] += 1
                    return False
                elif self.sm_cache[channel.id]["npermsc"] == 10:
                    self.sm_cache[channel.id]["npermsc"] = 0
                    return False
                else:
                    self.sm_cache[channel.id]["npermsc"] += 1
                    return False
            if author.id not in self.sm_cache[channel.id]:
                self.sm_cache[channel.id][author.id] = {}
                data = {}
                data["LastMsgTime"] = ts
                data["Counter"] = 0
                self.sm_cache[channel.id][author.id] = data
                return False

            data = self.sm_cache[channel.id][author.id]
            LastMsgTime = data["LastMsgTime"]
            if (ts - data["LastMsgTime"]) < timedelta(seconds = 5):
                try:
                    await self.bot.delete_message(message)
                    data["Counter"] += 1
                    if data["Counter"] == 3:
                        msg = "\n:no_entry:**Slowmode notices**:no_entry: \n ```diff\n Hold your horses!\n- This channel is in slowmode! Please wait 5 seconds between sending messages.\n Thank you!```\n{}".format(author.mention)
                        await self.bot.send_message(channel, msg)
                    data["LastMsgTime"] = ts
                    self.sm_cache[channel.id][author.id] = data
                    return True
                except:
                    pass
            else:
                data["LastMsgTime"] = ts
                data["Counter"] = 0
                self.sm_cache[channel.id][author.id] = data
        return False

    async def on_message(self, message):
        if message.channel.is_private or self.bot.user == message.author \
         or not isinstance(message.author, discord.Member):
            return
#        elif self.is_mod_or_superior(message):
#            return
        await self.check_slowmode(message)


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
