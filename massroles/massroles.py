from typing import List

import discord
from discord.ext import commands
from __main__ import send_cmd_help, settings

from .utils import checks


class MassRoles:
    '''Add roles to users in a target role(including everone)'''

    def __init__(self, bot):
        self.bot = bot

    def _member_has_role(self, member: discord.Member, role: discord.Role):
        return role in member.roles

    def _get_users_with_role(self, server: discord.Server,
                             role: discord.Role) -> List[discord.User]:
        roled = []
        for member in server.members:
            if self._member_has_role(member, role):
                roled.append(member)
        return roled

    @commands.command(no_pm=True, pass_context=True, name="massaddrole", aliases=["mar"])
    @checks.mod_or_permissions(administrator=True)
    async def _mar(self, ctx: commands.Context,
                   *roles: discord.Role):
        """Start the massrole add by providing the role you want **ADDED**, then the role of the users you want it added to.
        """
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
            return False

        server = ctx.message.server
        sender = ctx.message.author
        channel = ctx.message.channel

        if not channel.permissions_for(server.me).manage_roles:
            await self.bot.say('I don\'t have manage_roles.')
            return False

        await self.bot.say("Please confirm:\nThe target role is-->`" + roles[0].name + "`\nThe role being added is-->`" + roles[1].name + "`\nSay yes to continue, or aything else to escape.")
        answer = await self.bot.wait_for_message(timeout=15,
                                                 author=ctx.message.author)

        if answer is None:
            await self.bot.say("Timed Out")

        elif answer.content.lower().strip() == "yes":
            addroles = self._get_users_with_role(server, roles[0])
            for user in addroles:
                try:
                    await self.bot.add_roles(user, role)
                except (discord.Forbidden, discord.HTTPException):
                    continue
            await self.bot.say("Completed")
        else:
            await self.bot.say("Cancelled")
            return False

    @commands.command(no_pm=True, pass_context=True, name="massremoverole", aliases=["mrr"])
    @checks.mod_or_permissions(administrator=True)
    async def _mrr(self, ctx: commands.Context,
                   roles: discord.Role):
        """Removes the traget role from any users who have it.
        """
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
            return False

        server = ctx.message.server
        sender = ctx.message.author
        channel = ctx.message.channel

        if not channel.permissions_for(server.me).manage_roles:
            await self.bot.say('I don\'t have manage_roles.')
            return False

        await self.bot.say("Please confirm:\nThe role being removed is-->`" + role.name + "`\nSay yes to continue, or anything else to escape.")
        answer = await self.bot.wait_for_message(timeout=15,
                                                 author=ctx.message.author)

        if answer is None:
            await self.bot.say("Timed Out")

        elif answer.content.lower().strip() == "yes":
            await self.bot.say("Yes")
            removerole = self._get_users_with_role(server, roles[0])
            for user in removerole:
                try:
                    await self.bot.remove_roles(user, role)
                except (discord.Forbidden, discord.HTTPException):
                    continue
            await self.bot.say("Completed")
        else:
            await self.bot.say("Cancelled")
            return False


def setup(bot: commands.Bot):
    bot.add_cog(MassRoles(bot))
