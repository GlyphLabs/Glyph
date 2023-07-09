from discord import Intents, Game, MemberCacheFlags, TextChannel
from discord.ext.commands import when_mentioned, Bot
from typing import Optional, List, Tuple
from asyncpg import connect, Connection
from src.db import Database
from logging import info, error, getLogger, basicConfig, INFO
from asyncio import sleep

basicConfig(format="[%(levelname)s] %(asctime)s: %(message)s", level=INFO)
getLogger("discord.py")


class PurpBot(Bot):
    __slots__ = (
        "reaction_roles",
        "conn",
        "database_url",
        "db",
        "scanned_messages_count",
    )

    def __init__(
        self,
        database_url: Optional[str] = None,
        test_mode: Optional[bool] = False,
    ):
        intents = Intents.none()
        intents.guilds = True
        intents.message_content = True
        intents.guild_messages = True

        self.conn: Optional[Connection]
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
        info("initialized bot")

        for cog in ("fun", "moderation", "utils", "ai", "config", "error", "levels"):
            try:
                info(
                    f'loaded cog {self.load_extension(f"src.cogs.{cog}", store=False)[0]}'
                )
            except Exception as e:
                error(f"failed to load cog {cog}: {e}")

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
                    self.conn: Connection = await connect(self.database_url)
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
            self.db = Database(self.conn)

        async with self.conn.transaction():
            await self.conn.execute(
                "CREATE TABLE IF NOT EXISTS warns(user_id BIGINT, reason TEXT, time BIGINT, guild BIGINT)"
            )
            await self.conn.execute(
                "CREATE TABLE IF NOT EXISTS guild_config (guild_id BIGINT PRIMARY KEY, ai_reports_channel BIGINT UNIQUE, logs_channel BIGINT UNIQUE, level_system BOOLEAN)"
            )
            await self.conn.execute(
                "CREATE TABLE IF NOT EXISTS levels (level INTEGER, xp INTEGER, user_id BIGINT, guild_id BIGINT)"
            )
        info("initialized database")
        return
