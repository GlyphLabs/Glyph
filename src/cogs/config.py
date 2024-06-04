from src.bot import Glyph
from discord.ext.commands import Cog
from discord.commands import SlashCommandGroup
from discord import Option, ApplicationContext, TextChannel, Embed, Permissions
from src.db import GuildSettings
from src.views import CreateTicket


class Config(Cog):
    def __init__(self, bot: Glyph):
        self.bot = bot

    def cog_check(self, ctx: ApplicationContext) -> bool:
        return ctx.author.guild_permissions.manage_guild

    config = SlashCommandGroup("config", "Configure the bot for your server.")
    ai_config = config.create_subgroup(
        "ai", "Configure the AI moderation for your server."
    )
    
    @config.command(
            name="levels",
            description="Enable or disable the level system for your server.",
    )
    async def levels(
        self,
        ctx: ApplicationContext,
        enabled: Option(
            bool,
            description="Whether or not to enable the level system.",
            required=True,
        )
    ):
        settings = await self.bot.db.get_guild_settings(ctx.guild.id)
        if not settings:
            settings = GuildSettings(guild_id=ctx.guild.id, level_system=enabled)
        else:
            settings.level_system = enabled
        await self.bot.db.set_guild_settings(ctx.guild.id, settings)
        await ctx.respond(
            embed=Embed(
                description=f"Level system has been {'enabled' if enabled else 'disabled'} for this server.",
                color=0x6B74C7,
            ).set_author(name=f"Level System {'Enabled' if enabled else 'Disabled'}")
        )

    @ai_config.command(
        name="setchannel",
        description="Enable AI moderation for your server and set reports channel.",
    )
    async def ai_enable(
        self,
        ctx: ApplicationContext,
        reports_channel: Option(
            TextChannel,
            description="Channel where the intelligent reports should go.",
            required=True,
        ),
    ):
        reports_channel: TextChannel = reports_channel  # typing
        settings = await self.bot.db.get_guild_settings(ctx.guild.id)
        if not settings:
            settings = GuildSettings(
                guild_id=ctx.guild.id, ai_reports_channel=reports_channel.id
            )
        else:
            settings.ai_reports_channel = reports_channel.id
        perms: Permissions = reports_channel.permissions_for(ctx.guild.me)
        if not perms.send_messages:
            await ctx.respond(
                embed=Embed(
                    description="I don't have permissions to send messages in that channel.",
                    color=0xFF0000,
                )
                .set_author(name="Uh oh!")
                .set_footer(text="Your settings were not saved.")
            )
            return
        await self.bot.db.set_guild_settings(ctx.guild.id, settings)
        await ctx.respond(
            embed=Embed(
                description=f"AI moderation has been enabled for this server. Reports will be sent to {reports_channel.mention}.",
                color=0xffffff,
            ).set_author(name="AI Moderation Enabled")
        )

    @ai_config.command(
        name="disable", description="Disable AI moderation for your server."
    )
    async def ai_disable(self, ctx: ApplicationContext):
        settings = await self.bot.db.get_guild_settings(ctx.guild.id)
        if not settings:
            settings = GuildSettings(guild_id=ctx.guild.id, ai_reports_channel=None)
        else:
            settings.ai_reports_channel = None
        await self.bot.db.set_guild_settings(ctx.guild.id, settings)
        await ctx.respond(
            embed=Embed(
                title="AI Moderation Disabled",
                description="AI moderation has been disabled for this server.",
                color=0xffffff,
            )
        )

    @config.command(
        name="view", description="See the bot's configuration for your server."
    )
    async def config_view(self, ctx: ApplicationContext):
        settings = await self.bot.db.get_guild_settings(ctx.guild.id) or GuildSettings(
            guild_id=ctx.guild.id, ai_reports_channel=None
        )
        await ctx.respond(
            embed=Embed(
                color=0xffffff,
            )
            .set_author(
                name=f"{ctx.guild.name} Configuration",
                icon_url=ctx.guild.icon.url
                if ctx.guild.icon
                else ctx.bot.user.display_avatar,
            )
            .add_field(
                name="AI Moderation",
                value=f"Enabled: {settings.ai_reports_channel is not None}\nReports Channel: {f'<#{settings.ai_reports_channel}>' if settings.ai_reports_channel is not None else 'None'}",
            )
        )

    @config.command(
        name="reset", description="Reset the bot's configuration for your server."
    )
    async def config_reset(self, ctx: ApplicationContext):
        await self.bot.db.set_guild_settings(
            ctx.guild.id, GuildSettings(guild_id=ctx.guild.id, ai_reports_channel=None)
        )
        await ctx.respond(
            embed=Embed(
                title="Configuration Reset",
                description="The bot's configuration has been reset for this server.",
                color=0xffffff,
            )
        )

    @config.command(name="ticket_panel", description="Create a new ticket panel.")
    async def ticket_config(
        self,
        ctx: ApplicationContext,
        panel_channel: Option(
            TextChannel,
            description="Channel where the intelligent reports should go.",
            required=False,
        ),
    ):
        panel_channel = panel_channel or ctx.channel
        econf = Embed(
            title="Tickets",
            description="Click on the button below to create a ticket!",
            color=0xffffff,
        )
        await ctx.respond("Tickets configured automatically!", ephemeral=True)
        await panel_channel.send(embed=econf, view=CreateTicket())

    async def cog_command_error(
        self, ctx: ApplicationContext, error: Exception
    ) -> None:
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.respond(
                "You do not have permission to use this command.", ephemeral=True
            )
            return
        return await super().cog_command_error(ctx, error)


def setup(bot: Glyph):
    bot.add_cog(Config(bot))
