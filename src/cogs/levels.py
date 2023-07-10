from discord.ext.commands import Cog, slash_command, Context
from discord import Message, Embed
from src.bot import PurpBot
from random import randint


class Levels(Cog):
    def __init__(self, bot: PurpBot):
        self.bot = bot

    @Cog.listener()
    async def on_message(self, message: Message):
        if message.author.bot or not message.guild:
            return

        guild_settings = await self.bot.db.get_guild_settings(message.guild.id)

        if not guild_settings.level_system:
            return

        level_stats = await self.bot.db.get_level_stats(message.author.id, message.guild.id)
        new_xp = randint(5, 10)

        if level_stats.xp + new_xp >= level_stats.level * 100:
            await message.reply(
                embed=Embed(
                    description=f"Congratulations, {message.author.mention}! You leveled up to level {level_stats.level+1}!"
                ).set_author(name="New Level", icon_url=message.author.avatar.url)
            )

        await self.bot.db.add_xp(message.author.id, message.guild.id, new_xp)

    @slash_command(name="rank", description="Shows your rank")
    async def rank(self, ctx: Context):
        stats = self.bot.db.get_level_stats(ctx.author.id, ctx.guild.id)
        await ctx.respond(
            embed=Embed()
            .set_author(
                name=f"{ctx.author.name}'s Rank", icon_url=ctx.author.avatar.url
            )
            .add_field(name="Level", value=stats.level)
            .add_field(name="XP", value=f"{stats.xp}/{stats.level*100}")
        )


def setup(bot):
    bot.add_cog(Levels(bot))
