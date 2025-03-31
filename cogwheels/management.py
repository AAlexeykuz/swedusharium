import disnake
from disnake.ext import commands

from constants import GUILD_IDS, owner_only


class ManagementCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        name="save-channel-names",
        description="сохраняет названия каналов",
        guild_ids=GUILD_IDS,
    )
    @owner_only
    async def save_channel_names(
        self, inter: disnake.ApplicationCommandInteraction
    ):
        for i in inter.guild.channels:
            print(i.id, i.name)


def setup(bot):
    bot.add_cog(ManagementCog(bot))
