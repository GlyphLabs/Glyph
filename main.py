from discord.embeds import Embed
from discord.colour import Colour
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
        embed = Embed(description="Missing required permissions", color=Colour.red())
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
    if message.content == bot.user.mention:  # type: ignore
        embed = Embed(
            description="My default prefix is: `/` (Slash Commands)", color=0xFFFFFF
        )
        await message.channel.send(embed=embed)
    await bot.process_commands(message)


bot.load_extension("jishaku")
bot.loop.run_until_complete(bot.init_db())
bot.run(environ.get("TOKEN"))
