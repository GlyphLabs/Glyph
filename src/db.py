from __future__ import annotations
from cachetools import TTLCache
from ormsgpack import packb, unpackb
from typing import Optional
from asyncpg import Pool

class MsgPackMixin:
    def serialize(self):
        return packb(
            {
                column.name: getattr(self, column.name)
                for column in self.__table__.columns
                if not column.name.startswith("_")
            }
        )

    @classmethod
    def from_data(cls, data):
        return cls(**unpackb(data))

class Database:
    __slots__ = ("pool", "__cache")
    def __init__(self, pool: Pool):
        self.pool = pool
        self.__cache: TTLCache[int, bytes] = TTLCache(maxsize=100, ttl=600)
    
    async def get_guild_settings(self, guild_id: int) -> Optional[GuildSettings]:
        if guild_id in self.__cache:
            return GuildSettings.from_data(self.__cache[guild_id])
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                data = await conn.fetchrow(
                    "SELECT * FROM guild_config WHERE guild_id = $1",
                    guild_id
                )
                if data:
                    self.__cache[guild_id] = packb({k: v for k, v in data.items()})
                    return GuildSettings(**{k: v for k, v in data.items()})
                else:
                    await conn.execute(
                        "INSERT INTO guild_config (guild_id) VALUES ($1)",
                        guild_id
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
    def __init__(self, guild_id: int, ai_reports_channel: Optional[int] = None, logs_channel: Optional[int] = None):
        self.guild_id: int = guild_id
        self.ai_reports_channel: Optional[int] = ai_reports_channel
        self.logs_channel: Optional[int] = logs_channel

    def __repr__(self):
        return f"<GuildSettings(guild_id={self.guild_id})>"