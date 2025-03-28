import disnake
from disnake.ext import commands

from constants import GUILD_IDS


class Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        name="command", description="command", guild_ids=GUILD_IDS
    )
    async def command(self, inter: disnake.ApplicationCommandInteraction):
        pass


def setup(bot):
    bot.add_cog(Cog(bot))
