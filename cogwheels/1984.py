import disnake
from disnake.ext import commands

MODERATED_SERVERS = [955168680474443777]


class NinetyEightyFourCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.guild.id not in MODERATED_SERVERS:
            return


def setup(bot):
    bot.add_cog(NinetyEightyFourCog(bot))
