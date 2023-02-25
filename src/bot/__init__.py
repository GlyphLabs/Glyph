from discord import Intents, Game, MemberCacheFlags
from discord.ext.commands import when_mentioned, Bot
from aiofiles import open as aopen
from statcord import StatcordClient
from typing import Optional, List, Tuple
from asyncpg import create_pool, Pool
from perspective.models import Perspective
from src.db import Database


class PurpBot(Bot):
    __slots__ = (
        "statcord_key",
        "statcord",
        "reaction_roles",
        "pool",
        "database_url",
        "db",
        "perspective",
        "scanned_messages_count",
    )

    def __init__(
        self,
        statcord_key: Optional[str],
        database_url: Optional[str] = None,
        perspective_key: Optional[str] = None,
    ):
        intents = Intents.default()
        intents.message_content = True
        self.pool: Optional[Pool]
        self.db: Database
        self.statcord_key = statcord_key
        self.reaction_roles: List[Tuple[int, int, int]] = []
        self.database_url = database_url
        self.scanned_messages_count: int = 0

        if perspective_key:
            self.perspective = Perspective(perspective_key)

        super().__init__(
            command_prefix=when_mentioned,
            intents=intents,
            test_guilds=[1050102412104437801],
            member_cache_flags=MemberCacheFlags.none(),
            max_messages=None,
        )

        self.statcord = StatcordClient(
            self, self.statcord_key, custom_1=lambda: self.scanned_messages_count
        )

    async def on_ready(self):
        print("PurpBot is online!")
        await self.change_presence(activity=Game("/info"))

    async def getch_channel(self, channel_id: int):
        return self.get_channel(channel_id) or await self.fetch_channel(channel_id)

    async def setup_bot(self):
        if self.database_url:
            self.pool: Pool = await create_pool(self.database_url)
            self.db = Database(self.pool)
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "CREATE TABLE IF NOT EXISTS warns(user_id BIGINT, reason TEXT, time BIGINT, guild BIGINT)"
                )
                await conn.execute(
                    "CREATE TABLE IF NOT EXISTS guild_config (guild_id BIGINT PRIMARY KEY, ai_reports_channel BIGINT UNIQUE, logs_channel BIGINT UNIQUE)"
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

        for cog in ("fun", "tickets", "moderation", "utils", "ai"):
            print(self.load_extension(f"src.cogs.{cog}"))
