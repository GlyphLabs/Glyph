from typing import Optional
from discord.enums import ChannelType, ComponentType
from discord.ui import View, Button, button, select, Select
from discord import (
    ButtonStyle,
    PermissionOverwrite,
    Interaction,
    Embed,
    TextChannel,
)


class VoteButtons(View):
    def __init__(self):
        super().__init__()
        self.add_item(
            Button(
                label="Vote for Glyph (coming soon)",
                url="https://purplabs.github.io",
            )
        )


class CreateTicket(View):
    def __init__(self):
        super().__init__(timeout=None)

    @button(
        label="Create Ticket",
        style=ButtonStyle.green,
        custom_id="create_a_ticket:green",
    )
    async def create_ticket(self, button: Button, interaction: Interaction):
        if not interaction.guild:
            return  # something is wrong if this happens
        overwrtes = {
            interaction.guild.default_role: PermissionOverwrite(read_messages=False),
            interaction.user: PermissionOverwrite(read_messages=True),
        }
        channel = await interaction.guild.create_text_channel(
            f"{interaction.user}-ticket", overwrites=overwrtes
        )  # type: ignore
        await interaction.response.send_message(
            f"Channel created! You can go here: {channel.mention}", ephemeral=True
        )
        etix = Embed(
            title="Ticket Created",
            description=f"Hey, {interaction.user} created a ticket | **Click one of the buttons below to change the settings**",
            color=0x6B74C7,
        )
        await channel.send(embed=etix, view=TicketSettings())


class TicketSettings(View):
    def __init__(self):
        super().__init__(timeout=None)

    @button(
        label="Close Ticket", style=ButtonStyle.red, custom_id="ticket_settings:red"
    )
    async def close_ticket(self, button: Button, interaction: Interaction):
        if not interaction.user:
            return
        await interaction.response.send_message("Closing ticket", ephemeral=False)
        await interaction.channel.delete()  # type: ignore
        await interaction.user.send("Ticket closed.")

class YesNo(View):
    def __init__(self, timeout = 180):
        super().__init__(timeout = timeout)
        self.value = None

    @button(
        label="Yes",
        style=ButtonStyle.green,
        custom_id="yes_no:yes",
    )
    async def choose_yes(self, button: Button, interaction: Interaction):
        self.value = True
        await interaction.respond("Got it!", ephemeral=True)
        self.disable_all_items()
        self.stop()

    @button(
        label="No",
        style=ButtonStyle.red,
        custom_id="yes_no:no",
    )
    async def choose_no(self, button: Button, interaction: Interaction):
        self.value = False
        await interaction.respond("Got it!", ephemeral=True)
        self.disable_all_items()
        self.stop()

class ChannelSelect(View):
    def __init__(self, timeout = 180):
        super().__init__(timeout = timeout)
        self.value: Optional[TextChannel] = None

    @select(
        select_type=ComponentType.channel_select,
        placeholder="Choose a channel...",
        custom_id="channel_select:channel",
        max_values=1,
        channel_types=[ChannelType.text]
    )
    async def choose_channel(self, select: Select, interaction: Interaction):
        self.value = select.values[0] # type: ignore
        await interaction.respond("Got it!", ephemeral=True)
        self.disable_all_items()
        self.stop()

    @button(
        label="Cancel",
        style=ButtonStyle.red,
        custom_id="channel_select:cancel",
    )
    async def choose_none(self, button: Button, interaction: Interaction):
        self.value = None
        await interaction.respond("Got it!", ephemeral=True)
        self.disable_all_items()
        self.stop()