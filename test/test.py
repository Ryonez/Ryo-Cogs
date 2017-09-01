from typing import List

import discord
from discord.ext import commands

from .utils import checks


class test:
    '''test'''

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

    @commands.command(no_pm=True, pass_context=True, name="test")
    @checks.mod_or_permissions(administrator=True)
    async def _mdm(self, ctx: commands.Context,
                   role: discord.Role):
        """Start the massrole add by providing the role you want **ADDED**, then the role of the users you want it added to.
        """

        server = ctx.message.server
        sender = ctx.message.author

        addrole = role

        await self.bot.say("Please tell me the role you wish to group add **TO**:")
        answer = await self.bot.wait_for_message(timeout=15,
                                                 author=ctx.message.author)

        if answer is None:
            await self.bot.say("Timed Out")

        elif answer.content == role: discord.Role:
            await self.bot.say(addrole.id + "" + answer.id)

        else:
            return




def setup(bot: commands.Bot):
    bot.add_cog(test(bot))
