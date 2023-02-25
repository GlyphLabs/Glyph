from discord.ui import View, Button, button
from discord import (
    ButtonStyle,
    PermissionOverwrite,
    Interaction,
    Embed,
)


class VoteButtons(View):
    def __init__(self):
        super().__init__()
        self.add_item(
            Button(
                label="Vote for Purpbot",
                url="https://top.gg/bot/849823707429994517/vote",
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
            interaction.guild.me: PermissionOverwrite(read_messages=True),
        }
        channel = await interaction.guild.create_text_channel(f"{interaction.user}-ticket", overwrites=overwrtes)  # type: ignore
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
