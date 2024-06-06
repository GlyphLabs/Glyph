import logging
from discord.errors import HTTPException
from discord.ext.commands.errors import MissingPermissions
from discord.ext.commands.cog import Cog
from src.bot import Glyph
from discord.enums import AuditLogAction
from discord.guild import Guild
from discord.embeds import Embed
from discord.colour import Colour
from discord.commands import ApplicationContext
from discord.message import Message

class Events(Cog):
    def __init__(self, bot: Glyph):
        self.bot = bot

    @Cog.listener()
    async def on_guild_join(self, guild: Guild):
        events = await guild.audit_logs(
            limit=3
        ).flatten()  # grab a few extras, just in case
        events = filter(
            lambda x: x.action == AuditLogAction.bot_add
            and x.target.id == self.bot.user.id, # type: ignore
            events,
        )  # type: ignore
        if not (event := next(events, None)) or not event.user: # type: ignore
            return
        embed = Embed(
            title=f"Thanks for adding {self.bot.user.display_name}",
            description=f"Use the `/setup` command in {guild.name} to get started!",
            color=0xFFF,
        ).set_author(
            name="Welcome to Glyph!", icon_url=self.bot.user.display_avatar.url
        )
        try:
            await event.user.send(embed=embed)
        except HTTPException as e:
            if e.code == 50007:
                return  # idc about forbidden, that just means dms are private
            logging.error(f"Failed to send welcome message to {event.user}")
            logging.error(e)
            pass

    @Cog.listener()
    async def on_command_error(self, ctx: ApplicationContext, error: Exception):
        """central error handling for commands

        Args:
            ctx (Context): the information about the execution of the command
            error (Exception): the error itself
        """
        if isinstance(error, MissingPermissions):
            embed = Embed(description="Missing required permissions", color=Colour.red())
            embed.set_author(
                name="Error",
                icon_url="https://cdn.discordapp.com/emojis/1055805812511080499.webp?size=96&quality=lossless",
            )
            await ctx.respond(embed=embed, ephemeral=True)


    @Cog.listener()
    async def on_message(self, message: Message):
        """what to do when a message is sent

        Args:
            message (discord.Message): the message itself
        """
        if message.content == self.bot.user.mention:  # type: ignore
            embed = Embed(
                description="My default prefix is: `/` (Slash Commands)", color=0xFFFFFF
            )
            await message.channel.send(embed=embed)
        await self.bot.process_commands(message)


def setup(bot: Glyph):
    bot.add_cog(Events(bot))
