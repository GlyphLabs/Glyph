from src.bot import Glyph
from discord.ext.commands import slash_command, Cog
from discord import (
    Embed,
    Option,
    ApplicationContext,
    Webhook,
    Member,
)
from src.views import VoteButtons
from aiohttp import ClientSession
from discord.commands import SlashCommandGroup, option
from discord import Embed, ApplicationContext, Member, Colour, Role


class Utils(Cog):
    def __init__(self, bot: Glyph):
        self.bot = bot

    @slash_command(name="calc", description="Make the bot do some math!")
    @option(name="num1", description="First number", type=str, required=True)
    @option(name="operation", description="Calculation", type=str, choices=["+", "-", "*", "/"], required=True)
    @option(name="num2", description="Second number", type=str, required=True)
    async def calculate(
        self,
        ctx: ApplicationContext,
        num1: int,
        operation: str,
        num2: int,
    ):
        if operation not in ["+", "-", "*", "/"]:
            await ctx.respond("Please type a valid operation type.")
        else:
            var = f"{num1} {operation} {num2}"
            await ctx.respond(f"{var} = {eval(var)}")

    @slash_command(name="userinfo", description="Get information on a user")
    @option(name="member", description="The member you want get information", type=Member, required=False)
    async def userinfo(
        self, ctx: ApplicationContext, member: Member
    ):
        member = member if member else ctx.author # type: ignore
        date_format = "%a, %d %b %Y %I:%M %p"
        embed = Embed(color=0xffffff, description=member.mention)
        embed.set_author(name=str(member), icon_url=member.avatar.url) # type: ignore
        embed.set_thumbnail(url=member.avatar.url) # type: ignore
        embed.add_field(name="Joined", value=member.joined_at.strftime(date_format)) # type: ignore
        embed.add_field(
            name="Registered", value=member.created_at.strftime(date_format)
        )
        if len(member.roles) > 1:
            embed.add_field(
                name="Roles [{}]".format(len(member.roles) - 1),
                value=", ".join([r.mention for r in member.roles][1:]),
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
    @option(name="webhook_url", description="The webhook URL to use", type=str, required=True)
    @option(name="wdescription", description="The embed's description", type=str, required=True)
    @option(name="wtitle", description="The embed's title", type=str, required=True)
    async def embwebhook(
        self,
        ctx: ApplicationContext,
        webhook_url: str,
        wdescription: str,
        wtitle: str="** **",
    ):
        async with ClientSession() as session:
            webhook = Webhook.from_url(f"{webhook_url}", session=session) 
            e = Embed(title=f"{wtitle}", description=f"{wdescription}", color=0xffffff)

            await webhook.send(embed=e)
            await ctx.respond("Embed sent with webhook!")

    @slash_command(name="vote", description="Vote for our bot!")
    async def vote(self, ctx: ApplicationContext):
        print(type(ctx))
        embed = Embed(
            title="Vote for us!",
            description="Vote for us by clicking the button below!",
            color=0xffffff,
        )
        await ctx.respond(embed=embed, view=VoteButtons())

    @slash_command(name="serverinfo", description="Show's information about the server")
    async def serverinfo(self, ctx: ApplicationContext):
        roles = len(ctx.guild.roles)
        em = Embed(colour=0xffffff)
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
            description=f"Membercount: {ctx.guild.member_count}", colour=0xffffff
        )
        embed.set_author(name=f"{ctx.guild.name}")
        embed.set_footer(text=ctx.guild.id)
        await ctx.respond(embed=embed)

    @slash_command(name="info", description="Shows information about the bot")
    async def info(self, ctx: ApplicationContext):
        embed = Embed(
            title="Information",
            description="Glyph is a Discord bot created in pycord. It's a moderation and utility bot to make your server better and easier to moderate. It has tons of features for you to use\n- Use this following command for all the commands and how to use them: `help`\n\n**Developers** - <@!536644802595520534> & <@!825803913462284328>\n**Support Server** - https://discord.gg/mxR9xzprNG",
            color=0xffffff,
        )
        embed.add_field(name="Version:", value="v3.1.0")
        await ctx.respond(embed=embed)

    @slash_command(name="send", description="Make the bot say anything you want")
    @option(name="messagecontent", description="What the bot should say", type=str, required=True)
    async def send(
        self,
        ctx: ApplicationContext,
        messagecontent: str,
    ):
        await ctx.respond(f"{messagecontent}")

    @slash_command(name="embed", description="Customize your embed")
    @option(name="edescription", description="The embed's description", type=str, required=True)
    @option(name="etitle", description="The embed's title", type=str, required=True)
    async def embed(
        self,
        ctx: ApplicationContext,
        edescription: str,
        etitle: str,
    ):
        embed = Embed(title=f"{etitle}", description=f"{edescription}", color=0xffffff)
        await ctx.respond(embed=embed)

    @slash_command(name="invite", description="Invite the bot")
    async def invite(self, ctx: ApplicationContext):
        embed = Embed(
            description="Invite me [here](https://discord.com/api/oauth2/authorize?client_id=849823707429994517&permissions=274877991936&scope=applications.commands%20bot)",
            color=0xffffff,
        )
        await ctx.respond(embed=embed)

    @slash_command(name="guildcount", description="shows bot's servers")
    async def guildcount(self, ctx: ApplicationContext):
        embed = Embed(
            description=f"Glyph is in {len(self.bot.guilds)} servers!", color=0xffffff
        )
        await ctx.respond(embed=embed)

    @slash_command(name="ping", description="Check the bot's API latency | /ping")
    async def ping(self, ctx: ApplicationContext):
        await ctx.respond(f"API latency: {round(self.bot.latency * 1000)}ms")

    @slash_command(name="help", description="Help Command")
    async def _help(self, ctx: ApplicationContext):
        embed = Embed(title="Glyph Help", color=0xffffff)
        for name, cog in self.bot.cogs.items():
            if not cog.get_commands() or name.lower() == "jishaku":
                continue
            embed.add_field(
                name=name,
                value=", ".join(f"`{c.name}`" for c in cog.get_commands()),
                inline=False,
            )
        
        # if this is an admin who hasn't set up their server yet...
        if ctx.author.guild_permissions.manage_guild and not await self.bot.db.get_guild_settings(ctx.guild.id, auto_insert=False): # type: ignore
            embed.description = "**Hey, I noticed you haven't set up your server yet! Use `/setup` to get started!**"
        await ctx.respond(embed=embed)

    @slash_command(name="secret", description="Try it out for yourself")
    async def secret(self, ctx: ApplicationContext):
        await ctx.respond(
            "https://tenor.com/view/rick-ashtley-never-gonna-give-up-rick-roll-gif-4819894"
        )

    @slash_command(name="msgwebhook", description="Sends a message with a webhook.")
    @option(name="webhook_url", description="The webhook URL to use", type=str, required=True)
    @option(name="msgcontent", description="What the webhook should say", type=str, required=True)
    async def msgwebhook(
        self,
        ctx: ApplicationContext,
        webhook_url: str,
        msgcontent: str,
    ):
        async with ClientSession() as session:
            webhook = Webhook.from_url(f"{webhook_url}", session=session)
            await webhook.send(f"{msgcontent}")
            await ctx.respond("Message sent with webhook!")

    @slash_command(name="avatar", description="Sends the avatar of a user")
    @option(name="member", description="Member to get the avatar from", type=Member, required=False)
    async def avatar(
        self, ctx: ApplicationContext, member: str
    ):
        if not member:
            authoravatar = ctx.author.avatar.url #type: ignore
            embed = Embed(color=0xffffff)
            embed.set_image(url=authoravatar)
        else:
            useravatar = member.avatar.url #type: ignore
            embed = Embed(color=0xffffff)
            embed.set_image(url=useravatar)
        await ctx.respond(embed=embed)

    @slash_command(name="servericon", description="Sends the server icon")
    async def servericon(self, ctx: ApplicationContext):
        servericon = ctx.guild.icon.url
        embed = Embed(color=0xffffff)
        embed.set_image(url=servericon)
        await ctx.respond(embed=embed)


def setup(bot: Glyph):
    bot.add_cog(Utils(bot))
