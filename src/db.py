from __future__ import annotations
from cachetools import TTLCache
from msgpack import packb, unpackb
from typing import Optional
from asyncpg import Connection
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
    __slots__ = ("conn", "__cache")

    def __init__(self, conn: Connection):
        self.conn = conn
        self.__cache: TTLCache[int, bytes] = TTLCache(maxsize=100, ttl=600)

    async def create_warn(self, user_id: int, guild: int, reason: str) -> Warn:
        async with self.conn.transaction():
            await self.conn.execute(
                """INSERT INTO warns (user_id, reason, time, guild)
                    VALUES ($1, $2, $3, $4)""",
                user_id,
                reason,
                (timestamp := datetime.now().timestamp()),
                guild,
            )
            return Warn(user_id, reason, timestamp, guild)

    async def get_warns(self, user_id: int, guild: int) -> list[Warn]:
        async with self.conn.transaction():
            data = await self.conn.fetch(
                "SELECT * FROM warns WHERE user_id = $1 AND guild = $2",
                user_id,
                guild,
            )
            return [
                Warn.from_data(packb({k: v for k, v in warn.items()})) for warn in data
            ]

    async def get_guild_settings(self, guild_id: int) -> GuildSettings:
        if guild_id in self.__cache:
            return GuildSettings.from_data(self.__cache[guild_id])
        async with self.conn.transaction():
            data = await self.conn.fetchrow(
                "SELECT * FROM guild_config WHERE guild_id = $1", guild_id
            )
            if data:
                self.__cache[guild_id] = packb({k: v for k, v in data.items()})
                return GuildSettings(**{k: v for k, v in data.items()})
            else:
                await self.conn.execute(
                    "INSERT INTO guild_config (guild_id) VALUES ($1)", guild_id
                )
                return GuildSettings(guild_id)

    async def set_guild_settings(self, guild_id: int, settings: GuildSettings) -> None:
        async with self.conn.transaction():
            await self.conn.execute(
                """INSERT INTO guild_config
                    (guild_id, ai_reports_channel, logs_channel, level_system)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (guild_id) DO UPDATE
                    SET ai_reports_channel = $2, logs_channel = $3, level_system = $4""",
                guild_id,
                settings.ai_reports_channel,
                settings.logs_channel,
            )
            self.__cache[guild_id] = settings.serialize()

    async def get_level_stats(self, user_id: int, guild_id: int) -> LevelStats:
        async with self.conn.transaction():
            data = await self.conn.fetchrow(
                "SELECT * FROM level_stats WHERE user_id = $1 AND guild_id = $2",
                user_id,
                guild_id,
            )
            if data:
                return LevelStats(**{k: v for k, v in data.items()})
            else:
                await self.conn.execute("INSERT INTO levels (level, xp, user_id, guild_id) VALUES ($1, $2, $3, $4)", user_id, guild_id, 0, 0)
                return LevelStats(user_id, guild_id, 0, 0)
            
    async def set_level_stats(self, user_id: int, guild_id: int, stats: LevelStats) -> None:
        async with self.conn.transaction():
            await self.conn.execute(
                """INSERT INTO level_stats
                    (user_id, guild_id, level, xp)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (user_id, guild_id) DO UPDATE
                    SET level = $3, xp = $4""",
                user_id,
                guild_id,
                stats.level,
                stats.xp,
            )


class GuildSettings(MsgPackMixin):  # type: ignore
    __slots__ = ("guild_id", "ai_reports_channel", "logs_channel", "level_system")

    def __init__(
        self,
        guild_id: int,
        ai_reports_channel: Optional[int] = None,
        logs_channel: Optional[int] = None,
        level_system: bool = False,
    ):
        self.guild_id: int = guild_id
        self.ai_reports_channel: Optional[int] = ai_reports_channel
        self.logs_channel: Optional[int] = logs_channel
        self.level_system: bool = level_system

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

class LevelStats(MsgPackMixin):
    __slots__ = ("user_id", "guild_id", "xp", "level")

    def __init__(self, user_id: int, guild_id: int, xp: int, level: int):
        self.user_id: int = user_id
        self.guild_id: int = guild_id
        self.xp: int = xp
        self.level: int = level

    def __repr__(self):
        return f"<LevelStats(user_id={self.user_id}, guild_id={self.guild_id}, xp={self.xp}, level={self.level})>"