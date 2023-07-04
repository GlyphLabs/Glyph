from discord import Intents, Game, MemberCacheFlags, TextChannel
from discord.ext.commands import when_mentioned, Bot
from statcord import StatcordClient
from typing import Optional, List, Tuple
from asyncpg import create_pool, Pool
from src.db import Database
from logging import info, error, getLogger, basicConfig, INFO
from asyncio import sleep

basicConfig(format="[%(levelname)s] %(asctime)s: %(message)s", level=INFO)
getLogger("discord.py")


class PurpBot(Bot):
    __slots__ = (
        "statcord_key",
        "statcord",
        "reaction_roles",
        "pool",
        "database_url",
        "db",
        "scanned_messages_count",
    )

    def __init__(
        self,
        statcord_key: Optional[str],
        database_url: Optional[str] = None,
        test_mode: Optional[bool] = False,
    ):
        intents = Intents.none()
        intents.guilds = True
        intents.message_content = True
        intents.guild_messages = True

        self.pool: Optional[Pool]
        self.db: Database
        self.statcord_key = statcord_key
        self.reaction_roles: List[Tuple[int, int, int]] = []
        self.database_url = database_url
        self.scanned_messages_count: int = 0

        member_cache_flags = MemberCacheFlags.none()
        super().__init__(
            command_prefix=when_mentioned,
            intents=intents,
            debug_guilds=[1050102412104437801] if test_mode else None,
            member_cache_flags=member_cache_flags,
            max_messages=None,
            chunk_guilds_at_startup=False,
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

    async def getch_channel(self, channel_id: int) -> TextChannel:
        if channel := self.get_channel(channel_id):
            return channel
        else:
            try:
                return await self.fetch_channel(channel_id)
            except Exception:
                return None

    async def setup_bot(self):
        if self.database_url:
            retry = 1
            while True:
                try:
                    self.pool: Pool = await create_pool(self.database_url)
                    break
                except Exception as e:
                    if retry >= 3:
                        error("failed to connect to database, exiting")
                        await self.wait_until_ready()
                        await self.close()
                        raise e
                        # exit without raising error

                    retry += 1
                    info("failed to connect to database, retrying in 3 seconds")
                    await sleep(3)
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
        return
