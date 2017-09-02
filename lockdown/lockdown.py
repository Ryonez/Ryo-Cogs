from discord.ext import commands
from cogs.utils.dataIO import dataIO
from __main__ import send_cmd_help, settings
from .utils import checks
import datetime
import discord
import os
from collections import defaultdict


server_template = {
    "serverlockdown" : False,
    "channels" : {}
}
channel_template = {}
channeloverride_template = {
            "type": None,
            "overrides": {}
        }

class Lockdown:
    """Lockdown"""

    def __init__(self, bot):
        self.bot = bot
        setpath = os.path.join('data', 'lockdown', 'locks.json')
        locks = dataIO.load_json(setpath)
        self.locks = defaultdict(lambda: server_template.copy(), locks)

    @commands.group(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def lockdown(self, ctx):
        """lockdown."""
        if ctx.invoked_subcommand is None:
            await ctx.invoke(self._lockdownchannel_, channel=ctx.message.channel)


    @lockdown.command(name="channel", pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def _lockdownchannel_(self, ctx, channel: discord.Channel):
        """Locks the channel so only users with the Administrator perm can talk."""
        if channel is None:
            channel = ctx.message.channel
        server = ctx.message.server

        if self.locks[server.id]["channels"].get(channel.id) is None:
            status = await self.bot.say("Lockdown initiating, one moment!")
            await self._savechanneloverrides_(channel)
            await self._lockchannel_(channel)
            lockedmsg = discord.Embed(colour=discord.Colour(0xFF0000),
                                       timestamp=datetime.datetime.today(),
                                       description="`{}` has been locked!\n\nOnly Administrators can speak.".format(channel.name))
            lockedmsg.set_author(name="Channel Lockdown")
            lockedmsg.set_thumbnail(url="https://i.imgur.com/zNU3Y9m.png")
            await self.bot.delete_message(status)
            if channel != ctx.message.channel and channel.type.name != "voice":
                await self.bot.send_message(destination = channel, embed = lockedmsg)
            await self.bot.say(embed = lockedmsg)
        else:
            status = await self.bot.say("Lockdown lifting, one moment!")
            await self._unlockchannel_(channel)
            unlockedmsg = discord.Embed(colour=discord.Colour(0x2bdb25),
                                      timestamp=datetime.datetime.today(),
                                      description="`{}` has been unlocked!\n\nNormal perms have been restored.".format(channel.name))
            unlockedmsg.set_author(name="Channel Lockdown Lifted")
            unlockedmsg.set_thumbnail(url="https://i.imgur.com/Kw0C9gK.png")
            await self.bot.delete_message(status)
            if channel != ctx.message.channel and channel.type.name != "voice":
                await self.bot.send_message(destination = channel, embed = unlockedmsg)
            await self.bot.say(embed = unlockedmsg)

    @lockdown.command(name="server", pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def _lockdownserver_(self, ctx):
        """Locks the entire server so only users with the Administrator perm can talk."""
        server = ctx.message.server

        if self.locks[server.id].get("serverlockdown") is False:
            status = await self.bot.say("**Server Lockdown** initiating, one moment!")
            for c in server.channels:
                if self.locks[server.id]["channels"].get(c.id) is None:
                    await self._savechanneloverrides_(c)
                    await self._lockchannel_(c)
            self.locks[server.id]["serverlockdown"] = True
            self.save()
            lockedmsg = discord.Embed(colour=discord.Colour(0xFF0000),
                                      timestamp=datetime.datetime.today(),
                                      description="`{}` has been locked!\n\nOnly Administrators can speak on this server.".format(
                                          ctx.message.server.name))
            lockedmsg.set_author(name="SERVER LOCKDOWN")
            lockedmsg.set_thumbnail(url="https://i.imgur.com/zNU3Y9m.png")
            await self.bot.delete_message(status)
            await self.bot.say(embed=lockedmsg)
        else:
            status = await self.bot.say("**Server Lockdown** lifting, one moment!")
            for c in server.channels:
                await self._unlockchannel_(c)
            self.save
            unlockedmsg = discord.Embed(colour=discord.Colour(0x2bdb25),
                                        timestamp=datetime.datetime.today(),
                                        description="`{}` has been unlocked!\n\nNormal perms have been restored to all channels.".format(ctx.message.server.name))
            unlockedmsg.set_author(name="Server Lockdown Lifted")
            unlockedmsg.set_thumbnail(url="https://i.imgur.com/Kw0C9gK.png")
            await self.bot.delete_message(status)
            await self.bot.say(embed=unlockedmsg)

    async def _savechanneloverrides_(self, channel):
        #Saves the current channel overrides.
        server = channel.server
        savedserver = defaultdict(lambda: server_template.copy(),
                                        self.locks[server.id])
        savedchannels = defaultdict(lambda: channel_template.copy(),
                                        savedserver["channels"])
        savedchannel = defaultdict(lambda: channel_template.copy(), savedchannels[channel.id])
        try:
            for o in channel.overwrites:
                current_overrides = defaultdict(lambda: channeloverride_template.copy(),
                                                savedchannel[o[0].id])
                if isinstance(o[0], discord.Role):
                    current_overrides["type"] = 'Role'
                elif isinstance(o[0], discord.Member):
                    current_overrides["type"] = 'Member'
                current_overrides["overrides"] = o[1]._values
                savedchannels[channel.id][o[0].id] = current_overrides
        except discord.Forbidden:
            return "forbidden"

        savedserver["channels"] = savedchannels
        self.locks[server.id] = savedserver
        self.save()
        return None

    async def _lockchannel_(self, channel):

        for o in channel.overwrites:
            overwrite = channel.overwrites_for(o[0])
            if channel.type.name == 'text':
                overwrite.send_messages = False
            if channel.type.name == 'voice':
                overwrite.speak = False
            try:
                await self.bot.edit_channel_permissions(channel, o[0], overwrite)
            except discord.Forbidden:
                return False
        return True

    async def _unlockchannel_(self, channel):
        server = channel.server
        for o in channel.overwrites:
            soverride = self.locks[server.id]["channels"][channel.id][o[0].id].get("overrides")
            overwrite = channel.overwrites_for(o[0])
            if soverride is not None:
                if channel.type.name == 'text':
                    setattr(overwrite, "send_messages", soverride.get("send_messages"))
                if channel.type.name == 'voice':
                    setattr(overwrite, "speak", soverride.get("speak"))
                try:
                    await self.bot.edit_channel_permissions(channel, o[0], overwrite)
                except discord.Forbidden:
                    return False
        del self.locks[server.id]["channels"][channel.id]
        if len(self.locks[server.id]["channels"]) == 0:
            del self.locks[server.id]
        self.save()
        return True

    def save(self):
        setpath = os.path.join('data', 'lockdown', 'locks.json')
        dataIO.save_json(setpath, self.locks)

def check_folder():
    path = os.path.join('data', 'lockdown')
    if not os.path.exists(path):
        print('Creating ' + path + '...')
        os.makedirs(path)

def check_files():

    files = {
        "locks.json": {}
    }
    datapath = os.path.join('data', 'lockdown')
    for filename, value in files.items():
        path = os.path.join(datapath, filename)
        if not os.path.isfile(path):
            print("Path: {}".format(path))
            print("Creating empty {}".format(filename))
            dataIO.save_json(path, value)


def setup(bot):
    check_folder()
    check_files()
    n = Lockdown(bot)
    bot.add_cog(n)