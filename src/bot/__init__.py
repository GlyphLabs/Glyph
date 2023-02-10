from discord import Intents, Game, MemberCacheFlags
from discord.ext.commands import when_mentioned, Bot
from src.views import CreateTicket, TicketSettings
import aiosqlite
from aiofiles import open as aopen
from statcord import StatcordClient
from typing import Optional, List, Tuple


class PurpBot(Bot):
    def __init__(self, statcord_key: Optional[str], *args, **kwargs):
        intents = Intents.default()
        # intents.members = True
        intents.message_content = True
        self.statcord_key = statcord_key
        self.reaction_roles: List[Tuple[int, int, int]] = []
        super().__init__(
            command_prefix=when_mentioned,
            intents=intents,
            test_guilds=[1050102412104437801],
            member_cache_flags=MemberCacheFlags.none(),
            max_messages=None,
            *args,
            **kwargs,
        )
        self.statcord = StatcordClient(self, self.statcord_key)

    async def on_ready(self):
        print("PurpBot is online!")
        await self.change_presence(activity=Game("/info"))
        self.add_view(CreateTicket())
        self.add_view(TicketSettings())

    async def setup_bot(self):
        self.db = await aiosqlite.connect("warns.db")
        async with self.db.cursor() as cursor:
            await cursor.execute(
                "CREATE TABLE IF NOT EXISTS warns(user INTEGER, reason TEXT, time INTEGER, guild INTEGER)"
            )

        async with aopen("reaction_roles.txt", mode="a"):
            pass

        async with aopen("reaction_roles.txt", mode="r") as reaction_roles_file:
            lines = await reaction_roles_file.readlines()
            for line in lines:
                data = line.split(" ")
                self.reaction_roles.append(
                    (int(data[0]), int(data[1]), data[2].strip("\n"))
                )

        for cog in ("fun", "tickets", "moderation", "utils"):
            print(self.load_extension(f"src.cogs.{cog}"))
