# the core code of PurpBot. this file defines a `PurpBot` class that inherits from `discord.ext.commands.Bot`.
# it initialized some variables, sets up the database, and loads cogs

from discord import Intents, Game, MemberCacheFlags, Thread, HTTPException
from discord.ext.commands import when_mentioned, Bot
from discord.abc import GuildChannel, PrivateChannel
from typing import Optional, List, Tuple
from asyncpg import create_pool, Pool # type: ignore
from src.db import Database
from logging import info, error, getLogger, basicConfig, INFO
from asyncio import sleep

basicConfig(format="[%(levelname)s] %(asctime)s: %(message)s", level=INFO)
getLogger("discord.py")


class PurpBot(Bot):
    __slots__ = (
        "reaction_roles",
        "pool",
        "database_url",
        "db",
        "scanned_messages_count",
    )

    def __init__(
        self,
        database_url: Optional[str] = None,
        test_mode: Optional[bool] = False,
    ):
        # define bot intents.
        # we'll start from none and enable only the intents we need
        intents = Intents.none()
        intents.guilds = True
        intents.message_content = True
        intents.guild_messages = True

        # define some variables that will be used later
        self.pool: Optional[Pool]
        self.db: Database
        self.reaction_roles: List[Tuple[int, int, int]] = []
        self.database_url = database_url
        self.scanned_messages_count: int = 0

        # initialize the bot.
        # we don't want to cache any members
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

        # load cogs, code files with more features in them
        for cog in ("fun", "moderation", "utils", "ai", "config", "error"):
            try:
                # the load_extension part is actually doing the cog loading
                # type: ignore tells mypy to stop crying about it
                info(
                    f'loaded cog {self.load_extension(f"src.cogs.{cog}", store=False)[0]}'  # type: ignore
                )
            except Exception as e:
                error(f"failed to load cog {cog}: {e}")

    async def on_ready(self):
        """code to run when the bot is completely connected
        logs some information about the bot and connection
        """
        info("PurpBot is online!")
        info(f"logged in as {self.user}")
        info(f"can see {len(self.guilds)} guilds")
        info(f"{len(self.all_commands)} commands across {len(self.cogs)} cogs")

        # set the bot's activity to `Playing /info`
        await self.change_presence(activity=Game("/info"))

    async def getch_channel(
        self, channel_id: int
    ) -> Optional[GuildChannel | PrivateChannel | Thread]:
        """gets a channel from the bot's cache

        Args:
            channel_id (int): the id of the channel to get

        Returns:
            Optional[Channel]: the channel if found, None otherwise
        """
        if channel := self.get_channel(channel_id):
            return channel
        try:
            return await self.fetch_channel(channel_id)
        except HTTPException:
            return None

    async def init_db(self):
        """initializes the database

        Raises:
            e: the error preventing the bot from connecting to the database
        """
        if not self.database_url:
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

        retry = 1
        while True:
            try:
                self.pool: Pool = await create_pool(self.database_url)  # type: ignore
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
