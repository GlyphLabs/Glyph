from src.bot import PurpBot
from discord.ext.commands import slash_command, Cog
from discord import Member, Option, ApplicationContext


class Fun(Cog):
    def __init__(self, bot: PurpBot):
        self.bot = bot

    @slash_command(name="hug", description="Hug someone | /hug [member]")
    async def hug(self, ctx: ApplicationContext, member: Option(Member, description="The member you want to hug", required=True)):
        await ctx.respond(f"You hugged {member.mention}! You look so cute together")

def setup(bot: PurpBot):
    bot.add_cog(Fun(bot))
