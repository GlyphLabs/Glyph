import discord
from discord.ext.commands import Bot
from src.views import CreateTicket, TicketSettings
import aiosqlite
from aiofiles import open as aopen

class PurpBot(Bot):
    def __init__(self, *args, **kwargs):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        self.reaction_roles = []
        super().__init__(intents=intents, test_guilds=[1050102412104437801], *args, **kwargs)

    async def on_ready(self):
        print("PurpBot is online!")
        await self.change_presence(activity=discord.Game("/info"))
        self.add_view(CreateTicket())
        self.add_view(TicketSettings())
        self.db = await aiosqlite.connect("DataBases/warns.db")
        # await sleep(3)
        async with self.db.cursor() as cursor:
            await cursor.execute("CREATE TABLE IF NOT EXISTS warns(user INTEGER, reason TEXT, time INTEGER, guild INTEGER)")

        async with aopen("reaction_roles.txt", mode="a"):
            pass

        async with aopen("reaction_roles.txt", mode="r") as reaction_roles_file:
            lines = await reaction_roles_file.readlines()
            for line in lines:
                data = line.split(" ")
                self.reaction_roles.append(
                    (int(data[0]), int(data[1]), data[2].strip("\n")))
