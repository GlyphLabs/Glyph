import discord
from discord.ext import commands
from discord.commands import Option
from discord.ext.commands import MissingPermissions
from discord.ui import Button, View
from discord import Webhook

import os
import asyncio
import datetime
import math
import ast
from googlesearch import search

import aiosqlite
import aiofiles
import aiohttp

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(intents=intents)
bot.remove_command("help")
bot.reaction_roles = []

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, MissingPermissions):
        embed = discord.Embed(
            description="Missing required permissions",
            color=discord.Colour.red()
        )
        embed.set_author(
            name="Error", icon_url="https://cdn.discordapp.com/emojis/1055805812511080499.webp?size=96&quality=lossless")
        await ctx.reply(embed=embed)


@bot.event
async def on_message(message):
    ping = f"<@{bot.user.id}>"
    if message.content == ping:
        embed = discord.Embed(
            description="My default prefix is: `/` (Slash Commands)",
            color=0x6B74C7
        )
        await message.channel.send(embed=embed)
    return


async def addwarn(ctx, reason, user):
    async with bot.db.cursor() as cursor:
        await cursor.execute("INSERT INTO warns (user, reason, time, guild) VALUES (?, ?, ?, ?)", (user.id, reason, int(datetime.datetime.now().timestamp()), ctx.guild.id))
    await bot.db.commit()


@bot.slash_command(name="ping", description="Check the bot's API latency | /ping")
async def ping(ctx):
    await ctx.respond(f"API latency: {round(bot.latency * 1000)}ms")


@bot.slash_command(name="hug", description="Hug someone | /hug [member]")
async def hug(ctx, member: Option(discord.Member, description="The member you want to hug", required=True)):
    await ctx.respond(f"You hugged {member.mention}! You look so cute together")


@bot.slash_command(name="kick", description="Kicks a member | /kick [member]")
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: Option(discord.Member, description="The member you want to kick", required=True), reason: Option(str, description="The reason the member is kicked", required=False)):
    if member.guild_permissions.administrator:
        em = discord.Embed(
            description="You cannot kick this member, they have `Administrator` OR `Manage Server` permissions",
            color=discord.Colour.red()
        )
        em.set_author(
            name="Error", icon_url="https://cdn.discordapp.com/emojis/1055805812511080499.webp?size=96&quality=lossless")
        await ctx.respond(embed=em, ephemeral=True)
    else:
        if reason == None:
            reason = "No reason provided"
        await member.kick(reason=reason)
        embed = discord.Embed(
            description=f"{member.mention} has been kicked\n**Reason**: {reason}",
            color=discord.Colour.green()
        )
        embed.set_author(
            name="Success", icon_url="https://cdn.discordapp.com/emojis/1055805763651641355.webp?size=96&quality=lossless")
        await ctx.respond(embed=embed)


@kick.error
async def kickerror(ctx, error):
    if isinstance(error, MissingPermissions):
        embed = discord.Embed(
            description="You are missing the `KICK_MEMBERS` permission",
            color=discord.Colour.red()
        )
        embed.set_author(
            name="Error", icon_url="https://cdn.discordapp.com/emojis/1055805812511080499.webp?size=96&quality=lossless")
        await ctx.respond(embed=embed, ephemeral=False)
    else:
        em = discord.Embed(
            description="An error occured. Please try again later or contact the developers at the support server",
            color=discord.Colour.red()
        )
        em.set_author(
            name="Error", icon_url="https://cdn.discordapp.com/emojis/1055805812511080499.webp?size=96&quality=lossless")
        await ctx.respond(embed=em, ephemeral=True)
        raise error


@bot.slash_command(name="ban", description="Bans a member | /ban [member]")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: Option(discord.Member, description="The member you want to ban", required=True), reason: Option(str, description="The reason the member is banned", required=False)):
    if member.guild_permissions.administrator:
        em = discord.Embed(
            description="You cannot ban this member, they have `Administrator` OR `Manage Server` permissions",
            color=discord.Colour.red()
        )
        em.set_author(
            name="Error", icon_url="https://cdn.discordapp.com/emojis/1055805812511080499.webp?size=96&quality=lossless")
        await ctx.respond(embed=em, ephemeral=True)
    else:
        if reason == None:
            reason = "No reason provided"
        await member.ban(reason=reason)
        embed = discord.Embed(
            description=f"{member.mention} has been banned\n**Reason**: {reason}",
            color=discord.Colour.green()
        )
        embed.set_author(
            name="Success", icon_url="https://cdn.discordapp.com/emojis/1055805763651641355.webp?size=96&quality=lossless")
        await ctx.respond(embed=embed)


@ban.error
async def banerror(ctx, error):
    if isinstance(error, MissingPermissions):
        embed = discord.Embed(
            description="You are missing the `BAN_MEMBERS` permission",
            color=discord.Colour.red()
        )
        embed.set_author(
            name="Error", icon_url="https://cdn.discordapp.com/emojis/1055805812511080499.webp?size=96&quality=lossless")
        await ctx.respond(embed=embed, ephemeral=False)
    else:
        em = discord.Embed(
            description="An error occured. Please try again later or check the bot's permissions in the roles page in your server's settings",
            color=discord.Colour.red()
        )
        em.set_author(
            name="Error", icon_url="https://cdn.discordapp.com/emojis/1055805812511080499.webp?size=96&quality=lossless")
        await ctx.respond(embed=em, ephemeral=True)
        raise error


@bot.slash_command(name="guildcount", description="shows bot's servers")
async def guildcount(ctx):
    embed = discord.Embed(
        description=f"PurpBot is in {len(bot.guilds)} servers!",
        color=0x6B74C7
    )
    await ctx.respond(embed=embed)


@bot.slash_command(name="warn", description="Warns someone | /warn [member] <reason>")
@commands.has_permissions(manage_messages=True)
async def warn(ctx: commands.Context, member: Option(discord.Member, description="The member you want to warn", required=True), reason: Option(str="No reason specified", description="The reason for the warn", required=False)):
    await addwarn(ctx, reason, member)
    embed = discord.Embed(
        colour=discord.Colour.green(),
        description=f"**{member.mention}** was warned | **Reason:** {reason}",
    )
    embed.set_author(
        name="Success", icon_url="https://cdn.discordapp.com/emojis/1055805763651641355.webp?size=96&quality=lossless")
    await ctx.respond(embed=embed)


@bot.slash_command(name="unwarn", description="Delete all of someone's warn(s) | /unwarn [member]")
@commands.has_permissions(manage_guild=True)
async def unwarn(ctx: commands.Context, member: Option(discord.Member, description="The member you want to remove the warns from", required=True)):
    async with bot.db.cursor() as cursor:
        await cursor.execute("SELECT reason FROM warns WHERE user = ? AND guild = ?", (member.id, ctx.guild.id))
        data = await cursor.fetchone()
        if data:
            await cursor.execute("DELETE FROM warns WHERE user = ? AND guild = ?", (member.id, ctx.guild.id))
        embed = discord.Embed(
            colour=discord.Colour.green(),
            description=f"Removed all of {member.mention}'s warn(s)"
        )
        embed.set_author(
            name="Success", icon_url="https://cdn.discordapp.com/emojis/1055805763651641355.webp?size=96&quality=lossless")
        await ctx.respond(embed=embed)


@bot.slash_command(name="warns", description="Shows someone's warnings | /warrns [member]")
async def warns(ctx: commands.Context, member: Option(discord.Member, description="The member's warns", required=True)):
    async with bot.db.cursor() as cursor:
        await cursor.execute("SELECT reason, time FROM warns WHERE user = ? AND guild = ?", (member.id, ctx.guild.id))
        data = await cursor.fetchall()
        if data:
            embed = discord.Embed(
                colour=0x6B74C7,
                title=f"Warnings for {member.name}"
            )
            warnnum = 0
            for table in data:
                warnnum += 1
                embed.add_field(
                    name=f"Warning #{warnnum}", value=f"**Reason:** {table[0]} | **Date:** <t:{int(table[1])}:F>")
            await ctx.respond(embed=embed)
        else:
            embed = discord.Embed(
                colour=0x6B74C7,
                title=f"No warnings for {member.name}"
            )
            await ctx.respond(embed=embed)
    await bot.db.commit()


@bot.slash_command(name="serverinfo", description="Show's information about the server")
async def serverinfo(ctx):
    roles = len(ctx.guild.roles)
    em = discord.Embed(
        colour=0x6B74C7
    )
    em.add_field(name="Guild Name", value=f"{ctx.guild.name}", inline=False)
    em.add_field(name="Members", value=ctx.guild.member_count, inline=False)
    em.add_field(name="Verification Level", value=str(
        ctx.guild.verification_level), inline=False)
    em.add_field(name="Highest Role", value=ctx.guild.roles[-2], inline=False)
    em.add_field(name="Roles", value=str(roles), inline=False)
    em.add_field(name="Guild Owner",
                 value=f"<@{ctx.guild.owner_id}>", inline=False)
    em.set_footer(text=ctx.guild.id)
    await ctx.respond(embed=em)


@bot.slash_command(name="membercount", description="View server's member count")
async def membercount(ctx):
    embed = discord.Embed(
        description=f"Membercount: {ctx.guild.member_count}",
        colour=0x6B74C7
    )
    embed.set_author(name=f"{ctx.guild.name}")
    embed.set_footer(text=ctx.guild.id)
    await ctx.respond(embed=embed)


@bot.slash_command(name="secret", description="Try it out for yourself")
async def secret(ctx):
    await ctx.respond("https://tenor.com/view/rick-ashtley-never-gonna-give-up-rick-roll-gif-4819894")


@bot.slash_command(name="help", description="Help Command")
async def _help(ctx):
    embed = discord.Embed(
        title="PurpBot Help",
        color=0x6B74C7
    )
    embed.add_field(name="Moderation",
                    value="`/ban`, `/kick`, `/warn`, `/unwarn`, `/timeout`, `/purge`, `/addrole`, `/removerole`", inline=False)
    embed.add_field(
        name="Utility", value="`/hug`, `/secret`, `/send`, `/embed`, `/poll`, `/vote`, `/reactionroles`, `/userinfo`, `/calc`, `/search`, `/embwebhook`", inline=False)
    embed.add_field(name="Information",
                    value="`/ping`, `/warns`, `/serverinfo`, `/membercount`, `/guildcount`, `/invite`", inline=False)
    embed.add_field(name="Webhooks",
                    value="`/embwebhook`, `/msgwebhook`", inline=False)
    embed.add_field(name="Tickets",
                    value="`/ticket-config", inline=False)
    await ctx.respond(embed=embed)


@bot.slash_command(name="info", description="Shows information about the bot")
async def info(ctx):
    embed = discord.Embed(
        title="Information",
        description="PurpBot is a Discord bot created in pycord. It's a moderation and utility bot to make your server better and easier to moderate. It has tons of features for you to use\n- Use this following command for all the commands and how to use them: `help`\n\n**Developers** - <@!985809728624005130> & <@!839514280251359292>\n**Support Server** - https://discord.gg/NqZuBvtrEJ",
        color=0x6B74C7
    )
    embed.add_field(name="Version:", value="v2.4")
    await ctx.respond(embed=embed)


@bot.slash_command(name="send", description="Make the bot say anything you want")
async def send(ctx, messagecontent: Option(str, description="What the bot should say", required=True)):
    await ctx.respond(f"{messagecontent}")


@bot.slash_command(name="embed", description="Customize your embed")
async def embed(ctx, edescription: Option(str, description="The embed's description", required=True), etitle: Option(str="** **", description="The embed's title", required=True)):
    embed = discord.Embed(
        title=f"{etitle}",
        description=f"{edescription}",
        color=0x6B74C7
    )
    await ctx.respond(embed=embed)


@bot.slash_command(name="invite", description="Invite the bot")
async def invite(ctx):
    embed = discord.Embed(
        description="Invite me [here](https://discord.com/api/oauth2/authorize?client_id=849823707429994517&permissions=274877991936&scope=applications.commands%20bot)",
        color=0x6B74C7
    )
    await ctx.respond(embed=embed)


@bot.slash_command(name="timeout", description="Puts a member in timeout")
async def timeout(self, ctx, member: Option(discord.Member), minutes: Option(int)):
    """Apply a timeout to a member"""

    duration = datetime.timedelta(minutes=minutes)
    # timeout for the amount of time given, then remove timeout
    await member.timeout_for(duration)
    await ctx.reply(f"Member timed out for {minutes} minutes.")


@bot.slash_command(name="purge", description="Delete a certain amount of messages")
@commands.has_permissions(manage_messages=True)
@commands.cooldown(1, 5, commands.BucketType.user)
async def purge(ctx, messages: Option(int, description="The amount of messages you want to delete", required=True)):
    await ctx.defer()
    x = await ctx.channel.purge(limit=messages)
    await ctx.respond(f"Deleted {len(x)}", ephemeral=True)

# error handler


@purge.error
async def purgeerror(ctx, error):
    if isinstance(error, MissingPermissions):
        embed = discord.Embed(
            description="You are missing the `MANAGE_MESSAGES` permission",
            color=discord.Colour.red()
        )
        embed.set_author(
            name="Error", icon_url="https://cdn.discordapp.com/emojis/1055805812511080499.webp?size=96&quality=lossless")
        await ctx.respond(embed=embed)
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.respond(error)
    else:
        raise error


@bot.slash_command(name="addrole", description="Gives a user a role")
@commands.has_permissions(manage_guild=True)
async def addrole(ctx, role: Option(discord.Role, description="The role you want to add", required=True), member: Option(discord.Member, description="The member who'll get the role")):
    await member.add_roles(role)
    embed = discord.Embed(
        description=f"{member.mention} got {role.mention}",
        colour=0x2ECC71
    )
    embed.add_author(
        text="Success", icon_url="https://cdn.discordapp.com/emojis/1055805763651641355.webp?size=96&quality=lossless")
    await ctx.respond(embed=embed, ephemeral=False)

# error hadnler

@addrole.error
async def addroleerror(ctx, error):
    if isinstance(error, MissingPermissions):
        embed = discord.Embed(
            description="You are missing the `MANAGE_SERVER` permission",
            color=discord.Colour.red()
        )
        embed.set_author(
            name="Error", icon_url="https://cdn.discordapp.com/emojis/1055805812511080499.webp?size=96&quality=lossless")
        await ctx.respond(embed=embed, ephemeral=False)
    else:
        em = discord.Embed(
            description="An error occured. Please try again later or contact the developers at the support server",
            color=discord.Colour.red()
        )
        em.set_author(
            name="Error", icon_url="https://cdn.discordapp.com/emojis/1055805812511080499.webp?size=96&quality=lossless")
        await ctx.respond(embed=em, ephemeral=True)
        raise error
        
@bot.slash_command(name="removerole", description="Removes from a user a role")
@commands.has_permissions(manage_guild=True)
async def removerole(ctx, role: Option(discord.Role, description="The role you want to remove", required=True), member: Option(discord.Member, description="The member")):
    await member.add_roles(role)
    embed=discord.Embed(
        description=f"{member.mention} lost the {role.mention} role",
        colour=0x2ECC71
    )
    embed.add_author(text="Success", icon_url="https://cdn.discordapp.com/emojis/1055805763651641355.webp?size=96&quality=lossless")
    await ctx.respond(embed=embed, ephemeral=False)

# error hadnler

@removerole.error
async def removeroleerror(ctx, error):
    if isinstance(error, MissingPermissions):
        embed=discord.Embed(
            description="You are missing the `MANAGE_SERVER` permission",
            color=discord.Colour.red()
        )
        embed.set_author(name="Error", icon_url="https://cdn.discordapp.com/emojis/1055805812511080499.webp?size=96&quality=lossless")
        await ctx.respond(embed=embed, ephemeral=False)
    else:
        em=discord.Embed(
            description="An error occured. Please try again later or contact the developers at the support server",
            color=discord.Colour.red()
        )
        em.set_author(name="Error", icon_url="https://cdn.discordapp.com/emojis/1055805812511080499.webp?size=96&quality=lossless")
        await ctx.respond(embed=em, ephemeral=True)
        raise error
        
@bot.slash_command(name="emoji-info", description="Get info about an emoji")
async def emojiinfo(ctx, emoji: Option(discord.Emoji, description="The emoji", required=True)):
    if not emoji:
        await ctx.respond("Enter an emoji. Warning: this command works with custom emojis, not built-in ones")
        try:
            emoji = await emoji.guild.fetch_emoji(emoji.id)
        except discord.NotFound:
            return await ctx.respond("I couldn't find that emoji, it maybe is in another server")
        
        is_managed="Yes" if emoji.managed else "No"
        is_animated="Yes" if emoji.animated else "No"
        requires_colons="Yes" if emoji.require_colons else "No"
        creation_time=emoji.created_at.strftime("%I:%M %p %B %d, %Y")
        can_use_emoji="Everyone" if not emoji.roles else " ".join(role.name for role in emoji.roles)
        description=f'''
        > **Basic Info**
        **Name:** {emoji.name}
        **ID:** {emoji.id}
        **URL:** [Emoji Link]({emoji.url})
        **Author:** {emoji.user.mention} | {emoji.user.name}#{emoji.user.discriminator}
        **Created:** {creation_time}
        **Usable By:** {can_use_emoji}
            
        **Other Info**
        **Animated:** {is_animated}
        **Managed:** {is_managed}
        **Requires Colons:** {requires_colons}
        **Guild Name:** {emoji.guild.name}
        **Guild ID:** {emoji.guild.id}
        '''
        embed=discord.Embed(title=f"Info For {emoji.name}", description=description, colour=0x2ECC71)
        embed.set_thumbnail(url=emoji.url)
        await ctx.respond(embed=embed)
"""            
@bot.slash_command()
async def search(ctx, *, query):
    urls = [url for url in search(query, num_results=3)]
    message = "Search results:\n"
    for i in range(len(urls)):
        message += f"{i+1}. {urls[i]}\n"
    await ctx.respond(message)
"""

@bot.slash_command(name="poll", description="Creates a poll")
async def poll(ctx,
               question: Option(str),
               a: Option(str),
               b: Option(str)):
    embed = discord.Embed(title=question,
                          description=f"🅰️: {a}\n🅱️: {b}")
    await ctx.respond(embed=embed)
    msg = await ctx.interaction.original_message()
    await msg.add_reaction('🅰️')
    await msg.add_reaction('🅱️')


@bot.slash_command(name="avatar", description="Sends the avatar of a user")
async def avatar(ctx, member: Option(discord.Member, required=False)):
    if member == None:
        authoravatar = ctx.author.avatar.url
        embed = discord.Embed(color=0x6B74C7)
        embed.set_image(url=authoravatar)
    else:
        useravatar = member.avatar.url
        embed = discord.Embed(color=0x6B74C7)
        embed.set_image(url=useravatar)
    await ctx.respond(embed=embed)


@bot.slash_command(name="servericon", description="Sends the server icon")
async def servericon(ctx):
    servericon = ctx.guild.icon.url
    embed = discord.Embed(color=0x6B74C7)
    embed.set_image(url=servericon)
    await ctx.respond(embed=embed)


@bot.slash_command(name="reactionroles", description="Creates a reaction role")
async def reactionroles(ctx, role: Option(discord.Role), message_id: Option(discord.Message), emoji: Option(str)):
    await message_id.add_reaction(emoji)
    bot.reaction_roles.append(
        (role.id, message_id.id, str(emoji.encode("utf-8"))))
    async with aiofiles.open("reaction_roles.txt", mode="a") as file:
        emoji_utf = emoji.encode("utf-8")
        await file.write(f"{role.id} {message_id.id} {emoji_utf}\n")
        await ctx.respond("Reaction has been set.")


@bot.event
async def on_raw_reaction_add(payload):
    for role_id, message_id_id, emoji in bot.reaction_roles:
        if message_id_id == payload.message_id and emoji == str(payload.emoji.name.encode("utf-8")):
            await payload.member.add_roles(bot.get_guild(payload.guild_id).get_role(role_id))
            return


@bot.event
async def on_raw_reaction_remove(payload):
    for role_id, msg_id, emoji in bot.reaction_roles:
        if msg_id == payload.message_id and emoji == str(payload.emoji.name.encode("utf-8")):
            guild = bot.get_guild(payload.guild_id)
            await guild.get_member(payload.user_id).remove_roles(guild.get_role(role_id))
            return


@bot.slash_command(name="calc", description="Make the bot do some math!")
async def calculate(ctx, num1: Option(str), operation: Option(str, choices=["+", "-", "*", "/"]), num2: Option(str)):
    if operation not in ['+', '-', '*', '/']:
        await ctx.respond('Please type a valid operation type.')
    else:
        var = f'{num1} {operation} {num2}'
        await ctx.respond(f'{var} = {eval(var)}')


@bot.slash_command(name="userinfo", description="Get information on a user")
async def userinfo(ctx, member: Option(discord.Member, required=False)):
    if member is None:
        member = ctx.author
    date_format = "%a, %d %b %Y %I:%M %p"
    embed = discord.Embed(color=0x6B74C7, description=member.mention)
    embed.set_author(name=str(member), icon_url=member.avatar.url)
    embed.set_thumbnail(url=member.avatar.url)
    embed.add_field(
        name="Joined", value=member.joined_at.strftime(date_format))
    members = sorted(ctx.guild.members, key=lambda m: m.joined_at)
    embed.add_field(name="Join position", value=str(members.index(member)+1))
    embed.add_field(name="Registered",
                    value=member.created_at.strftime(date_format))
    if len(member.roles) > 1:
        role_string = ' '.join([r.mention for r in member.roles][1:])
        embed.add_field(name="Roles [{}]".format(
            len(member.roles)-1), value=role_string, inline=False)
    perm_string = ', '.join([str(p[0]).replace("_", " ").title()
                            for p in member.guild_permissions if p[1]])
    embed.add_field(name="Guild permissions", value=perm_string, inline=False)
    embed.set_footer(text='ID: ' + str(member.id))
    await ctx.respond(embed=embed)

@bot.slash_command(name="embwebhook", description="Sends an embed with a webhook.")
async def embwebhook(ctx, webhook: Option(str), wdescription: Option(str, description="The embed's description", required=True), wtitle: Option(str="** **", description="The embed's title", required=True)):
    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url(f"{webhook}", session=session)
        e = discord.Embed(title=f"{wtitle}",
                          description=f"{wdescription}",
                          color=0x6B74C7
                         )

        await webhook.send(embed=e)
        await ctx.respond("Embed sent with webhook!")
        
@bot.slash_command(name="msgwebhook", description="Sends a message with a webhook.")
async def msgwebhook(ctx, webhook: Option(str), msgcontent: Option(str, description="What the bot should say", required=True)):
    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url(f"{webhook}", session=session)
        await webhook.send(f"{msgcontent}")
        await ctx.respond("Message sent with webhook!")

@bot.slash_command(name="vote", description="Vote for our bot!")
async def vote(ctx):
    embed = discord.Embed(
        title="Vote for us!", description="Vote for us by clicking the button below!", color=0x6B74C7)
    await ctx.respond(embed=embed, view=VoteButtons())


class VoteButtons(View):
    def __init__(self):
        super().__init__()
        self.add_item(
            Button(
                label="Vote for Purpbot",
                url="https://top.gg/bot/849823707429994517/vote",
            )
        )
        
class CreateTicket(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label = "Create Ticket", style=discord.ButtonStyle.green, custom_id="create_a_ticket:green"
    )
    async def create_ticket(self, button: discord.ui.Button, interaction: discord.Interaction):
        overwrtes={
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True)
        }
        channel = await interaction.guild.create_text_channel(f"{interaction.user}-ticket", overwrites=overwrtes)
        msg = await interaction.response.send_message(f"Channel created! You can go here: {channel.mention}", ephemeral=True)
        etix = discord.Embed(
            title = "Ticket Created",
            description=f"Hey, {interaction.user} created a ticket | **Click one of the buttons below to change the settings**",
            color=0x6B74C7
        )
        await channel.send(embed=etix, view=TicketSettings())

class TicketSettings(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Close Ticket", style = discord.ButtonStyle.red, custom_id="ticket_settings:red"
    )
    async def close_ticket(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message("Closing ticket", ephemeral=False)
        await interaction.channel.delete()
        await interaction.user.send("Ticket closed.")
    
class Tickets(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.persistent_views_added = False
        
    async def on_ready(self):
        if not self.persistent_views_added:
            self.add_view(CreateTicket())
            self.persistent_views_added = True
            print("Views added")
            print("Tickts is ready")

@bot.slash_command(name="ticket-config", description="Configure Tickets.")
@commands.has_permissions(administrator=True)
async def ticket_config(ctx):
    econf = discord.Embed(title="Tickets", description="Click on the button below to create a ticket!", color=0x6B74C7)
    await ctx.respond("Tickets configured automatically!", ephemeral=True)
    await ctx.send(embed=econf, view=CreateTicket())

@bot.event
async def on_ready():
    print("PurpBot is online!")
    await bot.change_presence(activity=discord.Game("/info"))
    bot.db = await aiosqlite.connect("DataBases/warns.db")
    await asyncio.sleep(3)
    async with bot.db.cursor() as cursor:
        await cursor.execute("CREATE TABLE IF NOT EXISTS warns(user INTEGER, reason TEXT, time INTEGER, guild INTEGER)")

    async with aiofiles.open("reaction_roles.txt", mode="a") as temp:
        pass

    async with aiofiles.open("reaction_roles.txt", mode="r") as file:
        lines = await file.readlines()
        for line in lines:
            data = line.split(" ")
            bot.reaction_roles.append(
                (int(data[0]), int(data[1]), data[2].strip("\n")))
            
# bot.loop.create_task(initialize())
bot.run("")
# asyncio.run(bot.db.close())
