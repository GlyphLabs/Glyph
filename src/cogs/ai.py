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


class AiModeration(Cog):
    def __init__(self, bot: PurpBot):
        self.bot = bot
        self.messages: Deque[bytes] = deque()
        self.perspective = self.bot.perspective
        self.scan_messages.start()

    def build_view(self, message: Message, disabled: bool = False) -> View:
        delete_button: Button = Button(
            style=ButtonStyle.gray,
            label="Delete",
            custom_id=f"flagged_message_options:delete-{message.channel.id}-{message.id}",
            disabled=disabled,
        )
        timeout_button: Button = Button(
            style=ButtonStyle.gray,
            label="Timeout [1d]",
            custom_id=f"flagged_message_options:timeout-{message.channel.id}-{message.id}",
            disabled=disabled,
        )
        kick_button: Button = Button(
            style=ButtonStyle.red,
            label="Kick",
            custom_id=f"flagged_message_options:kick-{message.channel.id}-{message.id}",
            disabled=disabled,
        )
        ban_button: Button = Button(
            style=ButtonStyle.red,
            label="Ban",
            custom_id=f"flagged_message_options:ban-{message.channel.id}-{message.id}",
            disabled=disabled,
        )
        items = (delete_button, timeout_button, kick_button, ban_button)
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

        self.bot.scanned_messages_count += 1

    @loop(seconds=1.1)  # abide by perspective ratelimits
    async def scan_messages(self):
        if not self.messages:
            return

        msg = unpackb(self.messages.popleft())

        channel = await self.bot.getch_channel(msg["channel_id"])
        message = await channel.fetch_message(msg["message_id"])
        score = await self.perspective.score(
            message.content,
            [
                Attribute.toxicity,
                Attribute.severe_toxicity,
                Attribute.insult,
                Attribute.threat,
            ],
        )
        scores = (score.toxicity, score.severe_toxicity, score.insult, score.threat)
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
                    name=f"{message.author} ({message.author.id})",
                    icon_url=message.author.display_avatar.url,
                )
                .set_footer(
                    text=f"Message ID: {message.id} • Author ID: {message.author.id}"
                )
                .add_field(
                    name="Message",
                    value=f"{message.content}\n[[Jump to message]({message.jump_url})]",
                )
            )
            await reports_channel.send(embed=embed, view=self.build_view(message))


def setup(bot: PurpBot):
    bot.add_cog(AiModeration(bot))
