import disnake
from disnake.ext import commands

from constants import GUILD_IDS, MESSAGES


class ControlCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="articulate", guild_ids=GUILD_IDS)
    @commands.has_permissions(administrator=True)
    async def command(
        self,
        inter: disnake.ApplicationCommandInteraction,
        statement: str,
    ):
        await inter.channel.send(statement)
        await inter.response.send_message("⭐", ephemeral=True)

    @commands.slash_command(name="chant", guild_ids=GUILD_IDS)
    @commands.has_permissions(administrator=True)
    async def chant(
        self,
        inter: disnake.ApplicationCommandInteraction,
        statement: str,
    ):
        await inter.channel.send(**MESSAGES[statement])
        await inter.response.send_message("⭐", ephemeral=True)


def setup(bot):
    bot.add_cog(ControlCog(bot))
