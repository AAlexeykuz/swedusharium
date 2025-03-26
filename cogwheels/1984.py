import json
import disnake
from disnake.ext import commands, tasks
from g4f.client import Client
from constants import GUILD_IDS


MODERATED_SERVERS = [955168680474443777]
MODEL = "deepseek-chat"


class BigBrother:
    def __init__(self):
        self._client: Client = Client()
        self._registered_messages: list[int] = []
        self._new_messages = []

    def get_commands(self):
        if not self._new_messages:
            return []

    def register_messages(self, message: disnake.Message):
        message_info = {
            "id": message.id,  # int
            "channel": message.channel.name,  # str
            "author": message.author.name,  # str
            "time": message.created_at.timestamp(),  # float
            "content": message.content,
        }
        self._new_messages.append(message_info)

    def _save_to_json(self):
        MESSAGES_JSON = Path("messages.json")

        try:
            with open(MESSAGES_JSON, "r", encoding="utf-8") as f:
                all_messages = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            all_messages = []

        all_messages.extend(self._message_buffer)
        self._message_buffer.clear()  # Clear buffer after saving

        with open(MESSAGES_JSON, "w", encoding="utf-8") as f:
            json.dump(all_messages, f, indent=4, ensure_ascii=False)


class NinetyEightyFourCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.big_brother = BigBrother()

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.guild.id not in MODERATED_SERVERS:
            return
        self.big_brother.register_message(message)

    @tasks.loop(seconds=15.0)  # Runs every 15 seconds
    async def check_messages(self):
        commands = self.big_brother.get_commands()


def setup(bot):
    bot.add_cog(NinetyEightyFourCog(bot))
