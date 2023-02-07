from src.bot import PurpBot
from discord.ext.commands import slash_command, Cog
from discord import (
    Embed,
    Option,
    ApplicationContext,
    Role,
    Webhook,
    Member,
    NotFound,
    Message,
    Emoji,
)
from src.views import VoteButtons
from aiohttp import ClientSession
from aiofiles import open as aopen


class Utils(Cog):
    def __init__(self, bot: PurpBot):
        self.bot = bot

    @slash_command(name="calc", description="Make the bot do some math!")
    async def calculate(
        self,
        ctx: ApplicationContext,
        num1: Option(str),
        operation: Option(str, choices=["+", "-", "*", "/"]),
        num2: Option(str),
    ):
        if operation not in ["+", "-", "*", "/"]:
            await ctx.respond("Please type a valid operation type.")
        else:
            var = f"{num1} {operation} {num2}"
            await ctx.respond(f"{var} = {eval(var)}")

    @slash_command(name="userinfo", description="Get information on a user")
    async def userinfo(
        self, ctx: ApplicationContext, member: Option(Member, required=False)
    ):
        if member is None:
            member = ctx.author
        date_format = "%a, %d %b %Y %I:%M %p"
        embed = Embed(color=0x6B74C7, description=member.mention)
        embed.set_author(name=str(member), icon_url=member.avatar.url)
        embed.set_thumbnail(url=member.avatar.url)
        embed.add_field(name="Joined", value=member.joined_at.strftime(date_format))
        members = sorted(ctx.guild.members, key=lambda m: m.joined_at)
        embed.add_field(name="Join position", value=str(members.index(member) + 1))
        embed.add_field(
            name="Registered", value=member.created_at.strftime(date_format)
        )
        if len(member.roles) > 1:
            role_string = " ".join([r.mention for r in member.roles][1:])
            embed.add_field(
                name="Roles [{}]".format(len(member.roles) - 1),
                value=role_string,
                inline=False,
            )
        perm_string = ", ".join(
            [
                str(p[0]).replace("_", " ").title()
                for p in member.guild_permissions
                if p[1]
            ]
        )
        embed.add_field(name="Guild permissions", value=perm_string, inline=False)
        embed.set_footer(text="ID: " + str(member.id))
        await ctx.respond(embed=embed)

    @slash_command(name="embwebhook", description="Sends an embed with a webhook.")
    async def embwebhook(
        self,
        ctx: ApplicationContext,
        webhook: Option(str),
        wdescription: Option(str, description="The embed's description", required=True),
        wtitle: Option(str="** **", description="The embed's title", required=True),
    ):
        async with ClientSession() as session:
            webhook = Webhook.from_url(f"{webhook}", session=session)
            e = Embed(title=f"{wtitle}", description=f"{wdescription}", color=0x6B74C7)

            await webhook.send(embed=e)
            await ctx.respond("Embed sent with webhook!")

    @slash_command(name="vote", description="Vote for our bot!")
    async def vote(self, ctx: ApplicationContext):
        print(type(ctx))
        embed = Embed(
            title="Vote for us!",
            description="Vote for us by clicking the button below!",
            color=0x6B74C7,
        )
        await ctx.respond(embed=embed, view=VoteButtons())

    @slash_command(name="serverinfo", description="Show's information about the server")
    async def serverinfo(self, ctx: ApplicationContext):
        roles = len(ctx.guild.roles)
        em = Embed(colour=0x6B74C7)
        em.add_field(name="Guild Name", value=f"{ctx.guild.name}", inline=False)
        em.add_field(name="Members", value=ctx.guild.member_count, inline=False)
        em.add_field(
            name="Verification Level",
            value=str(ctx.guild.verification_level),
            inline=False,
        )
        em.add_field(name="Highest Role", value=ctx.guild.roles[-2], inline=False)
        em.add_field(name="Roles", value=str(roles), inline=False)
        em.add_field(name="Guild Owner", value=f"<@{ctx.guild.owner_id}>", inline=False)
        em.set_thumbnail(url=ctx.guild.icon.url)
        em.set_footer(text=ctx.guild.id)
        await ctx.respond(embed=em)

    @slash_command(name="membercount", description="View server's member count")
    async def membercount(self, ctx: ApplicationContext):
        embed = Embed(
            description=f"Membercount: {ctx.guild.member_count}", colour=0x6B74C7
        )
        embed.set_author(name=f"{ctx.guild.name}")
        embed.set_footer(text=ctx.guild.id)
        await ctx.respond(embed=embed)

    @slash_command(name="info", description="Shows information about the bot")
    async def info(self, ctx: ApplicationContext):
        embed = Embed(
            title="Information",
            description="PurpBot is a Discord bot created in pycord. It's a moderation and utility bot to make your server better and easier to moderate. It has tons of features for you to use\n- Use this following command for all the commands and how to use them: `help`\n\n**Developers** - <@!985809728624005130> & <@!839514280251359292>\n**Support Server** - https://discord.gg/NqZuBvtrEJ",
            color=0x6B74C7,
        )
        embed.add_field(name="Version:", value="v2.4")
        await ctx.respond(embed=embed)

    @slash_command(name="send", description="Make the bot say anything you want")
    async def send(
        self,
        ctx: ApplicationContext,
        messagecontent: Option(
            str, description="What the bot should say", required=True
        ),
    ):
        await ctx.respond(f"{messagecontent}")

    @slash_command(name="embed", description="Customize your embed")
    async def embed(
        self,
        ctx: ApplicationContext,
        edescription: Option(str, description="The embed's description", required=True),
        etitle: Option(str="** **", description="The embed's title", required=True),
    ):
        embed = Embed(title=f"{etitle}", description=f"{edescription}", color=0x6B74C7)
        await ctx.respond(embed=embed)

    @slash_command(name="invite", description="Invite the bot")
    async def invite(self, ctx: ApplicationContext):
        embed = Embed(
            description="Invite me [here](https://discord.com/api/oauth2/authorize?client_id=849823707429994517&permissions=274877991936&scope=applications.commands%20bot)",
            color=0x6B74C7,
        )
        await ctx.respond(embed=embed)

    @slash_command(name="guildcount", description="shows bot's servers")
    async def guildcount(self, ctx: ApplicationContext):
        embed = Embed(
            description=f"PurpBot is in {len(self.bot.guilds)} servers!", color=0x6B74C7
        )
        await ctx.respond(embed=embed)

    @slash_command(name="ping", description="Check the bot's API latency | /ping")
    async def ping(self, ctx: ApplicationContext):
        await ctx.respond(f"API latency: {round(self.bot.latency * 1000)}ms")

    @slash_command(name="help", description="Help Command")
    async def _help(self, ctx: ApplicationContext):
        embed = Embed(title="PurpBot Help", color=0x6B74C7)
        embed.add_field(
            name="Moderation",
            value="`/ban`, `/kick`, `/warn`, `/unwarn`, `/timeout`, `/purge`, `/addrole`, `/removerole`",
            inline=False,
        )
        embed.add_field(
            name="Utility",
            value="`/hug`, `/secret`, `/send`, `/embed`, `/poll`, `/vote`, `/reactionroles`, `/userinfo`, `/calc`, `/search`",
            inline=False,
        )
        embed.add_field(
            name="Information",
            value="`/ping`, `/warns`, `/serverinfo`, `/membercount`, `/guildcount`, `/invite`",
            inline=False,
        )
        embed.add_field(
            name="Webhooks", value="`/embwebhook`, `/msgwebhook`", inline=False
        )
        embed.add_field(name="Tickets", value="`/ticket-config`", inline=False)
        await ctx.respond(embed=embed)

    @slash_command(name="secret", description="Try it out for yourself")
    async def secret(self, ctx: ApplicationContext):
        await ctx.respond(
            "https://tenor.com/view/rick-ashtley-never-gonna-give-up-rick-roll-gif-4819894"
        )

    @slash_command(name="emoji-info", description="Get info about an emoji")
    async def emojiinfo(
        self,
        ctx: ApplicationContext,
        emoji: Option(Emoji, description="The emoji", required=True),
    ):
        if not emoji:
            await ctx.respond(
                "Enter an emoji. Warning: this command works with custom emojis, not built-in ones"
            )
            try:
                emoji = await emoji.guild.fetch_emoji(emoji.id)
            except NotFound:
                return await ctx.respond(
                    "I couldn't find that emoji, it maybe is in another server"
                )

            is_managed = "Yes" if emoji.managed else "No"
            is_animated = "Yes" if emoji.animated else "No"
            requires_colons = "Yes" if emoji.require_colons else "No"
            creation_time = emoji.created_at.strftime("%I:%M %p %B %d, %Y")
            can_use_emoji = (
                "Everyone"
                if not emoji.roles
                else " ".join(role.name for role in emoji.roles)
            )
            description = f"""
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
            """
            embed = Embed(
                title=f"Info For {emoji.name}", description=description, colour=0x2ECC71
            )
            embed.set_thumbnail(url=emoji.url)
            await ctx.respond(embed=embed)

    @slash_command(name="msgwebhook", description="Sends a message with a webhook.")
    async def msgwebhook(
        self,
        ctx: ApplicationContext,
        webhook: Option(str),
        msgcontent: Option(str, description="What the bot should say", required=True),
    ):
        async with ClientSession() as session:
            webhook = Webhook.from_url(f"{webhook}", session=session)
            await webhook.send(f"{msgcontent}")
            await ctx.respond("Message sent with webhook!")

    @slash_command(name="avatar", description="Sends the avatar of a user")
    async def avatar(
        self, ctx: ApplicationContext, member: Option(Member, required=False)
    ):
        if not member:
            authoravatar = ctx.author.avatar.url
            embed = Embed(color=0x6B74C7)
            embed.set_image(url=authoravatar)
        else:
            useravatar = member.avatar.url
            embed = Embed(color=0x6B74C7)
            embed.set_image(url=useravatar)
        await ctx.respond(embed=embed)

    @slash_command(name="servericon", description="Sends the server icon")
    async def servericon(self, ctx: ApplicationContext):
        servericon = ctx.guild.icon_url
        embed = Embed(color=0x6B74C7)
        embed.set_image(url=servericon)
        await ctx.respond(embed=embed)

    @slash_command(name="reactionroles", description="Creates a reaction role")
    async def reactionroles(
        self,
        ctx: ApplicationContext,
        role: Option(Role),
        message_id: Option(Message),
        emoji: Option(str),
    ):
        await message_id.add_reaction(emoji)
        self.bot.reaction_roles.append(
            (role.id, message_id.id, str(emoji.encode("utf-8")))
        )
        async with aopen("reaction_roles.txt", mode="a") as file:
            emoji_utf = emoji.encode("utf-8")
            await file.write(f"{role.id} {message_id.id} {emoji_utf}\n")
            await ctx.respond("Reaction has been set.")

        @Cog.listener()
        async def on_raw_reaction_add(self, payload):
            for role_id, message_id_id, emoji in self.bot.reaction_roles:
                if message_id_id == payload.message_id and emoji == str(
                    payload.emoji.name.encode("utf-8")
                ):
                    await payload.member.add_roles(
                        self.bot.get_guild(payload.guild_id).get_role(role_id)
                    )
                    return

        @Cog.listener()
        async def on_raw_reaction_remove(self, payload):
            for role_id, msg_id, emoji in self.bot.reaction_roles:
                if msg_id == payload.message_id and emoji == str(
                    payload.emoji.name.encode("utf-8")
                ):
                    guild = self.bot.get_guild(payload.guild_id)
                    await guild.get_member(payload.user_id).remove_roles(
                        guild.get_role(role_id)
                    )
                    return


def setup(bot: PurpBot):
    bot.add_cog(Utils(bot))
