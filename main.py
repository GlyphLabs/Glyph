from src.bot import Glyph
from dotenv import load_dotenv
from os import environ

load_dotenv()

bot = Glyph(
    database_url=environ.get("DATABASE_URL"),
    test_mode=bool(int(environ.get("TEST_MODE", 0))),
)
bot.remove_command("help")

bot.load_extension("jishaku")
bot.loop.run_until_complete(bot.init_db())
bot.run(environ.get("TOKEN"))
