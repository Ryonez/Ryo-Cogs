from discord.ext import commands
from cogs.utils.dataIO import dataIO
from __main__ import send_cmd_help, settings
from .utils import checks
import datetime
import discord
import os
import logging
from collections import defaultdict
import asyncio

server_template = {
    "greeterroleid" : None,
    "memberroleid" : None,
    "greetlogchid" : None,
    "greetchannelid" : None,
    "removetriggercmd" : False,
    "enabled" : False
}

class Greeter:

    def __init__(self, bot):
        self.bot = bot
        setpath = os.path.join('data', 'greeter', 'settings.json')
        settings = dataIO.load_json(setpath)
        self.settings = defaultdict(lambda: server_template.copy(), settings)

    @commands.command(pass_context=True, no_pm=True)
    async def greet(self, ctx, user: discord.User, user2: discord.User = None):
        """The greeter command, pass a user to greet someone into the server. If you pass a second user, the log shows them as being related accounts.\ni.e `[p]greet @user1 @user2\nYou must has either the greeter role, or manage_roles perm to use this.`"""

        server = ctx.message.server
        author = ctx.message.author

        if self.settings[server.id].get("enabled"):
            
            grole = discord.utils.get(server.roles, id=self.settings[server.id].get("greeterroleid"))
            mrole = discord.utils.get(server.roles, id=self.settings[server.id].get("memberroleid"))
            greetch = discord.utils.get(server.channels, id=self.settings[server.id].get("greetchannelid"))
            clrcmd = self.settings[server.id].get("removetriggercmd")

            if greetch is not None and ctx.message.channel is not greetch:
                return

            if self._hasrole_(author, grole) or ctx.message.channel.permissions_for(author).manage_roles:
                timestamp = ctx.message.timestamp
                
                if self._hasrole_(user, mrole):
                    wtfemoji = discord.utils.get(self.bot.get_all_emojis(), id="330424102915407872").url
                    embed = discord.Embed()
                    embed.colour = discord.Colour(0x0F71B5)
                    embed.description = "What you playing at {}?".format(author.mention)
                    name = "{} is already a member!".format(user.name)
                    embed.set_thumbnail(url = wtfemoji)
                    embed.set_author(name=name)
                    embed.set_footer(text = "This message will self delete in 30 seconds")
                    msg = await self.bot.say(embed = embed)
                    await asyncio.sleep(30)
                    await self.bot.delete_message(msg)
                else:
                    try:
                        if user2 is None:
                            await self.bot.add_roles(user, mrole)
                            await self._greetlogger_("Success", timestamp, server, author, user, None, mrole)
                        else:
                            await self.bot.add_roles(user, mrole)
                            await self._greetlogger_("Success - Linked", timestamp, server, author, user, user2, mrole)
                    except discord.Forbidden:
                        await self._greetlogger_("Forbidden", timestamp, server, author, user, None, mrole)

                if clrcmd:
                    await asyncio.sleep(30)
                    await self.bot.delete_message(ctx.message)

    @commands.group(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def greetset(self, ctx):
        """Settings for greeter. Having the greeter role, member role and log channel set is required for greet to work fully."""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @greetset.command(name="grole", pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def _grole_(self, ctx, role: discord.Role):
        """Sets the greeter role for the server. You can either mention a role, or give me a role ID.\n [p]greetset mrole @user"""

        server = ctx.message.server

        self.settings[server.id]["greeterroleid"] = role.id
        self.save()
        embed = discord.Embed()
        embed.colour = discord.Colour.green()
        embed.description = "{} has been saved as the greeter role. Please note users with this role will be able to add the specified member role even if they don't have the perms to when greeter is enabled. You've been warned.".format(role.mention)
        name = "The greeter role was succesfully set."
        embed.set_author(name=name, icon_url="https://i.imgur.com/Kw0C9gK.png")
        await self.bot.say(embed = embed)


    @greetset.command(name="mrole", pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def _mrole_(self, ctx, role: discord.Role):
        """Sets the member role for the server. You can either mention a role, or give me a role ID.\n [p]greetset mrole @user"""

        server = ctx.message.server

        self.settings[server.id]["memberroleid"] = role.id
        self.save()
        embed = discord.Embed()
        embed.colour = discord.Colour.green()
        embed.description = "{} has been saved as the member role. Please note users with the greeter role will be able to add the this role to others when greeter is enabled.".format(role.mention)
        name = "The member role was succesfully set."
        embed.set_author(name=name, icon_url="https://i.imgur.com/Kw0C9gK.png")
        await self.bot.say(embed = embed)

    @greetset.command(name="cleanupcmd", pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def _cleanupcmd_(self, ctx):
        """Toggles weather the bot removes successfully triggered greet commands from greeters. Delays 30 seconds before doing so. \n [p]greetset cleanupcmd"""

        server = ctx.message.server
        clrcmd = self.settings[server.id].get("removetriggercmd")
        
        onemoji = discord.utils.get(self.bot.get_all_emojis(), id="330419505589256192").url
        offemoji = discord.utils.get(self.bot.get_all_emojis(), id="330419505563959296").url

        embed = discord.Embed()
        embed.colour = discord.Colour.green()
        
        if clrcmd is True:
            clrcmd = False
            embed.description = "Successfully triggered greet commands will not be deleted."
            embed.set_author(name="Greet command cleanup has been toggled off.", icon_url=offemoji)
            embed.colour = discord.Colour(0xEA2011)
            
        else:
            clrcmd = True
            embed.description = "Successfully triggered greet commands will be deleted."
            embed.set_author(name="Greet command cleanup has been toggled on.", icon_url=onemoji)
            embed.colour = discord.Colour.green()

        self.settings[server.id]["removetriggercmd"] = clrcmd
        self.save()

        await self.bot.say(embed = embed)

    @greetset.command(name="loggerchannel", pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def _logggerchannel_(self, ctx, channel: discord.Channel = None):
        """Sets the channel greeter will log to. Mention a channel with this command, or use it's ID to set it.\ni.e: [p]greetset loggerchannel #greeter-logs\n"""

        server = ctx.message.server
        
        try:
            embed = discord.Embed()
            embed.colour = discord.Colour.green()
            embed.description = "Testing to see if I can log here. If you see this it worked!"
            name = "Testing logging."
            embed.set_author(name=name, icon_url="https://i.imgur.com/z4qtYxT.png")
            embed.set_footer(text = "This test message will self delete in 30 seconds")
            test = await self.bot.send_message(destination = channel, embed = embed)

            #Passed
            self.settings[server.id]["greetlogchid"] = channel.id
            self.save()
            embed = discord.Embed()
            embed.colour = discord.Colour.green()
            embed.description = "{} has been saved as the channel greeter will log to.".format(channel.mention)
            name = "The log was succesfully set."
            embed.set_author(name=name, icon_url="https://i.imgur.com/Kw0C9gK.png")
            await self.bot.say(embed = embed)
            await asyncio.sleep(30)
            await self.bot.delete_message(test)

        except discord.Forbidden:
            embed = discord.Embed()
            embed.colour = discord.Colour.red()
            embed.description = "I do have permission to send messages to that channel (server={}, channel={})".format(server.id, channel.id)
            embed.set_thumbnail(url="https://i.imgur.com/zNU3Y9m.png")
            name = "The logging channel was not set!"
            embed.set_author(name=name, icon_url="https://i.imgur.com/zNU3Y9m.png")
            await self.bot.say(embed = embed)

    @greetset.command(name="greetchannel", pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def _greetchannel_(self, ctx, channel: discord.Channel = None):
        """Sets the channel greeters have to greet from, a channel tha `[p]greet` is locked to. Mention a channel with this command, or use it's ID to set it.\ni.e: [p]greetset greetchannel #greeter-logs\nIf no channel is given, the command is unlocked for use anywhere on the server."""

        server = ctx.message.server
        if channel is None:
            self.settings[server.id]["greetchannelid"] = None
            self.save()
            embed = discord.Embed()
            embed.colour = discord.Colour.green()
            embed.description = "The greeter channel has been cleared. The greet command can be used anywhere on the server."
            name = "The greeter channel was succesfully cleared."
            embed.set_author(name=name, icon_url="https://i.imgur.com/Kw0C9gK.png")
            await self.bot.say(embed = embed)
            return
        
        try:
            embed = discord.Embed()
            embed.colour = discord.Colour.green()
            embed.description = "Testing to see if I can post here. If you see this it worked!"
            name = "Testing greet channel."
            embed.set_author(name=name, icon_url="https://i.imgur.com/z4qtYxT.png")
            embed.set_footer(text = "This test message will self delete in 30 seconds")
            test = await self.bot.send_message(destination = channel, embed = embed)

            #Passed
            self.settings[server.id]["greetchannelid"] = channel.id
            self.save()
            embed = discord.Embed()
            embed.colour = discord.Colour.green()
            embed.description = "{} has been saved as the greeter channel.".format(channel.mention)
            name = "The greeter channel was succesfully set."
            embed.set_author(name=name, icon_url="https://i.imgur.com/Kw0C9gK.png")
            await self.bot.say(embed = embed)
            await asyncio.sleep(30)
            await self.bot.delete_message(test)

        except discord.Forbidden:
            embed = discord.Embed()
            embed.colour = discord.Colour.red()
            embed.description = "I do have permission to send messages to that channel (server={}, channel={})".format(server.id, channel.id)
            embed.set_thumbnail(url="https://i.imgur.com/zNU3Y9m.png")
            name = "The greeter channel was not set!"
            embed.set_author(name=name, icon_url="https://i.imgur.com/zNU3Y9m.png")
            await self.bot.say(embed = embed)

    @greetset.command(name="greeter", pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def _greeter_(self, ctx, switch):
        """Enable or disable the greeter cog for the server.\n [p]greetset swtich [enabled/disable]"""

        server = ctx.message.server
        onemoji = discord.utils.get(self.bot.get_all_emojis(), id="330419505589256192").url
        offemoji = discord.utils.get(self.bot.get_all_emojis(), id="330419505563959296").url
        embed = discord.Embed()
        embed.colour = discord.Colour(0xEA2011)

        if switch == "enable":
            enabled = True
            embed.description = "The greeter cog has been enabled for this server."
            embed.set_author(name="Greeter has been toggled on.", icon_url=onemoji)
            embed.colour = discord.Colour.green()
        
        elif switch == "disable":
            enabled = False
            embed.description = "The greeter cog has been disabled for this server."
            embed.set_author(name="Greeter has been toggled off.", icon_url=offemoji)
            embed.colour = discord.Colour(0xEA2011)

        self.settings[server.id]["enabled"] = enabled
        self.save()

        await self.bot.say(embed = embed)
    
    def _hasrole_(self, user, role):
        # Check if the given user has a role.

        for r in user.roles:
            if r is role:
                return True
        return False


    async def _greetlogger_(self, status, timestamp, server, greetuser = None, newuser = None, linkuser = None, mrole = None):
        # Logging for the greeter cog.
        logch = discord.utils.get(server.channels, id=self.settings[server.id].get("greetlogchid"))

        if status == "Success":

            embed = discord.Embed()
            embed.colour = discord.Colour.green()
            embed.description = "{} was given the {} role by {}\n\n {}'s ID: `{}`".format(newuser.mention, mrole.mention, greetuser.mention, newuser.name, newuser.id)
            embed.timestamp = timestamp
            name = "{} greeted {}".format(greetuser.name, newuser.name)
            embed.set_author(name=name, icon_url="https://i.imgur.com/Kw0C9gK.png")
            embed.set_thumbnail(url = newuser.avatar_url or discord.Embed.Empty)
            embed.set_footer(text = "Greeter {}'s ID: `{}`".format(greetuser.name, greetuser.id))

            try:
                await self.bot.send_message(destination = logch, embed = embed)
            except discord.Forbidden:
                self.bot.logger.warning(
                    "Did not have permission to send message to logging channel (server={}, channel={})".format(logch.server.id, logch.id)
                )

        elif status == "Success - Linked":

            embed = discord.Embed()
            embed.colour = discord.Colour.green()
            embed.description = "{} was given the {} role by {}\n\n {}'s ID: `{}`".format(newuser.mention, mrole.mention, greetuser.mention, newuser.name, newuser.id)
            embed.timestamp = timestamp
            name = "{} greeted {}".format(greetuser.name, newuser.name)
            embed.add_field(name="Linked Account:",
                               value="This Member is related to: {}\n{}'s ID: `{}`".format(linkuser.mention, linkuser.name, linkuser.id),
                               inline=False)
            embed.set_author(name=name, icon_url="https://i.imgur.com/Kw0C9gK.png")
            embed.set_thumbnail(url = newuser.avatar_url or discord.Embed.Empty)
            embed.set_footer(text = "Greeter {}'s ID: `{}`".format(greetuser.name, greetuser.id))

            try:
                await self.bot.send_message(destination = logch, embed = embed)
            except discord.Forbidden:
                self.bot.logger.warning(
                    "Did not have permission to send message to logging channel (server={}, channel={})".format(logch.server.id, logch.id)
                )
        
        elif status == "Forbidden":

            embed = discord.Embed()
            embed.colour = discord.Colour(0xEA2011)
            embed.description = "I failed to give {} the {} role as requested by {}. Do I still have the mangage_roles perm, and is the member role under my highest role?\n\n {}'s ID: `{}`".format(newuser.mention, mrole.mention, greetuser.mention, newuser.name, newuser.id)
            embed.timestamp = timestamp
            embed.set_thumbnail(url="https://i.imgur.com/zNU3Y9m.png")
            name = "{} attempted to welcome {}.".format(greetuser.name, newuser.name)
            embed.set_author(name=name, icon_url="https://i.imgur.com/zNU3Y9m.png")
            embed.set_footer(text = "Greeter {}'s ID: `{}`".format(greetuser.name, greetuser.id))

            try:
                await self.bot.send_message(destination = logch, embed = embed)
            except discord.Forbidden:
                self.bot.logger.warning(
                    "Did not have permission to send message to logging channel (server={}, channel={})".format(logch.server.id, logch.id)
                )

    def save(self):
        setpath = os.path.join('data', 'greeter', 'settings.json')
        dataIO.save_json(setpath, self.settings)


def check_folder():
    path = os.path.join('data', 'greeter')
    if not os.path.exists(path):
        print('Creating ' + path + '...')
        os.makedirs(path)

def check_files():

    files = {
        "settings.json": {}
    }
    datapath = os.path.join('data', 'greeter')
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