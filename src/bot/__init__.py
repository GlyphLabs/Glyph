from discord import Intents, Game, MemberCacheFlags
from discord.ext.commands import when_mentioned, Bot
from aiofiles import open as aopen
from statcord import StatcordClient
from typing import Optional, List, Tuple
from asyncpg import create_pool, Pool
from perspective.models import Perspective
from src.db import Database
from logging import info, error, getLogger, basicConfig, INFO
basicConfig(format='[%(levelname)s] %(asctime)s: %(message)s', level=INFO)
getLogger("discord.py")

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
        test_mode: Optional[bool] = False,
    ):
        intents = Intents.default()
        intents.message_content = True
        intents.members = True

        self.pool: Optional[Pool]
        self.db: Database
        self.statcord_key = statcord_key
        self.reaction_roles: List[Tuple[int, int, int]] = []
        self.database_url = database_url
        self.scanned_messages_count: int = 0

        if perspective_key:
            self.perspective = Perspective(perspective_key)

        member_cache_flags = MemberCacheFlags.none()
        member_cache_flags.interaction = True
        member_cache_flags.joined = True
        super().__init__(
            command_prefix=when_mentioned,
            intents=intents,
            debug_guilds=[1050102412104437801] if test_mode else None,
            member_cache_flags=member_cache_flags,
            max_messages=None,
        )
        info("initialized bot")

        for cog in ("fun", "moderation", "utils", "ai", "config", "error"):
            try:
                info(
                    f'loaded cog {self.load_extension(f"src.cogs.{cog}", store=False)[0]}'
                )
            except Exception as e:
                error(f"failed to load cog {cog}: {e}")

        self.statcord = StatcordClient(
            self, self.statcord_key, custom_1=lambda: self.scanned_messages_count
        )

    async def on_ready(self):
        info("PurpBot is online!")
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
        info("initialized database")

        async with aopen("reaction_roles.txt", mode="a"):
            pass

        async with aopen("reaction_roles.txt", mode="r") as reaction_roles_file:
            lines = await reaction_roles_file.readlines()
            for line in lines:
                data = line.split(" ")
                self.reaction_roles.append(
                    (int(data[0]), int(data[1]), data[2].strip("\n"))
                )
