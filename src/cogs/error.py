# an error handling cog
from discord.ext.commands import Cog
from src.bot import Glyph
from discord.errors import Forbidden, HTTPException, NotFound
from discord import Embed


class Error(Cog):
    def __init__(self, bot: Glyph):
        self.bot = bot

    @Cog.listener()
    async def on_application_command_error(self, ctx, error):
        embed = Embed(color=0xFF0000).set_author(name="Error")
        if isinstance(error, Forbidden):
            embed.description = "I don't have permission to do that."
            await ctx.respond(embed=embed, ephemeral=True)
        elif isinstance(error, HTTPException):
            embed.description = "An error occurred while processing your request."
            await ctx.respond(embed=embed, ephemeral=True)
        elif isinstance(error, NotFound):
            embed.description = "The requested resource was not found."
            await ctx.respond(embed=embed, ephemeral=True)
        else:
            raise error


def setup(bot: Glyph):
    bot.add_cog(Error(bot))
