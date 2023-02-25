from src.bot import PurpBot
from discord.ext.commands import Cog
from discord import Message, Embed
from discord.ext.tasks import loop
from collections import deque
from ormsgpack import packb, unpackb
from typing import Deque
from perspective import Attribute

class AiModeration(Cog):
    def __init__(self, bot: PurpBot):
        self.bot = bot
        self.messages: Deque[bytes] = deque()
        self.perspective = self.bot.perspective
        self.scan_messages.start()


    @Cog.listener()
    async def on_message(self, message: Message):
        if message.author.bot or not message.guild:
            return
        
        guild_settings = await self.bot.db.get_guild_settings(message.guild.id)
        if not guild_settings or not guild_settings.ai_reports_channel:
            return
        
        self.messages.append(
            packb(
                {
                    "channel_id": message.channel.id,
                    "content": message.content,
                    "message_id": message.id,
                    "reports_channel": guild_settings.ai_reports_channel,
                }
            )
        )


    @loop(seconds=1.1) # abide by perspective ratelimits
    async def scan_messages(self):
        if not self.messages:
            return

        msg = unpackb(self.messages.popleft())

        channel = await self.bot.getch_channel(msg["channel_id"])
        message = await channel.fetch_message(msg["message_id"])
        score = await self.perspective.score(message.content, [Attribute.toxicity])
        if score.toxicity > 0.8:
            reports_channel = await self.bot.getch_channel(msg["reports_channel"])
            embed = Embed(
                title="Message Flagged", description=f"Toxicity rating was **{round(score.toxicity*100)}%**.", color=0x6B74C7
            ).set_author(
                name=f"{message.author} ({message.author.id})", icon_url=message.author.display_avatar.url
            ).set_footer(
                text=f"Message ID: {message.id} • Author ID: {message.author.id}"
            ).add_field(
                name="Message", value=f"{message.content}\n[[Jump to message]({message.jump_url})]"
            )
            await reports_channel.send(embed=embed)


def setup(bot: PurpBot):
    bot.add_cog(AiModeration(bot))
