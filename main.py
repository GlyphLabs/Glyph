from discord.embeds import Embed
from discord.colour import Colour
from discord.commands.options import Option
from discord.ext.commands import MissingPermissions, Context
from discord.message import Message
from src.bot import Glyph
from dotenv import load_dotenv
from os import environ

load_dotenv()

bot = Glyph(
    database_url=environ.get("DATABASE_URL"),
    test_mode=bool(int(environ.get("TEST_MODE", 0))),
)
bot.remove_command("help")


@bot.event
async def on_command_error(ctx: Context, error: Exception):
    """central error handling for commands

    Args:
        ctx (Context): the information about the execution of the command
        error (Exception): the error itself
    """    
    if isinstance(error, MissingPermissions):
        embed = Embed(
            description="Missing required permissions", color=Colour.red()
        )
        embed.set_author(
            name="Error",
            icon_url="https://cdn.discordapp.com/emojis/1055805812511080499.webp?size=96&quality=lossless",
        )
        await ctx.reply(embed=embed)


@bot.event
async def on_message(message: Message):
    """what to do when a message is sent

    Args:
        message (discord.Message): the message itself
    """    
    if message.content == bot.user.mention: # type: ignore
        embed = Embed(
            description="My default prefix is: `/` (Slash Commands)", color=0xffffff
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
    embed = Embed(title=question, description=f"🅰️: {a}\n🅱️: {b}")
    await ctx.respond(embed=embed)
    msg = await ctx.interaction.original_response()
    await msg.add_reaction("🅰️")
    await msg.add_reaction("🅱️")


bot.load_extension("jishaku")
bot.loop.run_until_complete(bot.init_db())
bot.run(environ.get("TOKEN"))
