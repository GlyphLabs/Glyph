from __future__ import annotations
from cachetools import LFUCache
from msgpack import packb, unpackb # type: ignore
from typing import Optional
from asyncpg import Pool # type: ignore
from datetime import datetime


class MsgPackMixin:
    def serialize(self):
        return packb(self.as_dict())

    def as_dict(self):
        return {
            attr: getattr(self, attr)
            for attr in dir(self)
            if not attr.startswith("__") and not callable(getattr(self, attr))
        }

    @classmethod
    def from_data(cls, data):
        return cls(**unpackb(data))


class Database:
    __slots__ = ("pool", "__cache")

    def __init__(self, pool: Pool):
        self.pool = pool
        self.__cache: LFUCache[int, bytes] = LFUCache(maxsize=100)

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
                    (guild_id, ai_reports_channel, logs_channel, leveling_enabled)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (guild_id) DO UPDATE
                    SET ai_reports_channel = $2, logs_channel = $3, leveling_enabled = $4""",
                    guild_id,
                    settings.ai_reports_channel,
                    settings.logs_channel,
                    settings.leveling_enabled,
                )
                self.__cache[guild_id] = settings.serialize()
    
    async def get_xp(self, user_id: int) -> int:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                data = await conn.fetchrow(
                    "SELECT xp FROM leveling WHERE user_id = $1", user_id
                )
                return data["xp"] if data else 0
    
    async def add_xp(self, user_id: int, xp: int) -> int:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    """INSERT INTO leveling (user_id, xp)
                    VALUES ($1, $2)
                    ON CONFLICT (user_id) DO UPDATE
                    SET xp = leveling.xp + $2""",
                    user_id,
                    xp,
                )
                return await self.get_xp(user_id)

    async def set_xp(self, user_id: int, xp: int) -> int:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "INSERT INTO leveling (user_id, xp) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET xp = $2",
                    user_id,
                    xp,
                )
                return xp


class GuildSettings(MsgPackMixin):
    __slots__ = ("guild_id", "ai_reports_channel", "logs_channel", "leveling_enabled")

    def __init__(
        self,
        guild_id: int,
        ai_reports_channel: Optional[int] = None,
        logs_channel: Optional[int] = None,
        leveling_enabled: bool = False,
        **kwargs,  # just collapse extra data instead of screaming and crying
    ):
        self.guild_id: int = guild_id
        self.ai_reports_channel: Optional[int] = ai_reports_channel
        self.logs_channel: Optional[int] = logs_channel
        self.leveling_enabled: bool = leveling_enabled

    def __repr__(self):
        return f"<GuildSettings(guild_id={self.guild_id})>"


class Warn(MsgPackMixin):
    __slots__ = ("user_id", "reason", "time", "guild")

    def __init__(self, user_id: int, reason: str, time: float, guild: int):
        self.user_id: int = user_id
        self.reason: str = reason
        self.time: float = time
        self.guild: int = guild

    def __repr__(self):
        return f"<Warn(user_id={self.user_id}, reason={self.reason}, time={self.time}, guild={self.guild})>"

class Leveling(MsgPackMixin):
    __slots__ = ("user_id", "xp")

    def __init__(self, user_id: int, xp: int):
        self.user_id: int = user_id
        self.xp: int = xp


    def __repr__(self):
        return f"<Leveling(user_id={self.user_id}, xp={self.xp})>"