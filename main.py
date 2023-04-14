import discord
from discord.commands import Option
from discord.ext.commands import MissingPermissions
from src.bot import PurpBot
from dotenv import load_dotenv
from os import environ

load_dotenv()

bot = PurpBot(
    statcord_key=environ.get("STATCORD_KEY"),
    database_url=environ.get("DATABASE_URL"),
    # perspective_key=environ.get("PERSPECTIVE_KEY"),
    test_mode=bool(int(environ.get("TEST_MODE", 0))),
)
bot.remove_command("help")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, MissingPermissions):
        embed = discord.Embed(
            description="Missing required permissions", color=discord.Colour.red()
        )
        embed.set_author(
            name="Error",
            icon_url="https://cdn.discordapp.com/emojis/1055805812511080499.webp?size=96&quality=lossless",
        )
        await ctx.reply(embed=embed)


@bot.event
async def on_message(message):
    if message.content == bot.user.mention:
        embed = discord.Embed(
            description="My default prefix is: `/` (Slash Commands)", color=0x6B74C7
        )
        await message.channel.send(embed=embed)
    await bot.process_commands(message)


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
async def poll(ctx, question: Option(str), a: Option(str), b: Option(str)):
    embed = discord.Embed(title=question, description=f"🅰️: {a}\n🅱️: {b}")
    await ctx.respond(embed=embed)
    msg = await ctx.interaction.original_response()
    await msg.add_reaction("🅰️")
    await msg.add_reaction("🅱️")


bot.load_extension("jishaku")
bot.loop.create_task(bot.setup_bot())
bot.run(environ.get("TOKEN"))
# asyncio.run(bot.db.close())
