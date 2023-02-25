from __future__ import annotations
from cachetools import TTLCache
from ormsgpack import packb, unpackb
from typing import Optional
from asyncpg import Pool
from datetime import datetime


class MsgPackMixin:
    def serialize(self):
        return packb(self.as_dict())

    def as_dict(self):
        return {
            attr: getattr(self, attr)
            for attr in dir(self)
            if not attr.startswith('__') and not callable(getattr(self,attr))
        }

    @classmethod
    def from_data(cls, data):
        return cls(**unpackb(data))


class Database:
    __slots__ = ("pool", "__cache")

    def __init__(self, pool: Pool):
        self.pool = pool
        self.__cache: TTLCache[int, bytes] = TTLCache(maxsize=100, ttl=600)

    async def create_warn(self, user_id: int, guild: int, reason: str) -> Warn:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    """INSERT INTO warns (user_id, reason, time, guild)
                    VALUES ($1, $2, $3, $4)""",
                    user_id,
                    reason,
                    (timestamp := datetime.now().timestamp()),
                    guild,
                )
                return Warn(user_id, reason, timestamp, guild)

    async def get_warns(self, user_id: int, guild: int) -> list[Warn]:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                data = await conn.fetch(
                    "SELECT * FROM warns WHERE user_id = $1 AND guild = $2",
                    user_id,
                    guild,
                )
                return [
                    Warn.from_data(packb({k: v for k, v in warn.items()}))
                    for warn in data
                ]

    async def get_guild_settings(self, guild_id: int) -> Optional[GuildSettings]:
        if guild_id in self.__cache:
            return GuildSettings.from_data(self.__cache[guild_id])
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                data = await conn.fetchrow(
                    "SELECT * FROM guild_config WHERE guild_id = $1", guild_id
                )
                if data:
                    self.__cache[guild_id] = packb({k: v for k, v in data.items()})
                    return GuildSettings(**{k: v for k, v in data.items()})
                else:
                    await conn.execute(
                        "INSERT INTO guild_config (guild_id) VALUES ($1)", guild_id
                    )
                    return GuildSettings(guild_id)

    async def set_guild_settings(self, guild_id: int, settings: GuildSettings) -> None:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    """INSERT INTO guild_config
                    (guild_id, ai_reports_channel, logs_channel)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (guild_id) DO UPDATE
                    SET ai_reports_channel = $2, logs_channel = $3""",
                    guild_id,
                    settings.ai_reports_channel,
                    settings.logs_channel,
                )
                self.__cache[guild_id] = settings.serialize()


class GuildSettings(MsgPackMixin):  # type: ignore
    __slots__ = ("guild_id", "ai_reports_channel", "logs_channel")

    def __init__(
        self,
        guild_id: int,
        ai_reports_channel: Optional[int] = None,
        logs_channel: Optional[int] = None,
    ):
        self.guild_id: int = guild_id
        self.ai_reports_channel: Optional[int] = ai_reports_channel
        self.logs_channel: Optional[int] = logs_channel

    def __repr__(self):
        return f"<GuildSettings(guild_id={self.guild_id})>"


class Warn(MsgPackMixin):  # type: ignore
    __slots__ = ("user_id", "reason", "time", "guild")

    def __init__(self, user_id: int, reason: str, time: float, guild: int):
        self.user_id: int = user_id
        self.reason: str = reason
        self.time: float = time
        self.guild: int = guild

    def __repr__(self):
        return f"<Warn(user_id={self.user_id}, reason={self.reason}, time={self.time}, guild={self.guild})>"
