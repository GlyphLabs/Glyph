import logging
import coloredlogs
from asyncio import sleep
from typing import Optional, List, Tuple

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
        'critical': {'color': 'red', 'bold': True},
        'error': {'color': 'red'},
        'warning': {'color': 'yellow'},
        'notice': {'color': 'magenta'},
        'info': {'color': 'green'},
        'debug': {'color': 'blue'},
    },
    field_styles={
        'asctime': {'color': 'cyan'},
        'levelname': {'color': 'black', 'bold': True},
        'message': {'color': 'white'},
    }
)
logger = logging.getLogger("discord.py")


class Glyph(Bot):
    __slots__ = (
        "reaction_roles",
        "pool",
        "database_url",
        "db",
        "scanned_messages_count",
    )

    def __init__(self, database_url: Optional[str] = None, test_mode: Optional[bool] = False):
        intents = Intents.none()
        intents.guilds = True
        intents.message_content = True
        intents.guild_messages = True

        self.db: Database
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

        logger.info("Bot initialized")

        self.load_all_cogs(["fun", "moderation", "utils", "ai", "config", "error"])

    def load_all_cogs(self, cogs: List[str]):
        """Load all specified cogs."""
        for cog in cogs:
            try:
                self.load_extension(f"src.cogs.{cog}")
                logger.info(f"Loaded cog: {cog}")
            except Exception as e:
                logger.error(f"Failed to load cog {cog}: {e}")

    async def on_ready(self):
        """Runs when the bot is completely connected."""
        logger.info("Glyph is online!")
        logger.info(f"Logged in as {self.user}")
        logger.info(f"Connected to {len(self.guilds)} guilds")
        logger.info(f"{len(self.all_commands)} commands across {len(self.cogs)} cogs")

        await self.change_presence(activity=Game("/info"))

    async def getch_channel(self, channel_id: int) -> Optional[GuildChannel | PrivateChannel | Thread]:
        """Fetch a channel from cache or API."""
        if channel := self.get_channel(channel_id):
            return channel
        try:
            return await self.fetch_channel(channel_id)
        except HTTPException:
            return None

    async def init_db(self):
        """Initialize the database."""
        retry = 1
        max_retries = 3

        while retry <= max_retries:
            try:
                self.pool: Pool = await create_pool(self.database_url)
                break
            except Exception as e:
                if retry >= max_retries:
                    logger.error(f"Database connection error: {e}. Exiting.")
                    await self.wait_until_ready()
                    await self.close()
                    raise e
                retry += 1
                logger.error(f"Database connection error: {e}. Retrying in 3 seconds.")
                await sleep(3)

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
        logger.info("Database initialized")
        self.db = Database(self.pool)
