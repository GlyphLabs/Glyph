from src.bot import PurpBot
from discord.ext.commands import (
    slash_command,
    Cog,
    has_permissions,
    cooldown,
    BucketType,
)
from discord import Embed, Option, ApplicationContext, Member, Colour, Role
from discord.ext.commands.errors import MissingPermissions, CommandOnCooldown
from datetime import timedelta


class Moderation(Cog):
    def __init__(self, bot: PurpBot):
        self.bot = bot

    async def addwarn(self, ctx: ApplicationContext, reason: str, user: Member):
        await self.bot.db.create_warn(user.id, ctx.guild.id, reason)

    @slash_command(name="kick", description="Kicks a member | /kick [member]")
    @has_permissions(kick_members=True)
    async def kick(
        self,
        ctx,
        member: Option(
            Member, description="The member you want to kick", required=True
        ),
        reason: Option(
            str, description="The reason the member is kicked", required=False
        ),
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
    async def kickerror(self, ctx, error):
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
    async def ban(
        self,
        ctx,
        member: Option(Member, description="The member you want to ban", required=True),
        reason: Option(
            str, description="The reason the member is banned", required=False
        ),
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
    async def banerror(self, ctx, error):
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
    async def warn(
        self,
        ctx: ApplicationContext,
        member: Option(
            Member, description="The member you want to warn", required=True
        ),
        reason: Option(
            str="No reason specified",
            description="The reason for the warn",
            required=False,
        ),
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
        await ctx.respond(embed=embed)

    @slash_command(
        name="unwarn", description="Delete all of someone's warn(s) | /unwarn [member]"
    )
    @has_permissions(manage_guild=True)
    async def unwarn(
        self,
        ctx: ApplicationContext,
        member: Option(
            Member,
            description="The member you want to remove the warns from",
            required=True,
        ),
    ):
        async with self.bot.db.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "DELETE FROM warns WHERE user = ? AND guild = ?",
                    (member.id, ctx.guild.id),
                )
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
    async def warns(
        self,
        ctx: ApplicationContext,
        member: Option(Member, description="The member's warns", required=True),
    ):
        rows = await self.bot.db.get_warns(member.id, ctx.guild.id)
        if rows:
            rows.sort(key=lambda x: x.time, reverse=True)
            embed = Embed(colour=0x6B74C7, title=f"Warnings for {member.name}")
            warnnum = 0
            for row in rows:
                warnnum += 1
                embed.add_field(
                    name=f"Warning #{warnnum}",
                    value=f"**Reason:** {row.reason} | **Date:** <t:{int(row.time)}:F>",
                )
            await ctx.respond(embed=embed)
        else:
            embed = Embed(colour=0x6B74C7, title=f"No warnings for {member.name}")
            await ctx.respond(embed=embed)

    @slash_command(name="timeout", description="Puts a member in timeout")
    async def timeout(self, ctx, member: Option(Member), minutes: Option(int)):
        """Apply a timeout to a member"""

        duration = timedelta(minutes=minutes)
        # timeout for the amount of time given, then remove timeout
        await member.timeout_for(duration)
        await ctx.reply(f"Member timed out for {minutes} minutes.")

    @slash_command(name="purge", description="Delete a certain amount of messages")
    @has_permissions(manage_messages=True)
    @cooldown(1, 5, BucketType.user)
    async def purge(
        self,
        ctx,
        messages: Option(
            int, description="The amount of messages you want to delete", required=True
        ),
    ):
        await ctx.defer()
        x = await ctx.channel.purge(limit=messages)
        await ctx.respond(f"Deleted {len(x)}", ephemeral=True)

    # error handler

    @purge.error
    async def purgeerror(self, ctx, error):
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

    @slash_command(name="addrole", description="Gives a user a role")
    @has_permissions(manage_guild=True)
    async def addrole(
        self,
        ctx: ApplicationContext,
        role: Option(Role, description="The role you want to add", required=True),
        member: Option(Member, description="The member who'll get the role"),
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

    @slash_command(name="removerole", description="Removes from a user a role")
    @has_permissions(manage_guild=True)
    async def removerole(
        self,
        ctx: ApplicationContext,
        role: Option(Role, description="The role you want to remove", required=True),
        member: Option(Member, description="The member"),
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


def setup(bot: PurpBot):
    bot.add_cog(Moderation(bot))
