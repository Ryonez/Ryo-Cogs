from discord.ext import commands
from cogs.utils.dataIO import dataIO
from __main__ import send_cmd_help, settings
from cogs.utils.chat_formatting import pagify, box
from .utils import checks
import datetime
import discord
import os
from collections import defaultdict, OrderedDict
import asyncio

link_template = {
    "hostservername" : None,
    "subserverid" : None,
    "subservername" : None,
    "subserverinvchannel" : None,
    "subexemptrole" : None,
    "stage" : None,
    "stage5p" : None,
    "status" : None,
    "running" : False,
    "invitecode" : None,
    "invitemsg" : None,
    "statuschannel" : None,
    "subserverlockdown" : None,
    "memberprocessedcount" : 0,
    "subserversavedchanneloverrides" : {},
    "linkedroles" : {},
    "members" : {},
}
linked_template = {
    "hostroleid" : None,
    "subroleid" : None
}
channeloverride_template = {
            "type": None,
            "overrides": {}
        }
member_info_template = {
    "dm" : None,
    "lastdm" : None,
    "inv" : None,
    "processed" : False,
    "sroles" : {},
    "froles" : {}
}

class Servermerge:
    """ServerMerge"""

    setpath = os.path.join('data', 'servermerge', 'mservers.json')

    def __init__(self, bot):
        self.bot = bot
        setpath = os.path.join('data', 'servermerge', 'mservers.json')
        mservers = dataIO.load_json(setpath)
        self.mservers = defaultdict(lambda: link_template.copy(), mservers)
        self.sm_cache = {}

        self.react_menu_out = {
            "hellna": "res1hellna:330424101908905990",
            "hellyeah": "res1hellyeah:330424103259340800"
        }

        self.react_menu_in = {
            "hellna": "<:res1hellna:330424101908905990>",
            "hellyeah": "<:res1hellyeah:330424103259340800>"
        }

    @commands.group(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(Administrator=True)
    async def servermerge(self, ctx):
        """Servermerge."""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
            return


    @commands.command(name="mergesetup", pass_context=True, no_pm=True)
    @checks.serverowner()
    async def _mergesetup_(self, ctx: commands.Context, serverID):
        """This starts a server merge. START with this command. This is to be run from the server you wish to merge TO.\n- For security, This can only be run by the server owner, and you must give this command your server ID to start."""


        if ctx.message.server.id == serverID:
            await self._core_(ctx)

    @commands.command(name="mergeresume", pass_context=True, no_pm=True)
    @checks.serverowner()
    async def _mergeresume_(self, ctx: commands.Context):
        """Resumes a server merge. Run only from the host server"""

        server = ctx.message.server
        stage = self.mservers[server.id].get("stage")

        if stage is not None:
            await self.bot.say("Resuming merge!")
            await self._core_(ctx)
        else:
            embedmsg = discord.Embed(title="Information:\n\n",
                                     colour=discord.Colour(0xFF470F),
                                     description="This server is currently not being merged, run\n```[prefix]mergesetup```\nto begin..",
                                     timestamp=datetime.datetime.today())
            embedmsg.set_author(name="Server Merge Status",
                                icon_url="http://i.imgur.com/PUDZ1gT.png")
            #            embedmsg.set_footer(text="Made by " + ownername, icon_url=ownericon)
            await self.bot.say(embed=embedmsg)

    @commands.command(name="mergestatus", pass_context=True, no_pm=True)
    @checks.serverowner()
    async def _mergestatus_(self, ctx: commands.Context):

        server = ctx.message.server
        stage = self.mservers[server.id].get("stage")

        if stage is not None:
            subserverid = self.mservers[server.id].get("subserverid")
            subserver = discord.utils.get(self.bot.servers, id=subserverid)
            statuschannel = discord.utils.get(server.channels, id=self.mservers[server.id].get("statuschannel"))
            erole = discord.utils.get(subserver.roles,
                                              id=self.mservers[server.id].get("subexemptrole"))
            smembers = 0
            emembers = 0
            pmembers = self.mservers[server.id].get("memberprocessedcount")

            if erole is None:
                erolename = "*Not set!*"
                eroleid = "`Not set!`"
            else:
                erolename = erole.name
                eroleid = erole.id

            if statuschannel is None:
                statuschannelmention = "*Not set!*"
            else:
                statuschannelmention = statuschannel.mention


            # Create a list of members currently in both servers.
            for m in server.members:
                subm = subserver.get_member(m.id)
                if subm is not None:
                    smembers += 1
                    if self.isexempt(subm, erole):
                        emembers += 1

            if stage != "completed":
                embedmsg = discord.Embed(title="Information:\n\n",
                                     colour=discord.Colour(0xFF470F),
                                     description="This server is currently on `{}` of setup".format(stage),
                                     timestamp=datetime.datetime.today())
            else:
                embedmsg = discord.Embed(title="Information:\n\n",
                                         colour=discord.Colour(0xFF470F),
                                         timestamp=datetime.datetime.today())


            embedmsg.set_author(name="Server Merge Status",
                                icon_url="http://i.imgur.com/IqTP53r.png")
            embedmsg.set_thumbnail(url=server.icon_url)
            embedmsg.add_field(name="<:res1issue_open:330419505589256192> Hostserver info:",
                               value="Name: {}\nServerID: `{}`\nNumber of roles: {}\nNumber of members: {}".format(server.name, server.id, str(len(server.roles)), str(len(server.members))),
                               inline=False)
            embedmsg.add_field(name="<:res1issue_open:330419505589256192> Subserver info:",
                               value="Name: {}\nServerID: `{}`\nNumber of roles: {}\nExemption Role: \"{}\"`\nExemption Role ID: `{}`\nNumber of members: {}".format(
                                   subserver.name, subserver.id, str(len(subserver.roles)), erolename, eroleid,
                                   str(len(subserver.members))),
                                   inline=False)
            embedmsg.add_field(name="<:res1issue_open:330419505589256192> Misc info:",
                               value="Status channel: {}\nNumber of currently shared members: {}\nNumber of exempt members: {}\nMembers processed so far: {}".format(
                                   statuschannelmention, str(smembers), str(emembers), str(pmembers)),
                               inline=False)
            await self.bot.say(embed=embedmsg)
            return
        else:
            embedmsg = discord.Embed(title="Information:\n\n",
                                     colour=discord.Colour(0xFF470F),
                                     description="This server is currently not being merged, nothing to display.",
                                     timestamp=datetime.datetime.today())
            embedmsg.set_author(name="Server Merge Status",
                                icon_url="http://i.imgur.com/PUDZ1gT.png")
            await self.bot.say(embed=embedmsg)

    @commands.command(name="rolelist", pass_context=True, no_pm=True)
    @checks.serverowner()
    async def rolelist(self, ctx):
        """List the roles in the server and their Id's."""
        server = ctx.message.server

        # Creates a list of roles on the subserver that haven't got a link to any roles on the hostserver.
        msg = "Rolls the this server has.\nPosition: <ID> Name\n=============="
        for r in server.role_hierarchy:
            name = r.name
            position = r.position
            id = r.id
            msg += "\n " + str(position) + ": <" + id + "> " + name

        result = list(pagify(msg, shorten_by=16))

        for i, page in enumerate(result):
            if i != 0 and i % 4 == 0:
                last = await self.bot.say("There are still {} messages. "
                                          "Type `more` to continue."
                                          "".format(len(result) - i))
                msg = await self.bot.wait_for_message(author=ctx.message.author,
                                                      channel=ctx.message.channel,
                                                      content="more",
                                                      timeout=10)
                if msg is None:
                    try:
                        await self.bot.delete_message(last)
                    except:
                        pass
                    finally:
                        break
            await self.bot.say(box(page, lang="py"))

    @commands.command(name="retrysublockdown", pass_context=True, no_pm=True)
    @checks.serverowner()
    async def retrysublockdown(self, ctx):
        """Tries to lockdown all of the subserver's channels again. Will only work if the main setup's lockdown had issues.Old saved perm are overwritten.."""
        server = ctx.message.server

        embedmsg = discord.Embed(title="Retry Subserver Lockdown:\n\n",
                                 colour=discord.Colour(0xFF470F),
                                 timestamp=datetime.datetime.today())

        #Make sure that the main setup has attempted to lock the subserver already
        if self.mservers[server.id].get("subserverlockdown") != "partial":
            return

        # Try to lockdown the subserver
        error, fchannels = await self._subserverlockdown_(server)

        # Check if there was an issue saving all the overrides
        if error == "forbidden":
            msg = "Channels I couldn't edit:\n\n"
            for c in fchannels:
                msg += "- \"{}\" ({})| Failed to change overrides.\n".format(c.name, c.id)
                # pagify messages in case over 2k chars
            result = list(pagify(msg, shorten_by=16))
            embedmsg.add_field(name="<:res1error:330424101661442050> *Warning*",
                               value="```diff\n- I was unable to edit the channel overrides for the following channels.\n Please give the Administrator perm to my role and shift it to the top of the role list to continue. This will eliminate any permission issues.```\n\nTo try to lock all of the channels after changing the perms, you may try running `[prefix]retrysublockdown`.".format(
                                   c.name),
                               inline=False)
            await self.bot.say(embed=embedmsg)
            for i, page in enumerate(result):
                await self.bot.say(content=box(page, lang="diff"))
            self.mservers[server.id]["subserverlockdown"] = "partial"
        else:
            self.mservers[server.id]["subserverlockdown"] = "full"
        self.save()
        embedmsg.add_field(
            name="<:res1issue_open:330419505589256192> *Full Subserver Lockdown Successfull".format(server.owner.name))
        await self.bot.say(embed=embedmsg)

    @commands.command(name="removesublockdown", pass_context=True, no_pm=True)
    @checks.serverowner()
    async def removesublockdown(self, ctx):
        """Restores the overrides changed by the servermerge on the subserver from saved settings in the current merge."""
        server = ctx.message.server

        embedmsg = discord.Embed(title="Remove Subserver Lockdown:\n\n",
                                 colour=discord.Colour(0xFF470F),
                                 timestamp=datetime.datetime.today())

        await self.bot.say("Attempting to restore subserver perms(This can take a ***long*** time, do not run the command again until I give you a result).")

        # Make sure that the main setup has attempted to lock the subserver already
        if self.mservers[server.id].get("subserverlockdown") is None:
            return

        # Try to remove the lockdown the subserver
        error, fchannels = await self._removesubserverlockdown_(server)

        # Check if there was an issue saving all the overrides
        if error == "forbidden":
            msg = "Channels I couldn't edit:\n\n"
            for c in fchannels:
                msg += "- \"{}\" ({})| Failed to change overrides.\n".format(c.name, c.id)
                # pagify messages in case over 2k chars
            result = list(pagify(msg, shorten_by=16))
            embedmsg.add_field(name="<:res1error:330424101661442050> *Warning*",
                               value="```diff\n- I was unable to edit the channel overrides for the following channels.\n Please give the Administrator perm to my role and shift it to the top of the role list to continue. This will eliminate any permission issues.```\n\nTo try to lock all of the channels after changing the perms, you may try running `[prefix]retrysublockdown`.".format(
                                   c.name),
                               inline=False)
            await self.bot.say(embed=embedmsg)
            for i, page in enumerate(result):
                await self.bot.say(content=box(page, lang="diff"))
            self.mservers[server.id]["subserverlockdown"] = "partial"
        else:
            self.mservers[server.id]["subserverlockdown"] = "full"
        self.save()
        embedmsg.add_field(name="<:res1issue_open:330419505589256192> Subserverperms were restored sucessfully", value = "The values changed by the merge have been reversed.")
        await self.bot.say(embed=embedmsg)


    @commands.command(name="regeninvite", pass_context=True, no_pm=True)
    @checks.serverowner()
    async def regeninvite(self, ctx):
        """Creates a new invite code an sends it to the Subserver's invite channel."""
        server = ctx.message.server
        invitecode = self.mservers[server.id].get("invitecode")
        hinvites = await self.bot.invites_from(server)

        embedmsg = discord.Embed(title="Invite Regen:\n\n",
                                     colour=discord.Colour(0xFF470F),
                                     timestamp=datetime.datetime.today())

        # Check for a valid saved invite, create one if not found. Throws crit error and halts on fail.
        for i in hinvites:
            if i.code == invitecode:
                invite = i
                embedmsg.add_field(
                    name=":incoming_envelope: *Invite Code Found*".format(server.owner.name),
                    value="There's no need to regen, the code I have is still valid: " + invite.code,
                    inline=False)
                await self.bot.say(embed=embedmsg)
        if invite is None:
            try:
                invite = await self.bot.create_invite(server.default_channel, max_age = 0)
                self.mservers[server.id]["invitecode"] = invite.code
                self.save()
                embedmsg.add_field(
                    name=":incoming_envelope: *Invite Regerated*".format(server.owner.name),
                    value=invite.code,
                    inline=False)
                await self.bot.say(embed=embedmsg)
            except discord.Forbidden:
                embedmsg.add_field(name="<:res1error:330424101661442050> *Warning*",
                                  value="```diff\n- I'm not allowed to make an invite for {}\n Please give the Administrator perm to my role to continue. This will eliminate any permission issues.```".format(
                                      server.name),
                                  inline=False)
                await self.bot.say(embed=embedmsg)
                return

    @commands.command(name="mergepause", pass_context=True, no_pm=True)
    @checks.serverowner()
    async def mergepause(self, ctx, timeout: int = 30):
        """Pauses the current servermerge. Only work when the merge setup is complete."""
        server = ctx.message.server

        if self.mservers[server.id]["stage5p"] != "complete":
            return

        embedmsg = discord.Embed(colour=discord.Colour(0x0090f0),
                                 timestamp=datetime.datetime.today())
        embedmsg.set_author(name="Mergehalt",
                            icon_url="http://i.imgur.com/T5L6Djq.png")
        embedmsg.set_thumbnail(url="https://i.imgur.com/zNU3Y9m.png")
        embedmsg.add_field(name="<:res1error:330424101661442050> *Warning!!!*",
                           value="You are about to pause the current servermerge.\n\nTo pause the merge, type `yes`.\nTo cancel, type `no`.",
                           inline=False)
        await self.bot.say(embed=embedmsg)

        response = await self.bot.wait_for_message(timeout=timeout,
                                                   author=ctx.message.author,
                                                   channel=ctx.message.channel)
        if response is None:
            await self.bot.say("Timed out.")
        elif response == "yes":
            await self.bot.say("Merge has been paused!")
            self.mservers[server.id]["running"] = False
            self.save()
        elif response == "no":
            return
        else:
            self.bot.say("Unexpected response, canceling.")


    @commands.command(name="mergedelete", pass_context=True, no_pm=True)
    @checks.serverowner()
    async def mergedelete(self, ctx, timeout: int=30):
        """Complete closes the current servermerge, and deletes all settings."""
        server = ctx.message.server
        emoji_out = self.react_menu_out.get('emoji', self.react_menu_out)
        emoji_in = self.react_menu_in.get('emoji', self.react_menu_in)

        embedmsg = discord.Embed(colour=discord.Colour(0x0090f0),
                                 timestamp=datetime.datetime.today())
        embedmsg.set_author(name="Merge Deletion",
                            icon_url="http://i.imgur.com/T5L6Djq.png")
        embedmsg.set_thumbnail(url="https://i.imgur.com/zNU3Y9m.png")
        embedmsg.add_field(name="<:res1error:330424101661442050> *Warning!!!*",
                           value="You are about to delete the current servermerge\n```diff\n- THIS WILL DELETE ALL SAVED SETTINGS, INCLUDING SAVED CHANNEL OVERRIDES FOR THE SUBSERVER!```\n\nTo **delete** the merge, react with hellyeah to this message.\nTo cancel, react with hellna to this message.",
                           inline=False)
        message = await self.bot.say(embed=embedmsg)
        await self.bot.add_reaction(message, str(emoji_out['hellna']))
        await self.bot.add_reaction(message, str(emoji_out['hellyeah']))
        r = await self.bot.wait_for_reaction(
            message=message,
            user=ctx.message.author,
            timeout=timeout)
        if r is None:
            try:
                try:
                    await self.bot.clear_reactions(message)
                except:
                    await self.bot.remove_reaction(message, "res1hellna:330424101908905990", self.bot.user)
                    await self.bot.remove_reaction(message, "res1hellyeah:330424103259340800", self.bot.user)
                await self.bot.say("Timed out.")
            except:
                pass
            return None
        reacts = {v: k for k, v in emoji_in.items()}
        try:
            react = reacts[str(r.reaction.emoji)]
        except:
            await self.bot.say(
                "Baka, you added a different or selected a different reaction! Canceling!")
            return
        if react == "hellna":
            await self.bot.say("Returning to the main menu.")

        elif react == "hellyeah":
            try:
                del self.mservers[server.id]
                self.save()
                await self.bot.say("The merge settings for this server have been deleted!")
            except KeyError:
                pass
            return
        else:
            try:
                await self.bot.say("Oh god, something really broke...")
            except:
                pass

    async def _core_(self, ctx):

        server = ctx.message.server
        stage = self.mservers[server.id].get("stage")
        statuschannel = discord.utils.get(server.channels, id=self.mservers[server.id].get("statuschannel"))

        if stage == "complete" and self.mservers[server.id]["running"] is False:
            self.mservers[server.id]["running"] = True
            self.save()
            await self.bot.say("Reprocessing shared members.")
            await self._stage5p4_(ctx, statuschannel)

        if stage is None:
            await self._startup_(ctx)
            stage = self.mservers[server.id].get("stage")

        if stage == "stage1":
            await self._stage1_(ctx)
            stage = self.mservers[server.id].get("stage")

        if stage == "stage3":
            await self._stage3_(ctx)
            stage = self.mservers[server.id].get("stage")

        if stage == "stage4":
            await self._stage4_(ctx)
            stage = self.mservers[server.id].get("stage")

        if stage == "stage5":
            await self._stage5_(ctx)

    async def _startup_(self, ctx, timeout: int=30):

        #Setting up the initial disclaimer
        server = ctx.message.server
        servername = ctx.message.server.name
        servericon = ctx.message.server.icon_url
        ts = datetime.datetime.today()
        emoji_out = self.react_menu_out.get('emoji', self.react_menu_out)
        emoji_in = self.react_menu_in.get('emoji', self.react_menu_in)

        embedmsg = discord.Embed(title="<:res1mikudoom:330424102915407872> Warning!:\n\n",
                                 colour=discord.Colour(0xFF0000),
                                 description="```diff\n- This command starts to set up a server merge. Once the host and sub servers have been connected and the process begins, changes made are unrreversable. You have been warned```",
                                 timestamp=ts)
        embedmsg.set_author(name="Server Merge Setup",
                            icon_url="http://i.imgur.com/9B8LMZV.png")
        embedmsg.set_thumbnail(url=servericon)
        embedmsg.add_field(name=":grey_question: *What's about to happen (READ THIS COMPLETELY FIRST)*",
                           value="This server is about to be setup as the hub of a server merge. once this and the sub server is set up, I'll be creating an invite for this server and users from the sub server will be given roles that have been linked, based on what they have. The following steps will be done:",
                           inline=False)
        embedmsg.add_field(name=":grey_question: *Stage 1 and 2*",
                           value="```diff\nYou will comfirm you wish to continue.\nThen, you will need to provide a passcode via dm to me. This is to provide security against a sub server connecting without your authorisation.This password will be kept in memory, If I need to reboot or clean my memory before the subserver has been linked, you'll need to come back here and run this same command again to restart.\nAfter you give me a password, I'll confirm it has been set here(Without displaying it) then you'll need to go to the sub server, the server you are mergeing into this one, and run {prefix}subsetup. This will point it to this HOST server. There you'll need to provide you password to link the servers. Congratz, the hard part is done!```",
                           inline=False)
        embedmsg.add_field(name=":grey_question: *Stage 3*",
                           value="```diff\nCome back to the HOST server(here). I'll go through and match up the roles based on their names. You'll get to confirm these, and remove any links, or add ones with mismatched names. At this time you'll need to supply an expemtion role id(you can find a role id by going to the sub server and running `[prefix]rolelist`). You'll also be asked for a channel ID fpr the subserver, for me to post the invite for everyone I can't dm, and ping them.```",
                           inline=False)
        embedmsg.add_field(name=":grey_question: *Stage 4*",
                           value="```diff\nI'll ask you for a message you want for the DM's.\n\nThen, I'll create a channel called \"servermerge\" and shift it to the top of the list. The channel by default will have read_messages perms denied for the everone role. This channel will log users moving over and the roles I give them. Then I'll dm everyone on the subserver, process those alread in both, and continue watching for people to join until I'm paused on stopped.\n\nI will ask you for the message you'd like the users of the sub server to get with an invite to the HOST server.\n\n To stop me, run `[prefix]mergepause`(Pause the member processing) or `[prefix]mergedelete`(Stop the mergeing and deletes the current merge settings)\n\nFinal step: Go have a drink with the time you've saved >.<```",
                           inline=False)
        embedmsg.add_field(name=":grey_question: *Stage 5*",
                           value="```diff\nI'll create a channel called \"servermerge\" and shift it to the top of the list. The channel by default will have read_messages perms denied for the everone role. This channel will log users moving over and the roles I give them. Then I'll dm everyone on the subserver, process those already in both, and continue watching for people to join until I'm paused on stopped.\n To stop me, run `[prefix]mergepause`(Pause the member processing) or `[prefix]mergedelete`(Stop the mergeing and deletes the current merge settings)\n\nFinal step: Go have a drink with the time you've saved >.<```",
                           inline=False)
        embedmsg.add_field(name="*Stopping me when your done with the merge*",
                           value="To stop me, run `[prefix]mergepause`(Pause the member processing) or `[prefix]mergedelete`(Stop the mergeing and deletes the current merge settings)Final step: Go have a drink with the time you've saved >.<```",
                           inline=False)
        embedmsg.add_field(name="*Bonus Step*",
                           value="Go have a drink with the time you've saved >.<",
                           inline=False)
        embedmsg.add_field(name=":white_check_mark: *Prechecks Completed*",
                           value="```diff\n+ Server ID provided\n+ Server not currently the hub of another merge```",
                           inline=False)

        message = await self.bot.send_message(ctx.message.channel, embed=embedmsg)
        await self.bot.add_reaction(message, str(emoji_out['hellna']))
        await self.bot.add_reaction(message, str(emoji_out['hellyeah']))
        r = await self.bot.wait_for_reaction(
            message=message,
            user=ctx.message.author,
            timeout=300)
        if r is None:
            try:
                try:
                    await self.bot.clear_reactions(message)
                except:
                    await self.bot.remove_reaction(message, "res1hellna:330424101908905990", self.bot.user)
                    await self.bot.remove_reaction(message, "res1hellyeah:330424103259340800", self.bot.user)
                await self.bot.say("No react")
                await self.bot.delete_message(message)
            except:
                pass
            return None
        reacts = {v: k for k, v in emoji_in.items()}
        try:
            react = reacts[str(r.reaction.emoji)]
        except:
            await self.bot.say("Baka, you added a different or selected a different reaction! Back to square one you go!")
            await self.bot.delete_message(message)
            return
        if react == "hellna":
            await self.bot.delete_message(message)
            message = await self.bot.say("Merge Canceled")

        elif react == "hellyeah":
                self.mservers[server.id]["hostservername"] = server.name
                self.mservers[server.id]["stage"] = "stage1"
                self.mservers[server.id]["status"] = "Being set up."
                self.save()
                await self.bot.say("Understood: Shifting to stage 1.")
                return
        else:
            try:
                await self.bot.say("Oh god, something really broke...")
                await self.bot.delete_message(message)
                return
            except:
                pass

    async def _stage1_(self, ctx, delay: int=1, timeout: int=30):

        server = ctx.message.server
        sowner = ctx.message.author

        embedmsg = discord.Embed(colour=discord.Colour(0xFF470F),
                                 description="I will now send you a dm requesting you to set a temporary password to link to this server with.",
                                 timestamp=datetime.datetime.today())
        embedmsg.set_author(name="Stage 1 - Password",
                            icon_url="http://i.imgur.com/IqTP53r.png")
        embedmsg.set_thumbnail(url=server.icon_url)

        await self.bot.say(embed=embedmsg)

        embedmsg = discord.Embed(colour=discord.Colour(0xFF470F),
                                 description="Please enter a password to use to link the server you're mergering from.\nNote, this password is kept in memory only and will be cleared after the link is made.\nYou have " + str(timeout) + " seconds to enter one.",
                                 timestamp=datetime.datetime.today())
        embedmsg.set_author(name="Stage 1 - Password Input for " + server.name,
                            icon_url="http://i.imgur.com/IqTP53r.png")
        embedmsg.set_thumbnail(url=server.icon_url)
        msg = await self.bot.send_message(destination=sowner, embed=embedmsg)
        password = await self.bot.wait_for_message(timeout=timeout,
                                             author=sowner,
                                             channel=msg.channel)
        if password is None:
            embedmsg = discord.Embed(colour=discord.Colour(0xFF470F),
                                     description="No password was given, stopping.",
                                     timestamp=datetime.datetime.today())
            embedmsg.set_author(name="Stage 1 - Password",
                                icon_url="http://i.imgur.com/IqTP53r.png")
            embedmsg.set_thumbnail(url=server.icon_url)
            embedmsg.add_field(name="<:res1Rachet:332453473884962816> *Info*",
                               value="To resume, please run:\n```[prefix]mergeresume```",
                               inline=False)
            await self.bot.say(embed=embedmsg, content=ctx.message.author.mention)
        else:
            await self._stage2_(ctx, password)
            return

    async def _stage2_(self, ctx, password, delay: int=1, timeout: int=60):

        server = ctx.message.server
        sowner = ctx.message.author

        embedmsg = discord.Embed(colour=discord.Colour(0xFF470F),
                                 description="Now I'll need to know the server you wish to merge FROM. Please provide the subserver's ID. Please note, I must already be in that server.\nYou have " + str(timeout) + " seconds to enter one.",
                                 timestamp=datetime.datetime.today())
        embedmsg.set_author(name="Stage 2 - Subserver Link",
                            icon_url="http://i.imgur.com/IqTP53r.png")
        embedmsg.set_thumbnail(url=server.icon_url)
        await self.bot.say(embed=embedmsg, content=ctx.message.author.mention)
        subserverid = await self.bot.wait_for_message(timeout=timeout,
                                             author=sowner,
                                             channel=ctx.message.channel)
        if subserverid is None:
            embedmsg = discord.Embed(colour=discord.Colour(0xFF470F),
                                     description="No subserver ID was given, stopping.",
                                     timestamp=datetime.datetime.today())
            embedmsg.set_author(name="Stage 2 - Subserver Link",
                                icon_url="http://i.imgur.com/IqTP53r.png")
            embedmsg.set_thumbnail(url=server.icon_url)
            embedmsg.add_field(name="<:res1Rachet:332453473884962816> *Info*",
                               value="To resume, please run:\n```[prefix]mergeresume```",
                               inline=False)
            await self.bot.say(embed=embedmsg)
        else:
            subserver = discord.utils.get(self.bot.servers, id=subserverid.content)
            if subserver is not None and ctx.message.author.id == subserver.owner_id and subserver.default_channel.permissions_for(subserver.me).administrator is True:
                embedmsg = discord.Embed(colour=discord.Colour(0xFF470F),
                                         description="Subserver found\nServer Name: " +subserver.name +"\nPlease provide the channel ID for where you wish to enter the link password.\nYou have " + str(
                                             timeout) + " seconds to enter one.",
                                         timestamp=datetime.datetime.today())
                embedmsg.set_author(name="Stage 2 - Subserver Link",
                                    icon_url="http://i.imgur.com/IqTP53r.png")
                embedmsg.set_thumbnail(url=subserver.icon_url)
                await self.bot.say(embed=embedmsg)
                subserverchannelid = await self.bot.wait_for_message(timeout=timeout,
                                                              author=sowner,
                                                              channel=ctx.message.channel)
                if subserverchannelid is None:
                    embedmsg = discord.Embed(colour=discord.Colour(0xFF470F),
                                             description="No subserver channel ID was given, stopping.",
                                             timestamp=datetime.datetime.today())
                    embedmsg.set_author(name="Stage 2 - Subserver Link",
                                        icon_url="http://i.imgur.com/IqTP53r.png")
                    embedmsg.set_thumbnail(url=server.icon_url)
                    embedmsg.add_field(name="<:res1Rachet:332453473884962816> *Info*",
                                       value="To resume, please run:\n```[prefix]mergeresume```",
                                       inline=False)
                    await self.bot.say(embed=embedmsg)
                else:
                    subserverchannel = discord.utils.get(subserver.channels, id=subserverchannelid.content)
                    if subserverchannel is None:
                        embedmsg = discord.Embed(colour=discord.Colour(0xFF0000),
                                                 timestamp=datetime.datetime.today())
                        embedmsg.set_author(name="Stage 2 - Subserver Link",
                                            icon_url="http://i.imgur.com/IqTP53r.png")
                        embedmsg.set_thumbnail(url=server.icon_url)
                        embedmsg.add_field(name="<:res1error:330424101661442050> *Error!*",
                                           value="```diff\n- That channel does not exist, please try again```",
                                           inline=False)
                        embedmsg.add_field(name="<:res1Rachet:332453473884962816> *Info*",
                                           value="To resume, please run:\n```[prefix]mergeresume```\n with a valid channel id",
                                           inline=False)
                        await self.bot.say(embed=embedmsg)

                    if subserverchannel is not None:
                        embedmsg = discord.Embed(colour=discord.Colour(0xFF470F),
                                                 description="Subserver found\nServer Name: " + subserver.name + "\nPlease enter the link password to confirm subserver link.\nYou have " + str(
                                                     timeout) + " seconds to enter one.",
                                                 timestamp=datetime.datetime.today())
                        embedmsg.set_author(name="Stage 2 - Subserver Link",
                                            icon_url="http://i.imgur.com/IqTP53r.png")
                        embedmsg.set_thumbnail(url=subserver.icon_url)
                        await self.bot.send_message(destination=subserverchannel, embed=embedmsg, content=ctx.message.author.mention)
                        subpassword = await self.bot.wait_for_message(timeout=timeout,
                                                                             author=sowner,
                                                                             content=password.content,
                                                                             channel=subserverchannel)
                        if subpassword is None:
                            embedmsg = discord.Embed(colour=discord.Colour(0xFF0000),
                                                    description="Subserver found\nServer Name: " + subserver.name,
                                                    timestamp=datetime.datetime.today())
                            embedmsg.set_author(name="Stage 2 - Subserver Link",
                                                icon_url="http://i.imgur.com/IqTP53r.png")
                            embedmsg.set_thumbnail(url=subserver.icon_url)
                            embedmsg.add_field(name="<:res1error:330424101661442050> *Error!*",
                                               value="```diff\n- The correct password was not given```",
                                               inline=False)
                            embedmsg.add_field(name="<:res1Rachet:332453473884962816> *Info*",
                                               value="To resume, please run:\n```[prefix]mergeresume```\nand enter matching passwords.",
                                               inline=False)
                            await self.bot.send_message(destination=subserverchannel, embed=embedmsg)
                            await self.bot.say(embed=embedmsg, content=ctx.message.author.mention)
                        if subpassword is not None:
                            embedmsg = discord.Embed(colour=discord.Colour(0x00ff52),
                                                     description="Password correct\nHostserver:\n```" + server.name + "```\nSubserver:\n```" + subserver.name + "```\nShifting to stage 3",
                                                     timestamp=datetime.datetime.today())
                            embedmsg.set_author(name="Stage 2 - Subserver Link Established",
                                                icon_url="http://i.imgur.com/T5L6Djq.png")
                            embedmsg.set_thumbnail(url=subserver.icon_url)
                            await self.bot.send_message(destination=subserverchannel, embed=embedmsg)
                            await self.bot.say(embed=embedmsg, content=ctx.message.author.mention)
                            self.mservers[server.id]["subserverid"] = subserver.id
                            self.mservers[server.id]["subservername"] = subserver.name
                            self.mservers[server.id]["stage"] = "stage3"
                            self.mservers[server.id]["status"] = "Role links."
                            self.save()
                            return

            elif subserver is not None and ctx.message.author.id != subserver.owner_id:
                embedmsg = discord.Embed(colour=discord.Colour(0xFF0000),
                                         description="Subserver found\nServer Name: " +subserver.name,
                                         timestamp=datetime.datetime.today())
                embedmsg.set_author(name="Stage 2 - Subserver Link",
                                    icon_url="http://i.imgur.com/IqTP53r.png")
                embedmsg.set_thumbnail(url=subserver.icon_url)
                embedmsg.add_field(name="<:res1error:330424101661442050> *Error!*",
                                   value="```diff\n- YOU ARE NOT THE OWNER OF THE SUBSERVER, UNABLE TO CONTINUE!```",
                                   inline=False)
                embedmsg.add_field(name="<:res1Rachet:332453473884962816> *Info*",
                                   value="To resume, please run:\n```[prefix]mergeresume```\nand select another server.",
                                   inline=False)
                await self.bot.say(embed=embedmsg)

            elif subserver is not None and subserver.default_channel.permissions_for(subserver.me).administrator is False:
                embedmsg = discord.Embed(colour=discord.Colour(0xFF0000),
                                         description="Subserver found\nServer Name: " + subserver.name,
                                         timestamp=datetime.datetime.today())
                embedmsg.set_author(name="Stage 2 - Subserver Link",
                                    icon_url="http://i.imgur.com/IqTP53r.png")
                embedmsg.set_thumbnail(url=subserver.icon_url)
                embedmsg.add_field(name="<:res1error:330424101661442050> *Error!*",
                                   value="```diff\n- I do not have Server Administrator perms. This is required to eliminate any permission issues. Please give the Administrator perm to my role to continue.```",
                                   inline=False)
                embedmsg.add_field(name="<:res1Rachet:332453473884962816> *Info*",
                                   value="To resume, please run:\n```[prefix]mergeresume```\nonce this is done.",
                                   inline=False)
                await self.bot.say(embed=embedmsg)

            else:
                embedmsg = discord.Embed(colour=discord.Colour(0xFF0000),
                                         timestamp=datetime.datetime.today())
                embedmsg.set_author(name="Stage 2 - Subserver Link",
                                    icon_url="http://i.imgur.com/IqTP53r.png")
                embedmsg.set_thumbnail(url=server.icon_url)
                embedmsg.add_field(name="<:res1error:330424101661442050> *Error!*",
                                   value="```diff\n- I'm not in that server, please try again```",
                                   inline=False)
                embedmsg.add_field(name="<:res1Rachet:332453473884962816> *Info*",
                                   value="To resume and select another server, please run:\n```[prefix]mergeresume```",
                                   inline=False)
                await self.bot.say(embed=embedmsg)

    async def _stage3_(self, ctx, delay: int=3, timeout: int=120):

        server = ctx.message.server
        author = ctx.message.author
        channel = ctx.message.channel
        subserverid = self.mservers[server.id].get("subserverid")
        subserver = discord.utils.get(self.bot.servers, id=subserverid)
        emoji_out = self.react_menu_out.get('emoji', self.react_menu_out)
        emoji_in = self.react_menu_in.get('emoji', self.react_menu_in)
        serverroles = [r for r in server.role_hierarchy]
        hostrolenum = len(serverroles)
        subserverroles = [r for r in subserver.role_hierarchy]
        subrolenum = len(subserverroles)
        administratorroles = []
        manageserverroles = []
        managerolesroles = []
        managechannelsroles = []
        banserverroles = []
        kickserverroles = []
        safeserverroles = []
        subnomatchroles = []
        hostnomatchroles = []
        linkedroles = defaultdict(lambda: linked_template.copy())
        linkcounter = 0
        linknum = -1
        manuallinkedroles = []
        safetytrip = False

        embedmsg = discord.Embed(colour=discord.Colour(0xFF0000),
                                 timestamp=datetime.datetime.today())
        embedmsg.set_author(name="Stage 3 - Role Links",
                            icon_url="http://i.imgur.com/T5L6Djq.png")
        embedmsg.add_field(name="<:res1Rachet:332453473884962816> *Info*",
                           value="I'll now scan for roles with matching names. Please give me a few minutes, I'll say when I'm done",
                           inline=False)
        await self.bot.say(embed=embedmsg)

        embedmsg = discord.Embed(colour=discord.Colour(0xFF0000),
                                 timestamp=datetime.datetime.today())
        embedmsg.set_author(name="Stage 3 - Role Links",
                            icon_url="http://i.imgur.com/T5L6Djq.png")
        embedmsg.add_field(name="<:res1Rachet:332453473884962816> *Info*",
                           value="Roles lists retrieved, scanning names",
                           inline=False)
        embedmsg.add_field(name=":sparkle: Hostserver Info",
                           value= str(hostrolenum) + " role/s found",
                           inline=True)
        embedmsg.add_field(name=":sparkle: Subserver Info",
                           value= str(subrolenum) + " role/s found",
                           inline=True)
        status = await self.bot.say(embed=embedmsg)

        for r in serverroles:
            submatch = discord.utils.get(subserver.role_hierarchy, name=r.name)
            if submatch is not None:
                if r.permissions.administrator is True:
                    administratorroles.append(submatch)
                    hostnomatchroles.append(submatch)
                    safetytrip = True
                elif r.permissions.manage_server is True:
                    manageserverroles.append(submatch)
                    hostnomatchroles.append(submatch)
                    safetytrip = True
                elif r.permissions.manage_roles is True:
                    managerolesroles.append(submatch)
                    hostnomatchroles.append(submatch)
                    safetytrip = True
                elif r.permissions.manage_channels is True:
                    managechannelsroles.append(submatch)
                    hostnomatchroles.append(submatch)
                    safetytrip = True
                elif r.permissions.ban_members is True:
                    banserverroles.append(submatch)
                    hostnomatchroles.append(submatch)
                    safetytrip = True
                elif r.permissions.kick_members is True:
                    kickserverroles.append(submatch)
                    hostnomatchroles.append(submatch)
                    safetytrip = True
                elif r == server.default_role:
                    pass
                else:
                    safeserverroles.append(r)
                    linkedroles[linkcounter]["hostroleid"] = r.id
                    linkedroles[linkcounter]["subroleid"] = submatch.id
                    linkcounter += 1
            else:
                hostnomatchroles.append(r)

        for r in subserverroles:
            submatch = discord.utils.get(server.role_hierarchy, name=r.name)
            if submatch is not None:
                if submatch.permissions.administrator is True:
                    subnomatchroles.append(r)
                elif submatch.permissions.manage_server is True:
                    subnomatchroles.append(r)
                elif submatch.permissions.manage_roles is True:
                    subnomatchroles.append(r)
                elif submatch.permissions.manage_channels is True:
                    subnomatchroles.append(r)
                elif submatch.permissions.ban_members is True:
                    subnomatchroles.append(r)
                elif submatch.permissions.kick_members is True:
                    subnomatchroles.append(r)
            else:
                subnomatchroles.append(r)

        saferolenum = len(safeserverroles)
        subnomatchrolenum = len(subnomatchroles)
        hostnomatchrolenum = len(hostnomatchroles)
        if saferolenum is not None:
            embedmsg.add_field(name=":sparkle: Saferoles Info",
                               value=str(saferolenum) + " role/s found",
                               inline=True)
        if hostnomatchrolenum is not None:
            embedmsg.add_field(name=":sparkle: Roles on this server no matches",
                               value=str(hostnomatchrolenum) + " role/s missing",
                               inline=False)
        if subnomatchrolenum is not None:
            embedmsg.add_field(name=":sparkle: Roles on the subserver with no matches",
                               value=str(subnomatchrolenum) + " role/s missing",
                               inline=False)
        await self.bot.edit_message(status, embed=embedmsg)

        menu = 'waiting'

        while menu == 'waiting':

            embedmsg = discord.Embed(colour=discord.Colour(0xFF0000),
                                     timestamp=datetime.datetime.today())
            embedmsg.set_author(name="Stage 3 - Role Links",
                                icon_url="http://i.imgur.com/T5L6Djq.png")
            embedmsg.add_field(name="<:res1Rachet:332453473884962816> *Info*",
                               value="I have created a list of Linked Roles based made from name of roles that match between the servers. Roles with the following perms on this server are *excluded*\n```diff\n- Administrator\n- Manage Server\n- Manage_Roles\n- Manage Channels\n- Ban Members\n- Kick Members```\n\nType `yes` if you wish to start with this list\n\nType `no` if you wish to start from scratch",
                               inline=False)
            await self.bot.say(embed=embedmsg)
            response = await self.bot.wait_for_message(timeout=timeout,
                                                       author=author,
                                                       channel=ctx.message.channel)
            if response is None:
                embedmsg = discord.Embed(colour=discord.Colour(0xFF0000),
                                         timestamp=datetime.datetime.today())
                embedmsg.set_author(name="Stage 3 - Role Links",
                                    icon_url="http://i.imgur.com/T5L6Djq.png")
                embedmsg.add_field(name="<:res1Rachet:332453473884962816> *Info*",
                                   value="Timed out. To resume, please run:\n```[prefix]mergeresume```",
                                   inline=False)
                await self.bot.say(embed=embedmsg)

            elif response.content == 'yes':

                if safetytrip is True:
                    embedmsg = discord.Embed(colour=discord.Colour(0xFF0000),
                                             timestamp=datetime.datetime.today())
                    embedmsg.set_author(name="Stage 3 - Role Links",
                                        icon_url="http://i.imgur.com/T5L6Djq.png")
                    embedmsg.set_thumbnail(url="https://i.imgur.com/zNU3Y9m.png")
                    embedmsg.add_field(name="<:res1Rachet:332453473884962816> *Info*",
                                       value="The following roles have not been linked because of the perms they have listed on this server:",
                                       inline=False)
                    safetyalert = await self.bot.say(embed=embedmsg)

                    if len(administratorroles) != 0:
                        administratorrolesmsg = "Roles with administrator perms.\nPosition: ID > Name\n=============="
                        for r in administratorroles:
                            name = r.name
                            position = r.position
                            id = r.id
                            administratorrolesmsg += "\n- " + str(position) + ": " + id + " > " + name

                        adminresult = list(pagify(administratorrolesmsg, shorten_by=16))
                        for i, page in enumerate(adminresult):
                            if i != 0 and i % 4 == 0:
                                last = await self.bot.say("There are still {} messages. "
                                                          "Type `more` to continue."
                                                          "".format(len(adminresult) - i))
                                msg = await self.bot.wait_for_message(author=author,
                                                                      channel=channel,
                                                                      content="more",
                                                                      timeout=10)
                                if administratorrolesmsg is None:
                                    try:
                                        await self.bot.delete_message(last)
                                    except:
                                        pass
                                    finally:
                                        break
                            await self.bot.say(box(page))

                    if len(manageserverroles) != 0:
                        manageserverrolesmsg = "Roles with manage server perms.\nPosition: ID > Name\n=============="
                        for r in manageserverroles:
                            name = r.name
                            position = r.position
                            id = r.id
                            manageserverrolesmsg += "\n- " + str(position) + ": " + id + " > " + name

                            manageserverrolesresult = list(pagify(manageserverrolesmsg, shorten_by=16))
                        for i, page in enumerate(manageserverrolesresult):
                            if i != 0 and i % 4 == 0:
                                last = await self.bot.say("There are still {} messages. "
                                                          "Type `more` to continue."
                                                          "".format(len(manageserverrolesresult) - i))
                                msg = await self.bot.wait_for_message(author=author,
                                                                      channel=channel,
                                                                      content="more",
                                                                      timeout=10)
                                if manageserverrolesmsg is None:
                                    try:
                                        await self.bot.delete_message(last)
                                    except:
                                        pass
                                    finally:
                                        break
                            await self.bot.say(box(page))

                    if len(managerolesroles) != 0:
                        managerolesrolesmsg = "Roles with manage roles perms.\nPosition: ID > Name\n=============="
                        for r in managerolesroles:
                            name = r.name
                            position = r.position
                            id = r.id
                            managerolesrolesmsg += "\n- " + str(position) + ": " + id + " > " + name

                            managerolesrolesresult = list(pagify(managerolesrolesmsg, shorten_by=16))
                        for i, page in enumerate(managerolesrolesresult):
                            if i != 0 and i % 4 == 0:
                                last = await self.bot.say("There are still {} messages. "
                                                          "Type `more` to continue."
                                                          "".format(len(managerolesrolesresult) - i))
                                msg = await self.bot.wait_for_message(author=author,
                                                                      channel=channel,
                                                                      content="more",
                                                                      timeout=10)
                                if managerolesrolesmsg is None:
                                    try:
                                        await self.bot.delete_message(last)
                                    except:
                                        pass
                                    finally:
                                        break
                            await self.bot.say(box(page))

                    if len(managechannelsroles) != 0:
                        managechannelsrolesmsg = "Roles with manage channels perms.\nPosition: ID > Name\n=============="
                        for r in managechannelsroles:
                            name = r.name
                            position = r.position
                            id = r.id
                            managechannelsrolesmsg += "\n- " + str(position) + ": " + id + " > " + name

                            managechannelsrolesresult = list(pagify(managechannelsrolesmsg, shorten_by=16))
                        for i, page in enumerate(managechannelsrolesresult):
                            if i != 0 and i % 4 == 0:
                                last = await self.bot.say("There are still {} messages. "
                                                          "Type `more` to continue."
                                                          "".format(len(managechannelsrolesresult) - i))
                                msg = await self.bot.wait_for_message(author=author,
                                                                      channel=channel,
                                                                      content="more",
                                                                      timeout=10)
                                if managechannelsrolesmsg is None:
                                    try:
                                        await self.bot.delete_message(last)
                                    except:
                                        pass
                                    finally:
                                        break
                            await self.bot.say(box(page))

                    if len(banserverroles) != 0:
                        banserverrolesmsg = "Roles with ban perms.\nPosition: ID > Name\n=============="
                        for r in banserverroles:
                            name = r.name
                            position = r.position
                            id = r.id
                            banserverrolesmsg += "\n- " + str(position) + ": " + id + " > " + name

                            banserverrolesresult = list(pagify(banserverrolesmsg, shorten_by=16))
                        for i, page in enumerate(banserverrolesresult):
                            if i != 0 and i % 4 == 0:
                                last = await self.bot.say("There are still {} messages. "
                                                          "Type `more` to continue."
                                                          "".format(len(banserverrolesresult) - i))
                                msg = await self.bot.wait_for_message(author=author,
                                                                      channel=channel,
                                                                      content="more",
                                                                      timeout=10)
                                if banserverrolesmsg is None:
                                    try:
                                        await self.bot.delete_message(last)
                                    except:
                                        pass
                                    finally:
                                        break
                            await self.bot.say(box(page))

                    if len(kickserverroles) != 0:
                        kickserverrolesmsg = "Roles with kick perms.\nPosition: ID > Name\n=============="
                        for r in kickserverroles:
                            name = r.name
                            position = r.position
                            id = r.id
                            kickserverrolesmsg += "\n- " + str(position) + ": " + id + " > " + name

                            kickserverrolesresult = list(pagify(kickserverrolesmsg, shorten_by=16))
                        for i, page in enumerate(kickserverrolesresult):
                            if i != 0 and i % 4 == 0:
                                last = await self.bot.say("There are still {} messages. "
                                                          "Type `more` to continue."
                                                          "".format(len(kickserverrolesresult) - i))
                                msg = await self.bot.wait_for_message(author=author,
                                                                      channel=channel,
                                                                      content="more",
                                                                      timeout=10)
                                if kickserverrolesmsg is None:
                                    try:
                                        await self.bot.delete_message(last)
                                    except:
                                        pass
                                    finally:
                                        break
                            await self.bot.say(box(page))

                    embedmsg = discord.Embed(colour=discord.Colour(0xFF0000),
                                             timestamp=datetime.datetime.today())
                    embedmsg.set_author(name="Stage 3 - Role Links",
                                        icon_url="http://i.imgur.com/T5L6Djq.png")
                    embedmsg.add_field(name="<:res1Rachet:332453473884962816> *Info*",
                                       value="Right, there are roles with no matching names, or roles that weren't matched because of their perms. Let me display them for you.",
                                       inline=False)
                    await self.bot.say(embed=embedmsg)

                    # Rolls this server has, but the subserver doesn't
                    await self._hostmissingroles_(hostnomatchroles, author, channel)

                    # Rolls the Subserver has, but this server doesn't
                    await self._submissingroles_(subnomatchroles, author, channel)

                await self._linklist_(linkedroles, server, subserver, author, channel)
                hostmatch = None
                submatch = None
                menu = 'done'

            elif response.content == 'no':
                linkedroles = defaultdict(lambda: linked_template.copy())
                linkcounter = 0
                hostnomatchroles = serverroles
                subnomatchroles = subserverroles
                hostnomatchroles.remove(server.default_role)
                subnomatchroles.remove(subserver.default_role)
                hostmatch = None
                submatch = None
                await self.bot.say("Pregenerated Linklist Purged")
                menu = 'done'

            else:
                await self.bot.say("Please enter a valid response.")

        selected = 'menu'
        while selected is 'menu':
            infomsg = "You have a few options here.\n\nRespond with `manual` to enter manual link mode(Manual links bypasses perm checks) You will be brought back here when you are done.\n\nRespond with `erole` to set a exemption role on the subserver for those you don't want kicked.\n\nRespond with `exit` to leave this stage and restart it later."
            embedmsg = discord.Embed(colour=discord.Colour(0xFF0000),
                                     timestamp=datetime.datetime.today())
            embedmsg.set_author(name="Stage 3 - Role Links",
                                icon_url="http://i.imgur.com/T5L6Djq.png")
            if linkedroles == defaultdict(lambda: linked_template.copy()):
                embedmsg.add_field(name="<:res1error:330424101661442050> *Warning*",
                                   value="```diff\n- There are no Linked roles!```",
                                   inline=False)
            else:
                infomsg += "\n\nRespond with `continue` to continue to the next stage."

            embedmsg.add_field(name="<:res1Rachet:332453473884962816> *Info*",
                               value=infomsg,
                               inline=False)
            await self.bot.say(embed=embedmsg)
            response = await self.bot.wait_for_message(timeout=timeout,
                                                          author=author,
                                                          channel=ctx.message.channel)
            if response is None:
                embedmsg = discord.Embed(colour=discord.Colour(0xFF0000),
                                         timestamp=datetime.datetime.today())
                embedmsg.set_author(name="Stage 3 - Role Links",
                                    icon_url="http://i.imgur.com/T5L6Djq.png")
                embedmsg.add_field(name="<:res1Rachet:332453473884962816> *Info*",
                                   value="Timed out. To resume, please run:\n```[prefix]mergeresume```",
                                   inline=False)
                await self.bot.say(embed=embedmsg)
                selected = 'timeout'

            elif response.content == 'manual':
                manualmode = 'on'
                while manualmode == 'on':
                    manualtype = 'none'
                    manualstage = 'off'
                    embedmsg = discord.Embed(colour=discord.Colour(0x0090f0),
                                             timestamp=datetime.datetime.today())
                    embedmsg.set_author(name="Stage 3 - Role Links",
                                        icon_url="http://i.imgur.com/T5L6Djq.png")
                    embedmsg.add_field(name=":cyclone: Manual Mode",
                                       value="Manual mode main menu.\n\nType `add` to add a link.\n\nType `del` to delete a link.\n\nType `links` to view the current links.\n\nType `exit` to return to the menu",
                                       inline=False)
                    await self.bot.say(embed=embedmsg)
                    response = await self.bot.wait_for_message(timeout=timeout,
                                                               author=author,
                                                               channel=ctx.message.channel)
                    if response is None:
                        await self.bot.say("Timed out, returning to the main menu.")
                        manualmode = 'off'
                        await asyncio.sleep(delay)
                        break

                    elif response.content == 'exit':
                        await self.bot.say("Returning to the menu.")
                        manualmode = 'off'
                        await asyncio.sleep(delay)

                    elif response.content == 'links':
                        await self._linklist_(linkedroles, server, subserver, author, channel)

                    elif response.content == 'add':
                        manualtype = 'add'
                        while manualtype == 'add':
                            manualstage = 'host'

                            while manualstage == 'host':
                                hostmatch = None
                                submatch = None
                                embedmsg = discord.Embed(colour=discord.Colour(0x0090f0),
                                                         timestamp=datetime.datetime.today())
                                embedmsg.set_author(name="Stage 3 - Role Links",
                                                    icon_url="http://i.imgur.com/T5L6Djq.png")
                                embedmsg.add_field(name=":cyclone: Hostserver role",
                                                   value="Enter the ID of the role on **Hostserver** you wish to link.\n\nType `links` to view the current links.\n\nType `unlinked` to view roles on this server that aren't in any links.\n\nType `roles` to view all of this servers roles.\n\nType `back` to return to the manual menu.",
                                                   inline=False)
                                await self.bot.say(embed=embedmsg)
                                response = await self.bot.wait_for_message(timeout=timeout,
                                                                                     author=author,
                                                                                     channel=ctx.message.channel)

                                if response is None:
                                    await self.bot.say("Timed out, retuning to manual menu")
                                    manualtype = 'none'
                                    manualstage = 'none'
                                    await asyncio.sleep(delay)
                                    break

                                elif response.content == 'back':
                                    manualtype = 'none'
                                    manualstage = 'none'
                                elif response.content == 'links':
                                    await self._linklist_(linkedroles, server, subserver, author, channel)
                                elif response.content == 'unlinked':
                                    await self._hostmissingroles_(hostnomatchroles, author, channel)
                                elif response.content == 'roles':
                                    await self._hostrolelist_(serverroles, author, channel)
                                else:
                                    hostmatch = discord.utils.get(server.role_hierarchy, id=response.content)
                                    if hostmatch is None:
                                        embedmsg = discord.Embed(colour=discord.Colour(0x0090f0),
                                                                 timestamp=datetime.datetime.today())
                                        embedmsg.set_author(name="Stage 3 - Role Links",
                                                            icon_url="http://i.imgur.com/T5L6Djq.png")
                                        embedmsg.add_field(name=":cyclone: Hostserver role",
                                                           value="Role not found",
                                                           inline=False)
                                        await self.bot.say(embed=embedmsg)
                                        await asyncio.sleep(delay)
                                    if hostmatch is not None:

                                        manualstage = 'sub'

                                        while manualstage == 'sub':
                                            embedmsg = discord.Embed(colour=discord.Colour(0x0090f0),
                                                                     timestamp=datetime.datetime.today())
                                            embedmsg.set_author(name="Stage 3 - Role Links",
                                                                icon_url="http://i.imgur.com/T5L6Djq.png")
                                            embedmsg.add_field(name=":cyclone: Subserver role",
                                                               value="Enter the ID of the role you wish to link from the **Subserver** role list.\n\nType `links` to view the current links.\n\nType `unlinked` to view roles on the subserver that aren't in any links..\n\nType `roles` to view all of the subservers roles.\n\nType `back` to reenter the host ID.",
                                                               inline=False)
                                            await self.bot.say(embed=embedmsg)

                                            response = await self.bot.wait_for_message(timeout=timeout,
                                                                                       author=author,
                                                                                       channel=ctx.message.channel)
                                            if response is None:
                                                await self.bot.say("Timed out, retuning to manual menu")
                                                manualtype = 'none'
                                                await asyncio.sleep(delay)
                                                break

                                            elif response.content == 'back':
                                                await self.bot.say("Going back.")
                                                manualstage = 'host'
                                                pass
                                            elif response.content == 'links':
                                                await self._linklist_(linkedroles, server, subserver, author, channel)
                                            elif response.content == 'unlinked':
                                                await self._submissingroles_(subnomatchroles, author, channel)
                                            elif response.content == 'roles':
                                                await self._subrolelist_(subserverroles, author, channel)
                                            else:
                                                submatch = discord.utils.get(subserver.role_hierarchy,
                                                                                 id=response.content)
                                                if submatch is None:
                                                    embedmsg = discord.Embed(colour=discord.Colour(0x0090f0),
                                                                             timestamp=datetime.datetime.today())
                                                    embedmsg.set_author(name="Stage 3 - Role Links",
                                                                        icon_url="http://i.imgur.com/T5L6Djq.png")
                                                    embedmsg.add_field(name=":cyclone: Subchannel role",
                                                                       value="Role not found",
                                                                       inline=False)
                                                    await self.bot.say(embed=embedmsg)
                                                    await asyncio.sleep(delay)
                                                    # await self.mass_purge(messagecleaner)
                                                if submatch is not None:
                                                    for r in linkedroles:
                                                        if linkedroles[r]["hostroleid"] == hostmatch.id and linkedroles[r]["subroleid"] == submatch.id:
                                                            hostmatch = discord.utils.get(server.role_hierarchy,
                                                                                          id=linkedroles[r][
                                                                                              "hostroleid"])
                                                            submatch = discord.utils.get(subserver.role_hierarchy,
                                                                                         id=linkedroles[r]["subroleid"])
                                                            linknum = r
                                                    if linknum != -1:
                                                        embedmsg = discord.Embed(colour=discord.Colour(0x0090f0),
                                                                                 timestamp=datetime.datetime.today())
                                                        embedmsg.set_author(name="Stage 3 - Role Links",
                                                                            icon_url="http://i.imgur.com/T5L6Djq.png")
                                                        embedmsg.add_field(name=":cyclone: Linknumber: " + str(linknum),
                                                                           value=hostmatch.name + " and " + submatch.name + " are already linked",
                                                                           inline=False)
                                                        await self.bot.say(embed=embedmsg)
                                                        hostmatch = None
                                                        submatch = None
                                                        linknum = -1
                                                        await asyncio.sleep(delay)
                                                    else:
                                                        embedmsg = discord.Embed(colour=discord.Colour(0x0090f0),
                                                                                 timestamp=datetime.datetime.today())
                                                        embedmsg.set_author(name="Stage 3 - Role Links",
                                                                            icon_url="http://i.imgur.com/T5L6Djq.png")
                                                        embedmsg.add_field(name=":cyclone: Creating Linknum:" + str(linkcounter),
                                                                           value="Linking:```diff\n" + hostmatch.name + "```\nTo:```diff\n" + submatch.name + "```",
                                                                           inline=False)
                                                        await self.bot.say(embed=embedmsg)
                                                        linkedroles[linkcounter]["hostroleid"] = hostmatch.id
                                                        linkedroles[linkcounter]["subroleid"] = submatch.id
                                                        linkcounter += 1
                                                        hostnomatchroles.remove(hostmatch)
                                                        subnomatchroles.remove(submatch)
                                                        hostmatch = None
                                                        submatch = None
                                                        manualstage = 'host'
                                                        await asyncio.sleep(delay)
                                                        #await self.mass_purge(messagecleaner)
                    elif response.content == 'del':
                        manualtype = 'del'
                        while manualtype == 'del':
                            hostmatch = None
                            submatch = None
                            present = 'no'
                            embedmsg = discord.Embed(colour=discord.Colour(0x0090f0),
                                                     timestamp=datetime.datetime.today())
                            embedmsg.set_author(name="Stage 3 - Role Links",
                                                icon_url="http://i.imgur.com/T5L6Djq.png")
                            embedmsg.add_field(name=":cyclone: Link Removal",
                                               value="Enter the Number of the Link you wish to delete.\n\nType `links` to view the current links.\n\nType `back` to return to the manual menu.",
                                               inline=False)
                            await self.bot.say(embed=embedmsg)
                            response = await self.bot.wait_for_message(timeout=timeout,
                                                                                 author=author,
                                                                                 channel=ctx.message.channel)

                            if response is None:
                                await self.bot.say("Timed out, retuning to the manual menu")
                                manualtype = 'none'
                                await asyncio.sleep(delay)

                            if response.content == 'back':
                                manualtype = 'none'
                            elif response.content == 'links':
                                await self._linklist_(linkedroles, server, subserver, author, channel)
                            else:
                                try:
                                    hostmatch = discord.utils.get(server.role_hierarchy,
                                                                  id=linkedroles[int(response.content)][
                                                                      "hostroleid"])
                                    submatch = discord.utils.get(subserver.role_hierarchy,
                                                                 id=linkedroles[int(response.content)]["subroleid"])
                                    linknum = int(response.content)
                                except:
                                    embedmsg = discord.Embed(colour=discord.Colour(0x0090f0),
                                                             timestamp=datetime.datetime.today())
                                    embedmsg.set_author(name="Stage 3 - Role Links",
                                                        icon_url="http://i.imgur.com/T5L6Djq.png")
                                    embedmsg.add_field(name=":cyclone: Link Error",
                                                       value="Link not found",
                                                       inline=False)
                                    await self.bot.say(embed=embedmsg)
                                    await asyncio.sleep(delay)
                                if hostmatch is not None and submatch is not None:

                                    embedmsg = discord.Embed(colour=discord.Colour(0x0090f0),
                                                             timestamp=datetime.datetime.today())
                                    embedmsg.set_author(name="Stage 3 - Role Links",
                                                        icon_url="http://i.imgur.com/T5L6Djq.png")
                                    embedmsg.add_field(name=":warning: Linknum: " + str(linknum),
                                                       value="You are about to unlink Host Role:```diff\n" + hostmatch.name + "```\nFrom Sub Role:```diff\n" + submatch.name + "```\n\nType `yes` to remove.\n\nType `no` to cancel.",
                                                       inline=False)
                                    await self.bot.say(embed=embedmsg)
                                    response = await self.bot.wait_for_message(timeout=timeout,
                                                                               author=author,
                                                                               channel=ctx.message.channel)
                                    if response is None:
                                        await self.bot.say("Timed out, retuning to manual menu")
                                        manualtype = 'none'
                                        await asyncio.sleep(delay)

                                    if response is not None:

                                        if response.content == 'no':
                                            await self.bot.say("Canceling.")
                                        elif response.content == 'yes':
                                            linkedroles.pop(linknum, None)
                                            hosttrip = False
                                            subttrip = False
                                            for r in linkedroles:
                                                if linkedroles[r]["hostroleid"] == hostmatch.id:
                                                    hosttrip = True
                                                if linkedroles[r]["subroleid"] == submatch.id:
                                                    subtrip = True
                                            if hosttrip is False:
                                                hostnomatchroles.append(hostmatch)
                                            if subttrip is False:
                                                subnomatchroles.append(submatch)
                                            hostrip = False
                                            subttrip = False
                                            embedmsg = discord.Embed(colour=discord.Colour(0x0090f0),
                                                                     timestamp=datetime.datetime.today())
                                            embedmsg.set_author(name="Stage 3 - Role Links",
                                                                icon_url="http://i.imgur.com/T5L6Djq.png")
                                            embedmsg.add_field(name=":cyclone: Link: " + str(linknum) + " removed.",
                                                               value="Removed",
                                                               inline=False)
                                            await self.bot.say(embed=embedmsg)
                                            hostmatch = None
                                            submatch = None
                                            linknum = -1
                                            await asyncio.sleep(delay)

            elif response.content == 'erole':
                erole = 'waiting'
                while erole == 'waiting':
                    embedmsg = discord.Embed(colour=discord.Colour(0x0090f0),
                                             timestamp=datetime.datetime.today())
                    embedmsg.set_author(name="Stage 3 - Role Links",
                                        icon_url="http://i.imgur.com/T5L6Djq.png")
                    embedmsg.add_field(name=":cyclone: *Exempt Role*",
                                       value="Please enter a role id for the **subserver**. This role will be used to exempt users with it from being kicked.",
                                       inline = False)
                    await self.bot.say(embed=embedmsg)
                    response = await self.bot.wait_for_message(timeout=timeout,
                    author = author,
                    channel = ctx.message.channel)

                    if response is None:
                        await self.bot.say("Timed out, returning to the main menu.")
                        await asyncio.sleep(delay)
                        erole = 'none'

                    else:
                        subexemptrole = discord.utils.get(subserver.roles, id=response.content)

                        if subexemptrole is None:
                            embedmsg.clear_fields()
                            embedmsg.add_field(name="<:res1error:330424101661442050> *Error*",
                                               value="diff\n- That role does not exist, please try again.```",
                                               inline=False)
                            await self.bot.say(embed=embedmsg)

                        if subexemptrole is not None:
                                self.mservers[server.id]["subexemptrole"] = subexemptrole.id
                                self.save()
                                embedmsg.clear_fields()
                                embedmsg.add_field(name=":cyclone: *Exempt Role Set!*",
                                                   value="The `{}` role in `{}` is now exempt from being kicked.".format(
                                                       subexemptrole.name, subserver.name),
                                                   inline=False)
                                await self.bot.say(embed=embedmsg)
                                await asyncio.sleep(delay)
                                erole = "done"


            elif response.content == 'exit':
                embedmsg = discord.Embed(colour=discord.Colour(0xFF0000),
                                         timestamp=datetime.datetime.today())
                embedmsg.set_author(name="Stage 3 - Role Links",
                                    icon_url="http://i.imgur.com/T5L6Djq.png")
                embedmsg.add_field(name="<:res1Rachet:332453473884962816> *Info*",
                                   value="Understood. To resume, please run:\n```[prefix]mergeresume```",
                                   inline=False)
                await self.bot.say(embed=embedmsg)
                selected = 'done'

            elif response.content == 'continue' and linkedroles != defaultdict(lambda: linked_template.copy()):
                embedmsg = discord.Embed(colour=discord.Colour(0x0090f0),
                                         timestamp=datetime.datetime.today())
                embedmsg.set_author(name="Stage 3 - Role Links",
                                    icon_url="http://i.imgur.com/T5L6Djq.png")
                embedmsg.set_thumbnail(url="https://i.imgur.com/zNU3Y9m.png")
                embedmsg.add_field(name="<:res1Rachet:332453473884962816> *Info*",
                                   value="You are about to shift to stage 4.\n```diff\n- Currently there is no way to edit these links after a server merge has started. You will need to stop the current merge and start from scratch. are you sure you're ready to proceed?```\nReact with HellYeah below to continue.\n\nReact with HellNa to return to the main menue.",
                                   inline=False)
                if self.mservers[server.id]["subexemptrole"] is None:
                    embedmsg.add_field(name="<:res1error:330424101661442050> *Warning: No erole!*",
                                      value="```diff\n- No exemption role has been set, I will kick everyone I can once they are processed! If I can't kick them, the merge will be paused (safety feature).```",
                                      inline=False)
                message = await self.bot.say(embed=embedmsg)
                await self.bot.add_reaction(message, str(emoji_out['hellna']))
                await self.bot.add_reaction(message, str(emoji_out['hellyeah']))
                r = await self.bot.wait_for_reaction(
                    message=message,
                    user=ctx.message.author,
                    timeout=timeout)
                if r is None:
                    try:
                        try:
                            await self.bot.clear_reactions(message)
                        except:
                            await self.bot.remove_reaction(message, "res1hellna:330424101908905990", self.bot.user)
                            await self.bot.remove_reaction(message, "res1hellyeah:330424103259340800", self.bot.user)
                        await self.bot.say("Timed out, returning to the main menu.")
                    except:
                        pass
                    return None
                reacts = {v: k for k, v in emoji_in.items()}
                try:
                    react = reacts[str(r.reaction.emoji)]
                except:
                    await self.bot.say(
                        "Baka, you added a different or selected a different reaction! Back to the main menu you go!")
                if react == "hellna":
                    message = await self.bot.say("Returning to the main menu.")

                elif react == "hellyeah":
                    self.mservers[server.id]["linkedroles"] = linkedroles
                    self.mservers[server.id]["stage"] = "stage4"
                    self.mservers[server.id]["status"] = "Setting up server dm."
                    self.save()
                    return
                else:
                    try:
                        await self.bot.say("Oh god, something really broke...")
                    except:
                        pass
            else:
                await self.bot.say("Please select a valid option")
                await asyncio.sleep(delay)

    async def _stage4_(self, ctx, delay: int = 1, timeout: int = 60):

        author = ctx.message.author
        server = ctx.message.server
        subserverid = self.mservers[server.id].get("subserverid")
        subserver = discord.utils.get(self.bot.servers, id=subserverid)

        #Embed core


        #Timeput message
        toutmsg = discord.Embed(colour=discord.Colour(0xFF0000))
        toutmsg.set_author(name="Stage 4 - Dm Invite",
                            icon_url="http://i.imgur.com/T5L6Djq.png")
        toutmsg.add_field(name="<:res1Rachet:332453473884962816> *Info*",
                           value="Timed out. To resume, please run:\n```[prefix]mergeresume```",
                           inline=False)

        dmstate= 'waiting'

        while dmstate == 'waiting':
            embedmsg = discord.Embed(colour=discord.Colour(0xFF0000),
                                     timestamp=datetime.datetime.today())
            embedmsg.set_author(name="Stage 4 - Dm Ivite",
                                icon_url="http://i.imgur.com/T5L6Djq.png")
            embedmsg.add_field(name="<:res1Rachet:332453473884962816> *Info*",
                               value="Please enter the message you wish to have dm'd to the users. This will be in an embed field, and will support normal message formatting.\nYou'll get to see the exact message that'll be dm'd when the merge is run when we are ready.\nYou'll have 5 mins before I timeout here.",
                               inline=False)
            await self.bot.say(embed=embedmsg)
            response = await self.bot.wait_for_message(timeout=300,
                                                       author=author,
                                                       channel=ctx.message.channel)

            if response is None:
                await self.bot.say(embed=toutmsg)
                await asyncio.sleep(delay)
                return
            else:
                invitemsg = response

            try:
                invite = await self.bot.create_invite(server.default_channel)
            except discord.Forbidden:
                embedmsg.clear_fields()
                embedmsg.add_field(name="<:res1error:330424101661442050> *Warning*",
                                   value="```diff\n- I'm not allowed to make an invite for {}\n Please give the Administrator perm to my role to continue. This will eliminate any permission issues.```".format(server.name),
                                   inline=False)
                await self.bot.say(embed=embedmsg)
                return

            subserverinvite = 'waiting'
            while subserverinvite == 'waiting':
                embedmsg.clear_fields()
                embedmsg.add_field(name="<:res1error:330424101661442050> *Warning*",
                                   value="Please enter a channel id for the **subserver** for me to post the dm message to, incase DM's are blocked. I will individually. This channel wil also be used for certain required notifications, such as when the subserver is locked down.",
                                   inline=False)
                await self.bot.say(embed=embedmsg)
                response = await self.bot.wait_for_message(timeout=timeout,
                                                                     author=author,
                                                                     channel=ctx.message.channel)
                if response is None:
                    await self.bot.say(embed=toutmsg)
                    await asyncio.sleep(delay)
                    return
                else:
                    subserverinvchannel = discord.utils.get(subserver.channels, id=response.content)
                    if subserverinvchannel is None:
                        embedmsg.clear_fields()
                        embedmsg.add_field(name="<:res1error:330424101661442050> *Error*",
                                           value="diff\n- That channel does not exist, please try again.```",
                                           inline=False)
                        await self.bot.say(embed=embedmsg)

                    if subserverinvchannel is not None:
                        if subserverinvchannel.permissions_for(server.me).send_messages == False:
                            embedmsg.clear_fields()
                            embedmsg.add_field(name="<:res1error:330424101661442050> *Warning*",
                                               value="```diff\n- I'm not allowed to send messages in {}\n Please give the Administrator perm to my role to continue. This will eliminate any permission issues.```".format(subserverinvchannel.name),
                                               inline=False)
                            await self.bot.say(embed=embedmsg)
                        else:
                            self.mservers[server.id]["subserverinvchannel"] = subserverinvchannel.id
                            self.save()
                            embedmsg.clear_fields()
                            embedmsg.add_field(name="<:res1Rachet:332453473884962816> *Info*",
                                               value="The channel `{}` in `{}` is now set as the server location to post the DM messages for the those I can't dm. This will only be done once, unless the servermerge invite code has to be regenerated.".format(subserverinvchannel.name, subserver.name),
                                               inline=False)
                            await self.bot.say(embed=embedmsg)
                            subserverinvite = "done"


            embedmsg.clear_fields()
            embedmsg.add_field(name="<:res1Rachet:332453473884962816> *Info*",
                               value="The message below will be what I'll dm to the users.",
                               inline=False)
            await self.bot.say(embed=embedmsg)

            dmmsg = discord.Embed(colour=discord.Colour(0x3fff00),
                                     timestamp=datetime.datetime.today())
            dmmsg.set_author(name="Server merge of \"{}\" into \"{}\"".format(subserver.name, server.name),
                                icon_url="http://i.imgur.com/T5L6Djq.png")
            dmmsg.set_thumbnail(url=subserver.icon_url)
            dmmsg.add_field(name=":incoming_envelope: *Message from the server owner, {}:*".format(author.name),
                               value=invitemsg.content,
                               inline=False)
            dmmsg.add_field(name="<:res1MomijiSmile:330424102806355968> *Invite link to {}.*".format(server.name),
                              value=invite,
                              inline=False)
            dmmsg.add_field(name="<:res1Rachet:332453473884962816> *Info*",
                            value="When you join the \"{}\", any roles that {} has linked to ones in \"{}\" will be automatically given to you. Your new roles will be listed in a dm I'll send you after I assign them. If you are already in the server, please wait and I'll apply your roles soon.\n\nWhile the server merge is running, new messages and invite creation will not be possible in \"{}\", and once your roles have been applied you'll be removed from \"{}\".".format(server.name, author.name, subserver.name, subserver.name, subserver.name),
                            inline=False)
            await self.bot.say(embed=dmmsg)

            embedmsg.clear_fields()
            embedmsg.add_field(name="<:res1Rachet:332453473884962816> *Info*",
                               value="Is this suitable?\n\nType `yes` to continue.\n\nType `no` to redo this.",
                               inline=False)
            await self.bot.say(embed=embedmsg)

            check = 'checking'
            while check == 'checking':
                response = await self.bot.wait_for_message(timeout=timeout,
                                                           author=author,
                                                           channel=ctx.message.channel)

                if response is None:
                    await self.bot.say(embed=toutmsg)
                    await asyncio.sleep(delay)
                    return
                elif response.content == 'yes':
                    self.mservers[server.id]["invitecode"] = invite.url
                    self.mservers[server.id]["invitemsg"] = invitemsg.content
                    self.mservers[server.id]["stage"] = "stage5"
                    self.mservers[server.id]["status"] = "Final setup."
                    self.save()
                    return
                elif response.content == 'no':
                    await self.bot.say("Understood, restarting stage 4")
                    await self.bot.delete_invite(invite)
                    check = 'escape'
                else:
                    await self.bot.say("Please select a valid option")

    async def _stage5_(self, ctx, delay: int = 1, timeout: int = 60):

        author = ctx.message.author
        server = ctx.message.server
        subserverid = self.mservers[server.id].get("subserverid")
        subserver = discord.utils.get(self.bot.servers, id=subserverid)
        check = 'checking'
        stage5p = self.mservers[server.id].get("stage5p")
        statuschannel = discord.utils.get(server.channels, id=self.mservers[server.id].get("statuschannel"))
        initialmsg = None
        errormsg = None

        #Timeput message
        toutmsg = discord.Embed(colour=discord.Colour(0xFF0000))
        toutmsg.set_author(name="Stage 5 - Final Setup",
                            icon_url="http://i.imgur.com/T5L6Djq.png")
        toutmsg.add_field(name="<:res1Rachet:332453473884962816> *Info*",
                           value="Timed out. To resume, please run:\n```[prefix]mergeresume```",
                           inline=False)

        #Stage 5 Embed header
        embedmsg = discord.Embed(colour=discord.Colour(0xFF0000))
        embedmsg.set_author(name="Stage 5 - Final Setup",
                            icon_url="http://i.imgur.com/T5L6Djq.png")

        if stage5p is not None and statuschannel is None:
            embedmsg.clear_fields()
            embedmsg.add_field(name="<:res1error:330424101661442050> *Warning*",
                               value="```diff\n- Server merge channel is gone, restarting Stage 5.```".format(
                                   server.name),
                               inline=False)
            initialmsg = await self.bot.say(embed=embedmsg)
            self.mservers[server.id]["statuschannel"] = None
            self.mservers[server.id]["stage5p"] = None
            self.mservers[server.id]["users"] = {}
            self.save()
            stage5p = self.mservers[server.id].get("stage5p")

        if stage5p is None:
            embedmsg.add_field(name="<:res1Rachet:332453473884962816> *Info*",
                               value="I'm now going to do the following. ```\n1: Create a channel to monitor progress on this server. This channel will be shifted to the top of the server list. I'll deny {} the Read Messages perm.\n2: The ability to create invites and send messages will be removed from roles (This is done by denying the {} create invites and send messages perms. This will not catch other channel overrides or stop anyone with admin perms)\n3: All invite links for \"{}\" will be deleted.\n4: I'll send the Servermerge dm to every user.\n5: I'll look for users already in this server. If I find them, I'll give them their linked roles and remove them from the subserver.\nAfter that is all done the servermerge will be switched to active mode, giving roles and removing users from the subserver until the merge is stopped via the stop command.```\n\nType `yes` to continue.\n\nType `no` stop for now.".format(subserver.default_role.name, subserver.default_role.name, subserver.name),
                               inline=False)
            if initialmsg is not None:
                await self.bot.edit_message(initialmsg, embed=embedmsg)
            else:
                await self.bot.say(embed=embedmsg)

            while check == 'checking':
                response = await self.bot.wait_for_message(timeout=timeout,
                                                           author=author,
                                                           channel=ctx.message.channel)

                if response is None:
                    await self.bot.say(embed=toutmsg)
                    await asyncio.sleep(delay)
                    return
                elif response.content == 'yes':
                    check = 'passed'
                elif response.content == 'no':
                    embedmsg.clear_fields()
                    embedmsg.add_field(name="<:res1Rachet:332453473884962816> *Info*",
                                       value="Understood. To resume, please run:\n```[prefix]mergeresume```",
                                       inline=False)
                    await self.bot.say(embed=embedmsg)
                    return
                else:
                    await self.bot.say("Please select a valid option")
        else:
            embedmsg.clear_fields()
            embedmsg.add_field(name="<:res1Rachet:332453473884962816> *Info*",
                               value="Previous run detected, resuming",
                               inline=False)
            status = await self.bot.send_message(destination=statuschannel, content=ctx.message.author.mention, embed=embedmsg)
            check = 'passed'

        if check == 'passed':

            if stage5p is None:
                await self._stage5p1_(ctx)
                server = ctx.message.server
                statuschannel = discord.utils.get(server.channels, id=self.mservers[server.id].get("statuschannel"))
                stage5p = self.mservers[server.id].get("stage5p")

            if statuschannel is not None:
                embedmsg.clear_fields()
                embedmsg.add_field(name="<:res1issue_open:330419505589256192> *Status Channel*",
                                   value="Created/Present")
                status = await self.bot.send_message(destination=statuschannel, content=ctx.message.author.mention,
                                                     embed=embedmsg)
            await asyncio.sleep(2)

            #Process channel lockdown
            if stage5p == 'sublockdown':
                await self._stage5p2_(ctx, statuschannel)
                stage5p = self.mservers[server.id].get("stage5p")
                if stage5p == 'sublockdown':
                    return

            embedmsg.add_field(name="<:res1issue_open:330419505589256192> *Subserver Locked Down*",
                                    value="Messages cannot be sent and invites can not be made.")
            await self.bot.delete_message(status)
            status = await self.bot.send_message(destination=statuschannel, content=ctx.message.author.mention,
                                                 embed=embedmsg)
            await asyncio.sleep(2)


            #Merge dm sent out. First member list saved, join watch started.
            if stage5p == 'dmprocess':
                await self._stage5p3_(ctx, statuschannel)
                stage5p = self.mservers[server.id].get("stage5p")
                if stage5p == 'dmprocess':
                    return

            embedmsg.add_field(name="<:res1issue_open:330419505589256192> *Direct Messages Sent*")
            await self.bot.delete_message(status)
            await self.bot.send_message(destination=statuschannel, content=ctx.message.author.mention,
                                                     embed=embedmsg)
            await asyncio.sleep(2)

            #Process member in bot servers.
            if stage5p == 'mprocess':
                await self._stage5p4_(ctx, statuschannel)
                stage5p = self.mservers[server.id].get("stage5p")
                if stage5p == 'mprocess':
                    return



    async def _stage5p1_(self, ctx, delay: int = 1, timeout: int = 60):
        #channel creation
        server = ctx.message.server
        embedmsg = discord.Embed(colour=discord.Colour(0xFF0000))
        embedmsg.set_author(name="Stage 5 - Final Setup",
                            icon_url="http://i.imgur.com/T5L6Djq.png")

        everyone = discord.PermissionOverwrite(read_messages=False)
        mine = discord.PermissionOverwrite(read_messages=True)
        try:
            statuschannel = await self.bot.create_channel(server, 'servermerge', (server.default_role, everyone),
                                                          (server.me, mine))
            await asyncio.sleep(5)
            await self.bot.move_channel(statuschannel, 0)
            self.mservers[server.id]["statuschannel"] = statuschannel.id
            self.mservers[server.id]["stage5p"] = "sublockdown"
            self.save()
            return
        except discord.Forbidden:
            embedmsg.clear_fields()
            embedmsg.add_field(name="<:res1error:330424101661442050> *Warning*",
                               value="```diff\n- I'm not allowed to make a channel"
                                     " in \"{}\"\n Please give the Administrator perm to my role to continue. This will eliminate any permission issues.```".format(
                                   server.name),
                               inline=False)
            await self.bot.say(embed=embedmsg)
            return

    async def _stage5p2_(self, ctx, statuschannel, delay: int = 1, timeout: int = 60):
        #Subserver lockdown, all overrides are saved just in case.
        server = ctx.message.server
        subserverid = self.mservers[server.id].get("subserverid")
        subserver = discord.utils.get(self.bot.servers, id=subserverid)
        subserverinvchannel = discord.utils.get(subserver.channels, id=self.mservers[server.id].get("subserverinvchannel"))


        embedmsg = discord.Embed(colour=discord.Colour(0xFF0000))
        embedmsg.set_author(name="Stage 5 - Final Setup",
                            icon_url="http://i.imgur.com/T5L6Djq.png")
        errormsg = embedmsg
        embedmsg.add_field(name=":cyclone: *Subserver Lockdown*",
                           value="In Progress")
        status = await self.bot.send_message(destination=statuschannel,
                                             embed=embedmsg)

        if subserverinvchannel.permissions_for(subserver.me).mention_everyone is False:
            errormsg.add_field(name="<:res1error:330424101661442050> *Warning*",
                               value="```diff\n- I'm not allowed to mention the `{}` role.\n Please give the Administrator perm to my role to continue. This will eliminate any permission issues. Aborting```".format(subserver.default_role),
                               inline=False)
            await self.bot.send_message(destination=statuschannel, content=ctx.message.author.mention,
                                        embed=errormsg)
            return

        #Save the channel overrides in the subserver
        error, c = await self._savesubserverchanneloverrides_(server)

        #Check if there was an issue saving all the overrides
        if error == "forbidden":
            errormsg.add_field(name="<:res1error:330424101661442050> *Warning*",
                               value="```diff\n- I'm not allowed to see the channel overrides for {}\n Please give the Administrator perm to my role to continue. This will eliminate any permission issues. Aborting```".format(c.name),
                               inline=False)
            await self.bot.send_message(destination=statuschannel, content=ctx.message.author.mention,
                                        embed=errormsg)
            return

        #Lockdown the subserver
        error, fchannels = await self._subserverlockdown_(server)

        # Check if there was an issue saving all the overrides
        if error == "forbidden":
            msg = "Channels I couldn't edit:\n\n"
            for c in fchannels:
                msg += "- \"{}\" ({})| Failed to change overrides.\n".format(c.name, c.id)
                # pagify messages in case over 2k chars
            result = list(pagify(msg, shorten_by=16))
            errormsg.add_field(name="<:res1error:330424101661442050> *Warning*",
                                   value="```diff\n- I was unable to edit the channel overrides for the following channels.\n Please give the Administrator perm to my role and shift it to the top of the role list to continue. This will eliminate any permission issues. Continuing.```\n\nPlease note, I'll continue to change all I can. To try to lock all of the channels after changing the perms, you may try running `[prefix]retrysublockdown`.".format(c.name),
                                   inline=False)
            await self.bot.send_message(destination=statuschannel, content=ctx.message.author.mention,
                                            embed=errormsg)
            for i, page in enumerate(result):
                await self.bot.send_message(destination=statuschannel, content=box(page, lang="diff"))
            self.mservers[server.id]["subserverlockdown"] = "partial"
        else:
            self.mservers[server.id]["subserverlockdown"] = "full"
        self.save()

        embedmsg.set_field_at(index=0,
                              name="<:res1issue_open:330419505589256192> *Subserver Lockdown*",
                              value="Subserver has been locked down.")
        embedmsg.add_field(name="<:res1Rachet:332453473884962816> *Info*",
                           value="I set channel overrides send_messages perm( or speak if it's a voice channel) to deny for all channels I can. Only the server owner or someone with the Administrator perm may ignore these changes. Please stand by for more info.",
                           inline=False)
        #Notify Status channel
        await self.bot.delete_message(status)
        await self.bot.send_message(destination=statuschannel, embed=embedmsg)
        #Notify subserver of lockdown
        await self.bot.send_message(destination=subserverinvchannel, content=subserver.default_role.mention, embed=embedmsg)
        await asyncio.sleep(3)
        self.mservers[server.id]["stage5p"] = "dmprocess"
        self.save()
        return

    async def _stage5p3_(self, ctx, statuschannel, delay: int = 1, timeout: int = 60):
        #Sends dms to everyone, and tags them in the subserverinvchannel if the dm can't be sent.

        server = ctx.message.server
        subserverid = self.mservers[server.id].get("subserverid")
        subserver = discord.utils.get(self.bot.servers, id=subserverid)
        subserverinvchannel = discord.utils.get(subserver.channels,
                                                id=self.mservers[server.id].get("subserverinvchannel"))
        subexemptrole = discord.utils.get(subserver.roles,
                                                id=self.mservers[server.id].get("subexemptrole"))
        submembers = [m for m in subserver.members]
        fdmmembers = []
        invitemsg = self.mservers[server.id].get("invitemsg")
        invitecode = self.mservers[server.id].get("invitecode")
        hinvites = await self.bot.invites_from(server)
        invite = None

        #Error Embed
        critmsg = discord.Embed(colour=discord.Colour(0xFF0000),
                                timestamp=datetime.datetime.today())
        critmsg.set_author(name="Stage 5 - Final Setup",
                           icon_url="http://i.imgur.com/T5L6Djq.png")
        critmsg.set_thumbnail(url="https://i.imgur.com/zNU3Y9m.png")
        critmsg.add_field(name="<:res1error:330424101661442050> *Critical error encountered, halting merge*",
                          value="Stage 5 is halted. To resume stage 5 once the problem has been corrected, please run:\n```[prefix]mergeresume```",
                          inline=False)

        # Status Embed
        embedmsg = discord.Embed(colour=discord.Colour(0xFF0000))
        embedmsg.set_author(name="Stage 5 - Dm Progress",
                            icon_url="http://i.imgur.com/T5L6Djq.png")

        # Check for a valid saved invite, create one if not found. Throws crit error and halts on fail.
        for i in hinvites:
            if i.code == invitecode:
                invite = i
                embedmsg.add_field(
                    name=":incoming_envelope: *Invite Found*".format(server.owner.name),
                    value=invite.code,
                    inline=False)
                dmstatus = await self.bot.send_message(destination=statuschannel,
                                                       embed=embedmsg)
        if invite is None:
            try:
                invite = await self.bot.create_invite(server.default_channel, max_age=0)
                self.mservers[server.id]["invitecode"] = invite.code
                self.save()
                embedmsg.add_field(
                    name=":incoming_envelope: *Invite Recreated*".format(server.owner.name),
                    value=invite.code,
                    inline=False)
                dmstatus = await self.bot.send_message(destination=statuschannel,
                                                       embed=embedmsg)
            except discord.Forbidden:
                critmsg.add_field(name="<:res1error:330424101661442050> *Warning*",
                                  value="```diff\n- I'm not allowed to make an invite for {}\n Please give the Administrator perm to my role to continue. This will eliminate any permission issues.```".format(
                                      server.name),
                                  inline=False)
                await self.bot.send_message(destination=statuschannel,
                                            embed=critmsg)
                return

        # DM Embed
        dmmsg = discord.Embed(colour=discord.Colour(0x7f08e0))
        dmmsg.set_author(name="Server merge of \"{}\" into \"{}\"".format(subserver.name, server.name),
                         icon_url="http://i.imgur.com/T5L6Djq.png")
        dmmsg.set_thumbnail(url=subserver.icon_url)
        dmmsg.add_field(name=":incoming_envelope: *Message from the server owner, {}:*".format(server.owner.name),
                        value=invitemsg,
                        inline=False)
        dmmsg.add_field(name="<:res1MomijiSmile:330424102806355968> *Invite link to {}.*".format(server.name),
                        value=invite.url,
                        inline=False)
        dmmsg.add_field(name="<:res1Rachet:332453473884962816> *Info*",
                        value="When you join the \"{}\", any roles that {} has linked to ones in \"{}\" will be automatically given to you. Your new roles will be listed in a dm I'll send you after I assign them(I'll still add them even if I can't dm you). If you are already in the server, please wait and I'll apply your roles soon.\n\nWhile the server merge is running, new messages and invite creation will not be possible in \"{}\", and once you've been moved you'll be removed from \"{}\"(Kicked). Thank you for your patience".format(
                            server.name, server.owner.name, subserver.name, subserver.name, subserver.name),
                        inline=False)

        #Send dms to users, while creating a list of those I can't dm.
        embedmsg.add_field(name=":cyclone: *Processing member dm's.*",
                           value="0 out of " + str(len(submembers)) + " messages attempted.")
        dmstatus = await self.bot.edit_message(dmstatus,
                                               embed=embedmsg)
        for i, m in enumerate(submembers):
            memberlist = defaultdict(lambda: member_info_template.copy(), self.mservers[server.id]["members"])
            if i != 0 and i % 25 == 0:
                embedmsg.set_field_at(1, name=":cyclone: *Processing member dm's.*",
                                      value=str(i) + " out of " + str(len(submembers)) + " messages attempted.")
                dmstatus = await self.bot.edit_message(dmstatus,
                                                       embed=embedmsg)

            if memberlist[m.id]["inv"] is None and memberlist[m.id]["dm"] != "forbidden":
                if self.isexempt(m, subexemptrole):
                    dmmsg.add_field(name="<:res1issue_open:330419505589256192> *Exempt Role Found*",
                                       value="You are exempt from being kicked from the server as long as you have the role.")
                try:
                    await self.bot.send_message(destination=m, embed=dmmsg)
                    memberlist[m.id]["lastdm"] = "Invite Msg"
                    memberlist[m.id]["lastdm"] = "sent"
                    memberlist[m.id]["inv"] = "dm"
                except discord.Forbidden:
                    memberlist[m.id]["dm"] = "forbidden"
                except discord.HTTPException:
                    memberlist[m.id]["dm"] = "HTTPException"
                except discord.NotFound:
                    memberlist[m.id]["dm"] = "Destination not found."
                if self.isexempt(m, subexemptrole):
                    dmmsg.remove_field(3)
            self.mservers[server.id]["members"][m.id] = memberlist[m.id]
            self.save()

        #Update the dmstat processing field for the last time.
        embedmsg.set_field_at(1,
                              name="<:res1issue_open:330419505589256192> *Member dm's Processed.*",
                              value=str(i) + " out of " + str(len(submembers)) + " messages attempted.")

        #Genterate list of users who I was unable to contact
        membersave = self.mservers[server.id].get("members")
        for m in membersave:
            if membersave[m].get("dm") == "forbidden":
                fdmmembers.append(discord.utils.get(subserver.members, id=m))

        if len(fdmmembers) != 0:
            embedmsg.add_field(name=":anger: *Forbidden DM's detected.*",
                               value=str(len(fdmmembers)) + " messages were forbidden. I'll mention each user in the invite in the subsver before posting the dm there.")
            dmstatus = await self.bot.edit_message(dmstatus,
                                                   embed=embedmsg)

            #Sends messages with mention lists in the sub invite channel for those I can't dm, with the dmmsg posted after.
            invchlmsg = ":anger: *Failed Dm's**\n```diff\n- There were users I couldn't reach. I'll now mention them all, and post the DM Message here afterwards!```\n\n"
            for m in fdmmembers:
                memberlist = defaultdict(lambda: member_info_template.copy(), self.mservers[server.id]["members"])
                invchlmsg += "{}, I failed to dm you, please stand by for the dm message after the mentions are complete. Please note, I'll be unable to dm you the roles when they are given.\n".format(m.mention)

            result = list(pagify(invchlmsg, escape = False, shorten_by=16))

            for i, page in enumerate(result):
                if i != 0 and i % 4 == 0:
                    await asyncio.sleep(int=1)
                    await self.bot.send_message(destination=subserverinvchannel, content=page)

        #Posts the DM in the invitechannel
        await self.bot.send_message(destination=subserverinvchannel, content = subserver.default_role.mention, embed=dmmsg)

        #Marks failed dm's as mention now.
        for m in fdmmembers:
            memberlist = defaultdict(lambda: member_info_template.copy(), self.mservers[server.id]["members"])
            memberlist[m.id]["inv"] = "mention"
            self.mserver[server.id]["members"][m.id] = memberlist[m.id]
            self.save


        embedmsg.add_field(name="<:res1issue_open:330419505589256192> Dm Segment Complete*",
                           value="Toggling join watch. New members will be given their roles upon going.")
        await self.bot.edit_message(dmstatus,
                                               embed=embedmsg)

        #Now the DMs have been sent, we'll toggle the joining watch on. After a last save we are done here.
        self.mservers[server.id]["running"] = True
        self.mservers[server.id]["stage5p"] = "mprocess"
        self.save()
        return


    async def _stage5p4_(self, ctx, statuschannel, delay: int = 1, timeout: int = 60):
        #Process members already in both servers.
        server = ctx.message.server
        subserverid = self.mservers[server.id].get("subserverid")
        subserver = discord.utils.get(self.bot.servers, id=subserverid)
        hostmembers = [m for m in server.members]
        smembers = []

        #Error Embed
        critmsg = discord.Embed(colour=discord.Colour(0xFF0000),
                                 timestamp=datetime.datetime.today())
        critmsg.set_author(name="Stage 5 - Final Setup",
                            icon_url="http://i.imgur.com/T5L6Djq.png")
        critmsg.set_thumbnail(url="https://i.imgur.com/zNU3Y9m.png")
        critmsg.add_field(name="<:res1error:330424101661442050> *Critical error encountered, merge was halted.*",
                           value="Stage 5 is halted. To resume stage 5 once the problem has been corrected, please run:\n```[prefix]mergeresume```",
                           inline=False)

        #State Embed
        embedmsg = discord.Embed(colour=discord.Colour(0xFF0000))
        embedmsg.set_author(name="Stage 5 - Final Setup",
                            icon_url="http://i.imgur.com/T5L6Djq.png")
        embedmsg.add_field(name=":cyclone: *Processing members of both servers.*",
                           value="In Progress")


        #Send initial status massage and track it.
        status = await self.bot.send_message(destination=statuschannel,
                                             embed=embedmsg)

        #Create a list of members currently in both servers.
        for m in hostmembers:
            if subserver.get_member(m.id) is not None:
                smembers.append(m)

        #Update Status embed
        embedmsg.set_field_at(0, name=":restroom: *Current number of shared users.*",
                           value=str(len(smembers)))
        embedmsg.add_field(name=":link: *Applying linked Roles*",
                           value="0 out of " + str(len(smembers)) + " processed.")
        status = await self.bot.edit_message(status,
                                             embed=embedmsg)

        #Process each shared member
        for i, m in enumerate(smembers):
            if i != 0 and i % 10 == 0:
                embedmsg.set_field_at(2, name=":link: *Applying linked Roles*", value=str(i) + " out of " + str(len(smembers)) + " processed.")
                await self.bot.delete_message(status)
                status = await self.bot.send_message(destination=statuschannel,
                                                     embed=embedmsg)

            error = await self._memberprocessor_(m)

            if error is 'critical':
                await self.bot.send_message(destination=statuschannel,
                                            embed=critmsg)
                return

        #Final message
        embedmsg.set_field_at(2, name=":link: *Applying linked Roles*", value=str(len(smembers)) + " out of " + str(len(smembers)) + " processed.")
        await self.bot.delete_message(status)
        await self.bot.send_message(destination=statuschannel,
                                             embed=embedmsg)
        embedmsg.clear_fields()
        embedmsg.set_thumbnail(url="https://i.imgur.com/9B8LMZV.png")
        embedmsg.add_field(name=":white_check_mark:  *All set up*",
                           value="The shared members between the servers has now been processed! You can sit back and relax now, I'll process everyone who joins from the subserver until told otherwise!\n\nRun `[prefix]mergehalt` to stop me! \n\nIf someone is silly and deletes the invite code I made, run `[prefix]regeninvite` and I'll post it in the channel you designated for the subserver. I will **not** dm members with the new invite.")

        #Finnish up
        self.mservers[server.id]["stage5p"] = "complete"
        self.save()

    async def _linklist_(self, linkedroles, server, subserver, author, channel):
        # Shows the current link list.
        linkedroles = OrderedDict(sorted(linkedroles.items(), key=lambda p: p[0]))
        embedmsg = discord.Embed(colour=discord.Colour(0xFF0000),
                                 timestamp=datetime.datetime.today())
        embedmsg.set_author(name="Stage 3 - Role Links",
                            icon_url="http://i.imgur.com/T5L6Djq.png")
        embedmsg.add_field(name="<:res1Rachet:332453473884962816> *Info*",
                           value="This is the current list of role links, it may take a moment to generate:",
                           inline=False)
        await self.bot.say(embed=embedmsg)
        currentlinkssmsg = "LinkList\nLink num: num\nHostrole Name(Position: <ID>)\nSubrole Name(Position: <ID>)\n=============="
        for r in linkedroles:
            hostrolelink = discord.utils.get(server.role_hierarchy,
                                             id=linkedroles[r]['hostroleid'])
            subrolelink = discord.utils.get(subserver.role_hierarchy, id=linkedroles[r]['subroleid'])
            currentlinkssmsg += "\nLink: " + str(
                r) + ": \nHost Role: " + hostrolelink.name + "(" + str(
                hostrolelink.position) + ": <" + hostrolelink.id + ">)" + "\nSub Role: " + subrolelink.name + "(" + str(subrolelink.position) + ": <" + subrolelink.id + ">)"

            currentlinkssresult = list(pagify(currentlinkssmsg, shorten_by=16))
        for i, page in enumerate(currentlinkssresult):
            if i != 0 and i % 4 == 0:
                last = await self.bot.say("There are still {} messages. "
                                          "Type `more` to continue."
                                          "".format(len(currentlinkssresult) - i))
                msg = await self.bot.wait_for_message(author=author,
                                                      channel=channel,
                                                      content="more",
                                                      timeout=10)
                if msg is None:
                    try:
                        await self.bot.say("No response, skipping")
                    except:
                        pass
                    finally:
                        break
            await self.bot.say(box(page, lang="py"))

    async def _hostmissingroles_(self, hostnomatchroles, author, channel):
        # Creates a list of roles on the hostserver that haven't got a link to any roles on the subserver.
        msg = "Rolls this server has, that not linked to any subserver roles.\nPosition: <ID> Name\n=============="
        sorted(hostnomatchroles, key=self.getKeyRolePosition)
        for r in hostnomatchroles:
            name = r.name
            position = r.position
            id = r.id
            msg += "\n " + str(position) + ": <" + id + "> " + name

        result = list(pagify(msg, shorten_by=16))

        for i, page in enumerate(result):
            if i != 0 and i % 4 == 0:
                last = await self.bot.say("There are still {} messages. "
                                          "Type `more` to continue."
                                          "".format(len(result) - i))
                msg = await self.bot.wait_for_message(author=author,
                                                      channel=channel,
                                                      content="more",
                                                      timeout=10)
                if msg is None:
                    try:
                        await self.bot.delete_message(last)
                    except:
                        pass
                    finally:
                        break
            await self.bot.say(box(page, lang="py"))

    async def _submissingroles_(self, subnomatchroles, author, channel):
        # Creates a list of roles on the subserver that haven't got a link to any roles on the hostserver.
        msg = "Rolls the Subserver has, that are not linked to any of this server's roles.\nPosition: <ID> Name\n=============="
        sorted(subnomatchroles, key=self.getKeyRolePosition)
        for r in subnomatchroles:
            name = r.name
            position = r.position
            id = r.id
            msg += "\n " + str(position) + ": <" + id + "> "+ name

        result = list(pagify(msg, shorten_by=16))

        for i, page in enumerate(result):
            if i != 0 and i % 4 == 0:
                last = await self.bot.say("There are still {} messages. "
                                          "Type `more` to continue."
                                          "".format(len(result) - i))
                msg = await self.bot.wait_for_message(author=author,
                                                      channel=channel,
                                                      content="more",
                                                      timeout=10)
                if msg is None:
                    try:
                        await self.bot.delete_message(last)
                    except:
                        pass
                    finally:
                        break
            await self.bot.say(box(page, lang="py"))

    async def _hostrolelist_(self, serverroles, author, channel):
        # Creates a list of roles on the hostserver.
        msg = "Rolls this server has.\nPosition: <ID> Name\n=============="
        for r in serverroles:
            name = r.name
            position = r.position
            id = r.id
            msg += "\n " + str(position) + ": <" + id + "> " + name

        result = list(pagify(msg, shorten_by=16))

        for i, page in enumerate(result):
            if i != 0 and i % 4 == 0:
                last = await self.bot.say("There are still {} messages. "
                                          "Type `more` to continue."
                                          "".format(len(result) - i))
                msg = await self.bot.wait_for_message(author=author,
                                                      channel=channel,
                                                      content="more",
                                                      timeout=10)
                if msg is None:
                    try:
                        await self.bot.delete_message(last)
                    except:
                        pass
                    finally:
                        break
            await self.bot.say(box(page, lang="py"))

    async def _subrolelist_(self, subserverroles, author, channel):
        #Creates a list of roles on the subserver.
        msg = "Rolls the Subserver has.\nPosition: <ID> Name\n=============="
        for r in subserverroles:
            name = r.name
            position = r.position
            id = r.id
            msg += "\n " + str(position) + ": <" + id + "> " + name

        result = list(pagify(msg, shorten_by=16))

        for i, page in enumerate(result):
            if i != 0 and i % 4 == 0:
                last = await self.bot.say("There are still {} messages. "
                                          "Type `more` to continue."
                                          "".format(len(result) - i))
                msg = await self.bot.wait_for_message(author=author,
                                                      channel=channel,
                                                      content="more",
                                                      timeout=10)
                if msg is None:
                    try:
                        await self.bot.delete_message(last)
                    except:
                        pass
                    finally:
                        break
            await self.bot.say(box(page, lang="py"))

    async def _savesubserverchanneloverrides_(self, server):
        #Saves the channel overrides in the subserver.
        subserverid = self.mservers[server.id].get("subserverid")
        subserver = discord.utils.get(self.bot.servers, id=subserverid)
        subserverchannels = [c for c in subserver.channels]

        for c in subserverchannels:
            current_overrides = defaultdict(lambda: channeloverride_template.copy(), self.mservers[server.id]["subserversavedchanneloverrides"].get(c.id))
            try:
                for o in c.overwrites:
                    if isinstance(o[0], discord.Role):
                        current_overrides["type"] = 'Role'
                    elif isinstance(o[0], discord.Member):
                        current_overrides["type"] = 'Member'
                    current_overrides["overrides"] = o[1]._values
                    self.mservers[server.id]["subserversavedchanneloverrides"][c.id] = current_overrides
            except discord.Forbidden:
                return "forbidden", c
        return None, None

    async def _subserverlockdown_(self, server):
        #Saves the channel overrides in the subserver.
        subserverid = self.mservers[server.id].get("subserverid")
        subserver = discord.utils.get(self.bot.servers, id=subserverid)
        subserverchannels = [c for c in subserver.channels]
        fchannels = []

        for c in subserverchannels:
            for o in c.overwrites:
                overwrite = c.overwrites_for(o[0])
                if c.type.name == 'text':
                    overwrite.send_messages = False
                if c.type.name == 'voice':
                    overwrite.speak = False
                overwrite.create_instant_invite = False
                try:
                    await self.bot.edit_channel_permissions(c, o[0], overwrite)
                except discord.Forbidden:
                    fchannels.append(c)
        if len(fchannels) == 0:
            return None, fchannels
        else:
            return "forbidden", fchannels

    async def _removesubserverlockdown_(self, server):
        #Restores the channel overrides in the subserver that the merge made in the lockdown.
        subserverid = self.mservers[server.id].get("subserverid")
        subserver = discord.utils.get(self.bot.servers, id=subserverid)
        subserverchannels = [c for c in subserver.channels]
        fchannels = []

        for c in subserverchannels:
            for o in c.overwrites:
                soverride = self.mservers[server.id]["subserversavedchanneloverrides"][c.id][o[0].id].get("overrides")
                overwrite = c.overwrites_for(o[0])
                if soverride is not None:
                    if c.type.name == 'text':
                        setattr(overwrite, "send_messages", soverride.get("send_messages"))
                    if c.type.name == 'voice':
                        setattr(overwrite, "speak", soverride.get("speak"))
                    setattr(overwrite, "create_instant_invite", soverride.get("create_instant_invite"))
                    try:
                        await self.bot.edit_channel_permissions(c, o[0], overwrite)
                    except discord.Forbidden:
                        fchannels.append(c)
        if len(fchannels) == 0:
            return None, fchannels
        else:
            return "forbidden", fchannels

    async def _memberprocessor_(self, hostm):
        #Processes a members merge into the host server.
        server = hostm.server
        subserverid = self.mservers[server.id].get("subserverid")
        subserver = discord.utils.get(self.bot.servers, id=subserverid)
        statuschannel = discord.utils.get(server.channels, id=self.mservers[server.id].get("statuschannel"))
        subm = subserver.get_member(hostm.id)
        memberlist = defaultdict(lambda: member_info_template.copy(), self.mservers[server.id]["members"])
        subexemptrole = discord.utils.get(subserver.roles,
                                          id=self.mservers[server.id].get("subexemptrole"))
        submem = subserver.get_member(hostm.id)
        srlist = None
        frlist = None
        dmstat = ""

        # Error Embed
        critmsg = discord.Embed(colour=discord.Colour(0xFF0000),
                                timestamp=datetime.datetime.today())
        critmsg.set_author(name="Merge Member Procesor",
                           icon_url="http://i.imgur.com/T5L6Djq.png")
        critmsg.set_thumbnail(url="https://i.imgur.com/zNU3Y9m.png")
        critmsg.add_field(name="<:res1error:330424101661442050> *Critical error encountered, halting merge*",
                          value="\n```[prefix]mergeresume```",
                          inline=False)

        #Ignore Bots
        if hostm.bot is True:
            await self.bot.send_message(content="The user \"{}\`{}`\" was skipped: *Bot account.*".format(hostm.name, hostm.id))
            return

        #Throw if they've already been processed
        if memberlist[hostm.id]["processed"] is True:
            return

        #Create Initial role msg
        msg = "Roles applied to {} in \"{}\".\n\nMerge being processed: \"{}\" into \"{}\"\n\nRoles given:\n".format(hostm.name, server.name, subserver.name, server.name)

        #Check to see if I have perms
        if not statuschannel.permissions_for(server.me).manage_roles:
            msg = "- ERROR: I don't have the manage_roles perm on this server!"
            await self.bot.send_message(destination=statuschannel, content=msg)
            self.mservers[server.id]["running"] = False
            self.save()
            return 'critical'

        #Process linked roles
        error, srlist, frlist = await self._applylinkedroles_(hostm, server, subserver)

        #Process Roles applied.
        if len(srlist) != 0:
            for r in srlist:
                msg += "+ \"{}\" | Success!\n".format(r.name)
                memberlist[hostm.id]["sroles"][r.id] = r.name
        if len(frlist) != 0:
            for r in frlist:
                msg += "- \"{}\" | Failed, this role is above my top role!\n".format(r.name)
                memberlist[hostm.id]["froles"][r.id] = r.name

        #pagify messages in case over 2k chars
        result = list(pagify(msg, shorten_by=16))

        #Send dm if no poir issues.
        if memberlist[hostm.id].get("dm") is None:
            for i, page in enumerate(result):
                try:
                    await self.bot.send_message(destination=hostm, content=box(page, lang="diff"))
                    dmstat = "+ DM Message returned: Success\n\n"
                except discord.Forbidden:
                    dmstat = "- DM Message returned: Forbbiden (I may be blocked by the user)\n\n"
                    memberlist[hostm.id]["dm"] = "forbidden"
                except discord.HTTPException:
                    dmstat = "- DM Message returned: HTTPException\n\n"
                    memberlist[m.id]["dm"] = "HTTPException"
                except discord.NotFound:
                    dmstat = "- DM Message returned: Destination not found.\n\n"
                    memberlist[m.id]["dm"] = "Destination not found."
        else:
            dmstat = "- DM Message for user remembered as Forbbiden. Dm was not not attempted this time.\n\n"

        #Kick the user if they aren't exempt. If Forbidden is returned, stop the servermerge processor(This should never happen). When a member is processed and kick from the subserver, they are considered processed
        if self.isexempt(subm, subexemptrole):
            msg = "- Member has the exemption role!\n\n" + msg
            memberlist[hostm.id]["processed"] = True
            self.mservers[server.id]["members"][hostm.id] = memberlist[hostm.id]
            self.save()

        else:
            try:
                await self.bot.kick(submem)
                msg = "+ Member has been removed from the subserver!\n\n" + msg
                self.mservers[server.id]["memberprocessedcount"] += 1
                memberlist[hostm.id]["processed"] = True
                self.mservers[server.id]["members"][hostm.id] = memberlist[hostm.id]
                self.save()
            except discord.Forbidden:
                critmsg.add_field(name="<:res1error:330424101661442050> *Warning*",
                                  value="```diff\n- I'm not allowed kick {} from {}\n Please make sure I have the perms to do so. Halting servermerge!```\n\nResume with `[prefix]mergeresume`".format(
                                      hostm.mention, subserver.name),
                                  inline=False)
                await self.bot.send_message(destination=statuschannel,
                                            embed=critmsg)
                self.mservers[server.id]["running"] = False
                self.save()
                return

        #Add the process status to the front of the message and post the results in the status channel.
        msg = dmstat + msg
        result = list(pagify(msg, shorten_by=16))

        for i, page in enumerate(result):
            await self.bot.send_message(destination=statuschannel, content=box(page, lang="diff"))
        return

    async def _applylinkedroles_(self, hostm, server, subserver):
        #Applies linked roles to a member.
        statuschannel = discord.utils.get(server.channels, id=self.mservers[server.id].get("statuschannel"))
        linkedroles = self.mservers[server.id].get("linkedroles")
        subm = subserver.get_member(hostm.id)
        srlist = []
        frlist = []
        error = None

        if not statuschannel.permissions_for(server.me).manage_roles:
            error = 'manage_roles'
            return error

        for r in subm.roles:
            for linkcount in linkedroles:
                if linkedroles[linkcount]["subroleid"] == r.id:
                    hrole = discord.utils.get(server.roles, id=linkedroles[linkcount].get("hostroleid"))
                    if server.me.top_role.position > hrole.position:
                        srlist.append(hrole)
                    else:
                        frlist.append(hrole)
        if len(srlist) != 0:
            try:
                await self.bot.add_roles(hostm, *srlist)
            except discord.Forbidden:
                error = 'Forbidden'
                return error
        return error, srlist, frlist

    def isexempt(self, subm, erole):
        for r in subm.roles:
            if r is erole:
                return True
        return False

    def getKeyRolePosition(self, role):
        return role.position

    def save(self):
        setpath = os.path.join('data', 'servermerge', 'mservers.json')
        dataIO.save_json(setpath, self.mservers)

    async def on_member_join(self, member):
        if self.mservers[member.server.id]["running"] is True:
            subserverid = self.mservers[member.server.id].get("subserverid")
            subserver = discord.utils.get(self.bot.servers, id=subserverid)
            if subserver.get_member(member.id) is not None:
                await self._memberprocessor_(member)

def check_folder():
    path = os.path.join('data', 'servermerge')
    if not os.path.exists(path):
        print('Creating ' + path + '...')
        os.makedirs(path)

def check_files():

    files = {
        "mservers.json": {}
    }
    datapath = os.path.join('data', 'servermerge')
    for filename, value in files.items():
        path = os.path.join(datapath, filename)
        if not os.path.isfile(path):
            print("Path: {}".format(path))
            print("Creating empty {}".format(filename))
            dataIO.save_json(path, value)


def setup(bot):
    check_folder()
    check_files()
    n = Servermerge(bot)
    bot.add_cog(n)

