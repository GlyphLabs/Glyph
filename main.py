from src.bot import Glyph
from dotenv import load_dotenv
from os import environ
from tomllib import loads

with open("pyproject.toml") as f:
    pyproject = loads(str(f.read()))

load_dotenv()

bot = Glyph(
    database_url=environ.get("DATABASE_URL"),
    test_mode=bool(int(environ.get("TEST_MODE", 0))),
    emoji_guild=int(environ.get("EMOJI_GUILD")) if environ.get("EMOJI_GUILD") else None,
    version=pyproject["project"]["version"],
)
bot.remove_command("help")

bot.load_extension("jishaku")
bot.loop.run_until_complete(bot.init_db())
bot.run(environ.get("TOKEN"))
