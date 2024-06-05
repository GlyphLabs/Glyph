from discord.commands import SlashCommandGroup, option
from src.bot import Glyph
from discord.ext.commands import (
    slash_command,
    Cog,
    has_permissions,
    cooldown,
    BucketType,
)
from discord import Embed, ApplicationContext, Member, Colour, Role
from discord.ext.commands.errors import MissingPermissions, CommandOnCooldown
from datetime import timedelta
from humanize import naturaldelta


class Moderation(Cog):
    def __init__(self, bot: Glyph):
        self.bot = bot

    async def addwarn(self, ctx: ApplicationContext, reason: str, user: Member):
        await self.bot.db.create_warn(user.id, ctx.guild.id, reason)

    @slash_command(name="kick", description="Kicks a member | /kick [member]")
    @has_permissions(kick_members=True)
    @option(name="member", description="The member you want to kick", type=Member, required=True)
    @option(name="reason", description="The reason to kick the member", type=str, required=True)
    async def kick(
        self,
        ctx: ApplicationContext,
        member: Member,
        reason: str,
    ):
        if member.guild_permissions.administrator:
            em = Embed(
                description="You cannot kick this member, they have `Administrator` OR `Manage Server` permissions",
                color=Colour.red(),
            )
            em.set_author(
                name="Error",
                icon_url="https://cdn.discordapp.com/emojis/1055805812511080499.webp?size=96&quality=lossless",
            )
            await ctx.respond(embed=em, ephemeral=True)
        else:
            if not reason:
                reason = "No reason provided"
            await member.kick(reason=reason)
            embed = Embed(
                description=f"{member.mention} has been kicked\n**Reason**: {reason}",
                color=Colour.green(),
            )
            embed.set_author(
                name="Success",
                icon_url="https://cdn.discordapp.com/emojis/1055805763651641355.webp?size=96&quality=lossless",
            )
            await ctx.respond(embed=embed)

    @kick.error
    async def kickerror(self, ctx: ApplicationContext, error):
        if isinstance(error, MissingPermissions):
            embed = Embed(
                description="You are missing the `KICK_MEMBERS` permission",
                color=Colour.red(),
            )
            embed.set_author(
                name="Error",
                icon_url="https://cdn.discordapp.com/emojis/1055805812511080499.webp?size=96&quality=lossless",
            )
            await ctx.respond(embed=embed, ephemeral=False)
        else:
            em = Embed(
                description="An error occured. Please try again later or contact the developers at the support server",
                color=Colour.red(),
            )
            em.set_author(
                name="Error",
                icon_url="https://cdn.discordapp.com/emojis/1055805812511080499.webp?size=96&quality=lossless",
            )
            await ctx.respond(embed=em, ephemeral=True)
            raise error

    @slash_command(name="ban", description="Bans a member | /ban [member]")
    @has_permissions(ban_members=True)
    @option(name="member", description="The member you want to ban", type=Member, required=True)
    @option(name="reason", description="The reason to ban the member", type=str, required=True)
    async def ban(
        self,
        ctx: ApplicationContext,
        member: Member,
        reason: str,
    ):
        if member.guild_permissions.administrator:
            em = Embed(
                description="You cannot ban this member, they have `Administrator` OR `Manage Server` permissions",
                color=Colour.red(),
            )
            em.set_author(
                name="Error",
                icon_url="https://cdn.discordapp.com/emojis/1055805812511080499.webp?size=96&quality=lossless",
            )
            await ctx.respond(embed=em, ephemeral=True)
        else:
            if not reason:
                reason = "No reason provided"
            await member.ban(reason=reason)
            embed = Embed(
                description=f"{member.mention} has been banned\n**Reason**: {reason}",
                color=Colour.green(),
            )
            embed.set_author(
                name="Success",
                icon_url="https://cdn.discordapp.com/emojis/1055805763651641355.webp?size=96&quality=lossless",
            )
            await ctx.respond(embed=embed)

    @ban.error
    async def banerror(self, ctx: ApplicationContext, error):
        if isinstance(error, MissingPermissions):
            embed = Embed(
                description="You are missing the `BAN_MEMBERS` permission",
                color=Colour.red(),
            )
            embed.set_author(
                name="Error",
                icon_url="https://cdn.discordapp.com/emojis/1055805812511080499.webp?size=96&quality=lossless",
            )
            await ctx.respond(embed=embed, ephemeral=False)
        else:
            em = Embed(
                description="An error occured. Please try again later or check the bot's permissions in the roles page in your server's settings",
                color=Colour.red(),
            )
            em.set_author(
                name="Error",
                icon_url="https://cdn.discordapp.com/emojis/1055805812511080499.webp?size=96&quality=lossless",
            )
            await ctx.respond(embed=em, ephemeral=True)
            raise error

    @slash_command(name="warn", description="Warns someone | /warn [member] <reason>")
    @has_permissions(manage_messages=True)
    @option(name="member", description="The member you want to warn", type=Member, required=True)
    @option(name="reason", description="The reason to warn the member", type=str, required=True)
    async def warn(
        self,
        ctx: ApplicationContext,
        member: Member,
        reason: str,
    ):
        await self.addwarn(ctx, reason, member)
        embed = Embed(
            colour=Colour.green(),
            description=f"**{member.mention}** was warned | **Reason:** {reason}",
        )
        embed.set_author(
            name="Success",
            icon_url="https://cdn.discordapp.com/emojis/1055805763651641355.webp?size=96&quality=lossless",
        )
        await ctx.respond(embed=embed, ephemeral=True)

    @slash_command(
        name="unwarn", description="Delete all of someone's warn(s) | /unwarn [member]"
    )
    @has_permissions(manage_guild=True)
    @option(name="member", description="The member you want to remove warns from", type=Member, required=True)
    async def unwarn(
        self,
        ctx: ApplicationContext,
        member: Member,
    ):
        await self.bot.db.delete_warns(member.id, ctx.guild.id)
        embed = Embed(
            colour=Colour.green(),
            description=f"Removed all of {member.mention}'s warn(s)",
        )
        embed.set_author(
            name="Success",
            icon_url="https://cdn.discordapp.com/emojis/1055805763651641355.webp?size=96&quality=lossless",
        )
        await ctx.respond(embed=embed)

    @slash_command(
        name="warns", description="Shows someone's warnings | /warrns [member]"
    )
    @option(name="member", description="The member you want to remove warns from", type=Member, required=True)
    async def warns(
        self,
        ctx: ApplicationContext,
        member: Member,
    ):
        rows = await self.bot.db.get_warns(member.id, ctx.guild.id)
        if rows:
            rows.sort(key=lambda x: x.time, reverse=True)
            embed = Embed(colour=0xffffff, title=f"Warnings for {member.name}")
            warnnum = 0
            for row in rows:
                warnnum += 1
                embed.add_field(
                    name=f"Warning #{warnnum}",
                    value=f"**Reason:** {row.reason} | **Date:** <t:{int(row.time)}:F>",
                )
            await ctx.respond(embed=embed)
        else:
            embed = Embed(colour=0xffffff, title=f"No warnings for {member.name}")
            await ctx.respond(embed=embed)

    @slash_command(name="timeout", description="Puts a member in timeout")
    @option(name="member", description="The member you want to time out", type=Member, required=True)
    @option(name="time", description="The period of time to time the user out for. Expressed as 1d, 5, etc.", type=str, required=True)
    async def timeout(
        self,
        ctx: ApplicationContext,
        member: Member,
        time: str
    ):
        """Apply a timeout to a member"""
        time_units = {
            "s": 1,  # seconds
            "m": 60,  # minutes
            "h": 3600,  # hours
            "d": 86400,  # days
        }

        try:
            seconds = int(time[:-1]) * time_units[(time[-1])]
        except Exception:
            return await ctx.respond(f"Invalid time `{time}`")

        duration = timedelta(seconds=seconds)
        # timeout for the amount of time given, then remove timeout
        await member.timeout_for(duration)
        await ctx.respond(f"Member timed out for {naturaldelta(duration)}.")

    @slash_command(name="purge", description="Delete a certain amount of messages")
    @has_permissions(manage_messages=True)
    @cooldown(1, 5, BucketType.user)
    @option(name="messages", description="The amount of messages you want to delete", type=int, required=True)
    async def purge(
        self,
        ctx: ApplicationContext,
        messages: int
    ):
        await ctx.defer()
        m = await ctx.respond(f"Deleting {messages}...", ephemeral=True)
        x = await ctx.channel.purge(limit=messages) # type: ignore
        await m.edit(content=f"Deleted {len(x)} messages")

    # error handler

    @purge.error
    async def purgeerror(self, ctx: ApplicationContext, error):
        if isinstance(error, MissingPermissions):
            embed = Embed(
                description="You are missing the `MANAGE_MESSAGES` permission",
                color=Colour.red(),
            )
            embed.set_author(
                name="Error",
                icon_url="https://cdn.discordapp.com/emojis/1055805812511080499.webp?size=96&quality=lossless",
            )
            await ctx.respond(embed=embed)
        elif isinstance(error, CommandOnCooldown):
            await ctx.respond(error)
        else:
            raise error

    role = SlashCommandGroup("role", "Manage a user's roles")

    @role.command(name="add", description="Gives a user a role")
    @has_permissions(manage_guild=True)
    @option(name="role", description="The role to give the member", type=Role, required=True)
    @option(name="member", description="The member you want to give the role to", type=Member, required=True)
    async def addrole(
        self,
        ctx: ApplicationContext,
        role: Role,
        member: Member,
    ):
        await member.add_roles(role)
        embed = Embed(
            description=f"{member.mention} got {role.mention}", colour=0x2ECC71
        )
        embed.set_author(
            name="Success",
            icon_url="https://cdn.discordapp.com/emojis/1055805763651641355.webp?size=96&quality=lossless",
        )
        await ctx.respond(embed=embed, ephemeral=False)

    # error hadnler

    @addrole.error
    async def addroleerror(self, ctx: ApplicationContext, error):
        if isinstance(error, MissingPermissions):
            embed = Embed(
                description="You are missing the `MANAGE_SERVER` permission",
                color=Colour.red(),
            )
            embed.set_author(
                name="Error",
                icon_url="https://cdn.discordapp.com/emojis/1055805812511080499.webp?size=96&quality=lossless",
            )
            await ctx.respond(embed=embed, ephemeral=False)
        else:
            em = Embed(
                description="An error occured. Please try again later or contact the developers at the support server",
                color=Colour.red(),
            )
            em.set_author(
                name="Error",
                icon_url="https://cdn.discordapp.com/emojis/1055805812511080499.webp?size=96&quality=lossless",
            )
            await ctx.respond(embed=em, ephemeral=True)
            raise error

    @slash_command(name="remove", description="Removes a role from a user")
    @has_permissions(manage_guild=True)
    @option(name="role", description="The role to give the member", type=Role, required=True)
    @option(name="member", description="The member you want to give the role to", type=Member, required=True)
    async def removerole(
        self,
        ctx: ApplicationContext,
        role: Role,
        member: Member,
    ):
        await member.add_roles(role)
        embed = Embed(
            description=f"{member.mention} lost the {role.mention} role",
            colour=0x2ECC71,
        )
        embed.set_author(
            name="Success",
            icon_url="https://cdn.discordapp.com/emojis/1055805763651641355.webp?size=96&quality=lossless",
        )
        await ctx.respond(embed=embed, ephemeral=False)

    # error hadnler

    @removerole.error
    async def removeroleerror(self, ctx: ApplicationContext, error):
        if isinstance(error, MissingPermissions):
            embed = Embed(
                description="You are missing the `MANAGE_SERVER` permission",
                color=Colour.red(),
            )
            embed.set_author(
                name="Error",
                icon_url="https://cdn.discordapp.com/emojis/1055805812511080499.webp?size=96&quality=lossless",
            )
            await ctx.respond(embed=embed, ephemeral=False)
        else:
            em = Embed(
                description="An error occured. Please try again later or contact the developers at the support server",
                color=Colour.red(),
            )
            em.set_author(
                name="Error",
                icon_url="https://cdn.discordapp.com/emojis/1055805812511080499.webp?size=96&quality=lossless",
            )
            await ctx.respond(embed=em, ephemeral=True)
            raise error


def setup(bot: Glyph):
    bot.add_cog(Moderation(bot))
