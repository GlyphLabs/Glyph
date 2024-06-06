import logging
import coloredlogs
from asyncio import sleep
from typing import Optional

from asyncpg import create_pool, Pool
from discord import Intents, Game, MemberCacheFlags, HTTPException, Thread
from discord.abc import GuildChannel, PrivateChannel
from discord.ext.commands import when_mentioned, Bot

from src.db import Database

# omg colors
coloredlogs.install(
    fmt="[%(levelname)s] %(asctime)s: %(message)s",
    level="INFO",
    level_styles={
        "critical": {"color": "red", "bold": True},
        "error": {"color": "red"},
        "warning": {"color": "yellow"},
        "notice": {"color": "magenta"},
        "info": {"color": "green"},
        "debug": {"color": "blue"},
    },
    field_styles={
        "asctime": {"color": "cyan"},
        "levelname": {"color": "black", "bold": True},
        "message": {"color": "white"},
    },
)
logger = logging.getLogger("discord.py")


class Glyph(Bot):
    __slots__ = (
        "pool",
        "database_url",
        "db",
    )

    def __init__(
        self, database_url: Optional[str] = None, test_mode: Optional[bool] = False
    ):
        self.db: Database
        self.database_url = database_url

        super().__init__(
            command_prefix=when_mentioned,
            intents=Intents(guilds=True, message_content=True, guild_messages=True),
            debug_guilds=[1247673555462787143] if test_mode else None,
            member_cache_flags=MemberCacheFlags.none(),
            max_messages=None,
            chunk_guilds_at_startup=False,
        )

        logger.info("bot initialized")
        for cog in ("fun", "moderation", "utils", "ai", "config", "error", "events"):
            try:
                self.load_extension(f"src.cogs.{cog}")
                logger.info(f"loaded {cog.replace('src.cogs.', '')} cog")
            except Exception as e:
                logger.error(f"failed to load {cog.replace('src.cogs.', '')} cog: {e}")

    async def on_ready(self):
        """Runs when the bot is completely connected."""
        logger.info("glyph is online!")
        logger.info(f"logged in as {self.user}")
        logger.info(f"connected to {len(self.guilds)} guilds")
        logger.info(f"{len(self.all_commands)} commands across {len(self.cogs)} cogs")

        await self.change_presence(activity=Game("/info"))

    async def getch_channel(
        self, channel_id: int
    ) -> Optional[GuildChannel | PrivateChannel | Thread]:
        """Fetch a channel from cache or API."""
        if channel := self.get_channel(channel_id):
            return channel
        try:
            return await self.fetch_channel(channel_id)
        except HTTPException:
            return None

    async def init_db(self):
        """Initialize the database."""

        logger.info("connecting to database...")

        for i in range(3):
            try:
                self.pool: Pool = await create_pool(self.database_url) # type: ignore
                break
            except Exception as e:
                if i == 2:
                    logger.error(f"database connection error: {e}. exiting.")
                    continue
                logger.error(f"database connection error: {e}. retrying in 3 seconds.")
                await sleep(3)
        else:
            exit(1)
            
        logger.info("connected to database, validating tables...")
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS warns(
                        user_id BIGINT, 
                        reason TEXT, 
                        time BIGINT, 
                        guild BIGINT
                    )
                """)
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS leveling(
                        user_id BIGINT, 
                        xp BIGINT
                    )
                """)
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS guild_config (
                        guild_id BIGINT PRIMARY KEY, 
                        ai_reports_channel BIGINT UNIQUE, 
                        logs_channel BIGINT UNIQUE, 
                        leveling_enabled BOOLEAN DEFAULT FALSE
                    )
                """)
        self.db = Database(self.pool)
        logger.info("database initialized")
