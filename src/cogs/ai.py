from src.bot import PurpBot
from discord.ext.commands import Cog
from discord import Message, Embed, ButtonStyle, Interaction
from discord.ui import View, Button
from discord.ext.tasks import loop
from collections import deque
from ormsgpack import packb, unpackb
from typing import Deque
from perspective import Attribute
from datetime import timedelta
from logging import getLogger
from dataclasses import dataclass
logger = getLogger(__name__)


@dataclass
class AiPartialMessage:
    guild_id: int
    channel_id: int
    content: str
    message_id: int
    reports_channel: int
    author_id: int


class AiModeration(Cog):
    def __init__(self, bot: PurpBot):
        self.bot = bot
        self.messages: Deque[bytes] = deque()
        self.perspective = self.bot.perspective
        self.scan_messages.start()

    def build_view(self, message: AiPartialMessage, disabled: bool = False) -> View:
        delete_button: Button = Button(
            style=ButtonStyle.gray,
            label="Delete",
            custom_id=f"flagged_message_options:delete-{message.channel_id}-{message.message_id}",
            disabled=disabled,
        )
        timeout_button: Button = Button(
            style=ButtonStyle.gray,
            label="Timeout [1d]",
            custom_id=f"flagged_message_options:timeout-{message.channel_id}-{message.message_id}",
            disabled=disabled,
        )
        kick_button: Button = Button(
            style=ButtonStyle.red,
            label="Kick",
            custom_id=f"flagged_message_options:kick-{message.channel_id}-{message.message_id}",
            disabled=disabled,
        )
        ban_button: Button = Button(
            style=ButtonStyle.red,
            label="Ban",
            custom_id=f"flagged_message_options:ban-{message.channel_id}-{message.message_id}",
            disabled=disabled,
        )
        jump_button: Button = Button(
            style=ButtonStyle.url,
            label="Jump to message",
            url=message.jump_url,
            disabled=disabled,
        )
        items = (jump_button, delete_button,
                 timeout_button, kick_button, ban_button)
        return View(*items, timeout=None)

    @Cog.listener()
    async def on_interaction(self, interaction: Interaction):
        if (
            not interaction.custom_id
            or not interaction.message
            or not interaction.custom_id.startswith("flagged_message_options")
        ):
            return
        cleaned_id = interaction.custom_id.split(":")[1]
        action, msg_channel_id, msg_id = cleaned_id.split("-")
        channel = await self.bot.getch_channel(int(msg_channel_id))
        message = await channel.fetch_message(int(msg_id))
        if action == "delete":
            await message.delete()
            await interaction.response.send_message("Message deleted.", ephemeral=True)
        elif action == "timeout":
            await message.delete()
            author = await message.guild.fetch_member(message.author.id)
            await author.timeout_for(timedelta(days=1))
            await interaction.response.send_message(
                f"{message.author} has been timed out for 1 day.", ephemeral=True
            )
        elif action == "kick":
            await message.delete()
            await message.guild.kick(
                message.author.id,
                f"Flagged message by AI moderation. Kicked by {interaction.user}.",
            )
            await interaction.response.send_message(
                f"{message.author} has been kicked.", ephemeral=True
            )
        elif action == "ban":
            await message.delete()
            await message.guild.ban(message.author.id)
            await interaction.response.send_message(
                f"{message.author} has been banned.", ephemeral=True
            )
        await interaction.message.edit(
            embed=interaction.message.embeds[0],
            view=self.build_view(message, disabled=True),
        )

    @Cog.listener()
    async def on_message(self, message: Message):
        if message.author.bot or not message.guild:
            return

        if not message.content:
            return
        guild_settings = await self.bot.db.get_guild_settings(message.guild.id)
        if not guild_settings or not guild_settings.ai_reports_channel:
            return
        logger.debug(f"adding message {message.id} to scanning queue")
        self.messages.append(
            packb(
                {
                    "guild_id": message.guild.id,
                    "channel_id": message.channel.id,
                    "content": message.content,
                    "message_id": message.id,
                    "reports_channel": guild_settings.ai_reports_channel,
                    "author_id": message.author.id
                }
            )
        )

        self.bot.scanned_messages_count += 1

    @loop(seconds=1.1)  # abide by perspective ratelimits
    async def scan_messages(self):
        if not self.messages:
            return

        msg = unpackb(self.messages.popleft())

        message_id = msg["message_id"]

        try:
            guild = await self.bot.fetch_guild(msg["guild_id"])
            author = await guild.fetch_member(msg["author_id"])
            score = await self.perspective.score(
                msg["content"],
                [
                    Attribute.toxicity,
                    Attribute.severe_toxicity,
                    Attribute.insult,
                    Attribute.threat,
                ],
            )
            scores = (score.toxicity, score.severe_toxicity,
                    score.insult, score.threat)
            avgscore = sum(scores) / 4
            if avgscore > 0.5 or any(score > 0.7 for score in scores):
                reports_channel = await self.bot.getch_channel(msg["reports_channel"])
                embed = (
                    Embed(
                        title="Message Flagged",
                        description=f"Average rating was **{round(avgscore*100)}%**.\nToxicity rating was **{round(score.toxicity*100)}%**.\nSevere toxicity rating was **{round(score.severe_toxicity*100)}%**.\nInsult rating was **{round(score.insult*100)}%**.\nThreat rating was **{round(score.threat*100)}%**.",
                        color=0x6B74C7,
                    )
                    .set_author(
                        name=f"{author} ({author.id})",
                        icon_url=author.display_avatar.url,
                    )
                    .set_footer(
                        text=f"Message ID: {message_id} • Author ID: {author.id}"
                    )
                )
                await reports_channel.send(embed=embed, view=self.build_view(AiPartialMessage(**msg)))
        except Exception as e: # don't die if you fail once
            logger.error(f"error while scanning message {message_id}: {e}")

    @scan_messages.error
    async def scan_msgs_error(self, error: Exception):
        logger.error(
            f"error while scanning message {unpackb(self.messages.popleft())}")
        if not self.scan_messages.is_running():
            self.scan_messages.start()


def setup(bot: PurpBot):
    bot.add_cog(AiModeration(bot))
