from __future__ import annotations
from src.bot import Glyph
from discord.ext.commands import Cog
from discord.channel import TextChannel
from discord import Message, Embed, ButtonStyle, Interaction
from discord.ui import View, Button
from typing import Optional
from datetime import timedelta
from logging import getLogger
from dataclasses import dataclass
from fasttext import load_model # type: ignore
from asyncio import get_running_loop


logger = getLogger(__name__)


@dataclass
class AiPartialMessage:
    guild_id: int
    channel_id: int
    content: str
    message_id: int
    author_id: int
    reports_channel: Optional[int] = None

    @classmethod
    def from_message(
        cls, message: Message, reports_channel: Optional[int] = None
    ) -> AiPartialMessage:
        """builds an AiPartialMessage from a discord.Message object and optional reports_channel id.

        Args:
            message (Message): the message to build the partial message from.
            reports_channel (int, optional): the id of the reports channel of that guild. Defaults to None.

        Raises:
            ValueError: raised if the message is not in a guild.

        Returns:
            AiPartialMessage: the constructed partial message.
        """
        if not message.guild:
            raise ValueError("message must be in a guild.")

        return cls(
            guild_id=message.guild.id,
            channel_id=message.channel.id,
            content=message.content,
            message_id=message.id,
            reports_channel=reports_channel,
            author_id=message.author.id,
        )


class AiModeration(Cog):
    __slots__ = ["bot"]

    def __init__(self, bot: Glyph):
        self.bot = bot

    def build_view(self, message: AiPartialMessage, disabled: bool = False) -> View:
        """builds an interactions view for the flagged message. the id's carry all required information to act on the message.

        Args:
            message (AiPartialMessage): a minimal version of the message to build the view for.
            disabled (bool, optional): whether or not the view is disabled. Defaults to False.

        Returns:
            View: the built view
        """
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
            url=f"https://discord.com/channels/{message.guild_id}/{message.channel_id}/{message.message_id}",
            disabled=disabled,
        )
        items = (jump_button, delete_button, timeout_button, kick_button, ban_button)
        return View(*items, timeout=None)

    @Cog.listener()
    async def on_interaction(self, interaction: Interaction):
        # handles what happens when a view is interacted with

        # check if the interaction is relevant. if not, end early.
        if (
            not interaction.custom_id
            or not interaction.message
            or not interaction.custom_id.startswith("flagged_message_options")
        ):
            return

        # get the data we stored in the custom_id
        cleaned_id = interaction.custom_id.split(":")[1]
        action, msg_channel_id, msg_id = cleaned_id.split("-")
        channel = await self.bot.getch_channel(int(msg_channel_id))
        message = await channel.fetch_message(int(msg_id)) # type: ignore
        
        # appease linter
        if not message.guild:
            return
        
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
                message.author.id, # type: ignore
                f"Flagged message by AI moderation. Kicked by {interaction.user}.",
            )
            await interaction.response.send_message(
                f"{message.author} has been kicked.", ephemeral=True
            )
        elif action == "ban":
            await message.delete()
            await message.guild.ban(message.author.id) # type: ignore
            await interaction.response.send_message(
                f"{message.author} has been banned.", ephemeral=True
            )
        await interaction.message.edit(
            embed=interaction.message.embeds[0],
            view=self.build_view(AiPartialMessage.from_message(message), disabled=True),
        )

    @Cog.listener()
    async def on_message(self, message: Message):
        if message.author.bot or not message.guild:
            return

        if not message.content:
            return

        guild_settings = await self.bot.db.get_guild_settings(message.guild.id, auto_insert=False)
        if not guild_settings or not guild_settings.ai_reports_channel:
            return

        await self.scan_message(message, guild_settings.ai_reports_channel)

    async def scan_message(self, msg: Message, reports_channel_id: int):
        if not msg.guild:
            return
        
        content = msg.content
        message_id = msg.id
        try:
            loop = get_running_loop()
            model = await loop.run_in_executor(
                None, lambda: load_model("src/cogs/model.bin")
            )

            for line in content.splitlines():
                _score = await loop.run_in_executor(
                    None, lambda: model.predict(line, k=6)
                )

                score = {
                    label.replace("__label__", ""): score
                    for label, score in zip(_score[0], _score[1])
                }
                logger.debug(f"message {message_id} has probability: {score}")
                if score.get("non_toxic", 0) < 0.65:
                    guild = await self.bot.fetch_guild(msg.guild.id)
                    author = await guild.fetch_member(msg.author.id)
                    reports_channel: TextChannel = await self.bot.getch_channel(reports_channel_id) # type: ignore
                    embed = (
                        Embed(
                            title="Message Flagged",
                            description=f"Highest score was **{next(iter(score.keys()))}** with a percentage of **{round(next(iter(score.values()))*100)}%**.\n"
                            + "\n".join(
                                f"`{f}`: **{round(s*100)}%**"
                                for f, s in list(i for i in score.items())[1:4]
                            ),
                            color=0xffffff,
                        )
                        .set_author(
                            name=f"{str(author).replace('#0','')} ({author.id})",
                            icon_url=author.display_avatar.url,
                        )
                        .set_footer(
                            text=f"Message ID: {message_id} • Author ID: {author.id}"
                        )
                        .add_field(
                            name="Message Content",
                            value=f'||{content[:100]}{("..." if len(content) > 100 else "")}||',
                        )
                    )
                    await reports_channel.send(
                        embed=embed,
                        view=self.build_view(AiPartialMessage.from_message(msg)),
                    )
        except Exception as e:  # don't die if you fail once
            logger.error(f"error while scanning message {message_id}: {e}")


def setup(bot: Glyph):
    bot.add_cog(AiModeration(bot))
