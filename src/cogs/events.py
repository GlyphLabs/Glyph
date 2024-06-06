import logging
from discord import HTTPException
from discord.ext.commands.cog import Cog
from src.bot import Glyph
from discord.enums import AuditLogAction
from discord.guild import Guild
from discord.embeds import Embed

class Events(Cog):
    def __init__(self, bot: Glyph):
        self.bot = bot

    @Cog.listener()
    async def on_guild_join(self, guild: Guild):
        events = await guild.audit_logs(limit=3).flatten() # grab a few extras, just in case
        events = filter(lambda x: x.action == AuditLogAction.bot_add and x.target.id == self.bot.user.id, events) # type: ignore
        if not (event := next(events, None)) or not event.user:
            return
        embed = Embed(
            title=f"Thanks for adding {self.bot.user.display_name}",
            description=f"Use the `/setup` command in {guild.name} to get started!",
            color=0xfff
        ).set_author(
            name="Welcome to Glyph!",
            icon_url=self.bot.user.display_avatar.url
        )
        try:
            await event.user.send(embed=embed)
        except HTTPException as e:
            if e.code == 50007:
                return # idc about forbidden, that just means dms are private
            logging.error(f"Failed to send welcome message to {event.user}")
            logging.error(e)
            pass

def setup(bot: Glyph):
    bot.add_cog(Events(bot))