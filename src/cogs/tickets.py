from src.bot import PurpBot
from discord.ext.commands import slash_command, Cog, has_permissions
from discord import Embed, ApplicationContext
from src.views import CreateTicket


class Tickets(Cog):
    def __init__(self, bot: PurpBot):
        self.bot = bot
        self.db = self.bot.db

    @slash_command(name="ticket-config", description="Configure Tickets.")
    @has_permissions(administrator=True)
    async def ticket_config(self, ctx: ApplicationContext):
        econf = Embed(
            title="Tickets",
            description="Click on the button below to create a ticket!",
            color=0x6B74C7,
        )
        await ctx.respond("Tickets configured automatically!", ephemeral=True)
        await ctx.respond(embed=econf, view=CreateTicket())


def setup(bot: PurpBot):
    bot.add_cog(Tickets(bot))
