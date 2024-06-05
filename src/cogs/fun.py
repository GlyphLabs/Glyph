from src.bot import Glyph
from discord.ext.commands import slash_command, Cog
from discord import Member, Option, ApplicationContext
from discord.commands import SlashCommandGroup, option


class Fun(Cog):
    def __init__(self, bot: Glyph):
        self.bot = bot

    @slash_command(name="hug", description="Hug someone | /hug [member]")
    @option(name="member", description="The member you want to kick", type=Member, required=True)
    async def hug(
        self,
        ctx: ApplicationContext,
        member: Member,
    ):
        await ctx.respond(f"You hugged {member.mention}! You look so cute together")


def setup(bot: Glyph):
    bot.add_cog(Fun(bot))
