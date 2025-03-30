import json
import logging

import disnake
from disnake.ext import commands, tasks
from g4f.client import Client

from constants import GUILD_IDS, OWNERS

MODERATED_SERVERS = [955168680474443777]
MODEL = "deepseek-chat"


def message_dict(message: disnake.Message) -> dict[str]:
    return {
        "content": message.content,  # str
        "author": message.author.name,  # str
        "channel": message.channel.name,  # str
        "id": message.id,  # int
        "author_id": message.author.id,  # int
        "channel_id": message.channel.id,  # int
        "time": message.created_at.timestamp(),  # float
    }


class BigBrother:
    def __init__(self):
        self.active: bool = True

        self._messages_path: str = "other_files/1984/messages.json"
        self._client: Client = Client()
        self._registered_messages: list[int] = []
        self._new_messages: list[tuple[str, dict]] = []

    def set_active(self, active: bool):
        self.active = active

    def get_commands(self):
        if not self._new_messages:
            return []

    def register_message(self, message: disnake.Message) -> None:
        if message.author.bot or not message.content:
            return
        self._new_messages.append(
            (message.created_at.strftime("%Y.%m.%d"), message_dict(message))
        )

    def update_messages(self) -> None:
        if not self._new_messages:
            return

        with open(self._messages_path, encoding="utf-8") as file:
            messages: dict[str, dict] = json.load(file)

        new_messages = self._new_messages[:]
        self._new_messages = []

        for date_key, message in new_messages:
            messages.setdefault(date_key, []).append(message)

        messages = {
            k: sorted(v, key=lambda x: x["time"], reverse=True)
            for k, v in sorted(messages.items(), reverse=True)
        }

        with open(self._messages_path, "w", encoding="utf-8") as file:
            json.dump(messages, file, indent=4, ensure_ascii=False)


class NinetyEightyFourCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.big_brother = BigBrother()
        self.update_messages_loop.start()

    @commands.slash_command(
        name="read-server-history",
        description="Читает сообщения сервера",
        guild_ids=GUILD_IDS,
    )
    async def read_server_messages(  # noqa
        self, inter: disnake.ApplicationCommandInteraction, limit: int = 100
    ):
        if inter.author.id not in OWNERS:
            await inter.response.send_message(
                "Вы не можете использовать эту команду", ephemeral=True
            )
            return
        await inter.response.defer()
        self.big_brother.set_active(False)
        for channel in inter.guild.channels:
            if channel.type not in [
                disnake.ChannelType.text,
                disnake.ChannelType.voice,
                disnake.ChannelType.stage_voice,
                disnake.ChannelType.public_thread,
                disnake.ChannelType.private_thread,
            ]:
                continue
            i = 0
            async for message in channel.history(limit=limit):
                i += 1
                if i % 5000 == 0:
                    logging.info(f"Processing... {message.created_at}")
                    self.big_brother.update_messages()
                self.big_brother.register_message(message)
        self.big_brother.set_active(True)
        self.big_brother.update_messages()
        await inter.followup.send("Успех", delete_after=5)

    @commands.slash_command(
        name="update_messages",
        description="Вызывает update_messages()",
        guild_ids=GUILD_IDS,
    )
    async def update_messages(
        self,
        inter: disnake.ApplicationCommandInteraction,
    ):
        if inter.author.id not in OWNERS:
            await inter.response.send_message(
                "Вы не можете использовать эту команду", ephemeral=True
            )
            return
        self.big_brother.update_messages()
        await inter.response.send_message("Успех", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.guild.id not in MODERATED_SERVERS:
            return
        self.big_brother.register_message(message)

    @tasks.loop(seconds=30)
    async def update_messages_loop(self):
        if self.big_brother.active:
            self.big_brother.update_messages()


def setup(bot):
    bot.add_cog(NinetyEightyFourCog(bot))
