import asyncio
import time

import disnake
from disnake.ext import commands
from g4f.client import Client

from constants import GUILD_IDS, OWNERS

swedusharium_image_url = "https://i.imgur.com/mHi3aRb.png"
MODEL = "deepseek-chat"


class Conversation:
    def __init__(self, system_message: str):
        self.client = Client()
        self.history = [{"role": "system", "content": system_message}]

    def add_message(self, role, content):
        self.history.append({"role": role, "content": content})

    def add_message_disnake(self, message: disnake.message.Message):
        name = message.author.name
        content = message.content
        self.add_message(f"user {name}", content)

    def get_response(self):
        response = self.client.chat.completions.create(
            model=MODEL, messages=self.history, web_search=False
        )

        assistant_response = response.choices[0].message.content
        self.add_message("assistant", assistant_response)

        return assistant_response


class TestCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_channel_ids: dict[int, Conversation] = {}

    @commands.slash_command(
        name="generate-text", description="generates text", guild_ids=GUILD_IDS
    )
    async def generate_text(
        self, inter: disnake.ApplicationCommandInteraction, prompt: str
    ):
        await inter.response.defer()
        client = Client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            web_search=False,
        )
        text = response.choices[0].message.content
        await inter.followup.send(text)

    @commands.slash_command(
        name="generate-image",
        description="generates image",
        guild_ids=GUILD_IDS,
    )
    async def generate_image(
        self, inter: disnake.ApplicationCommandInteraction, prompt: str
    ):
        await inter.response.defer()
        client = Client()
        response = await client.images.async_generate(
            model="flux", prompt=prompt, response_format="url"
        )
        text = response.data[0].url
        await inter.followup.send(text)

    @commands.slash_command(
        name="webhook-test", description="webhook test", guild_ids=GUILD_IDS
    )
    async def webhook_test(
        self,
        inter: disnake.ApplicationCommandInteraction,
        message: str,
        username: str,
        avatar_url: str,
    ):
        await inter.response.defer()
        webhook = await inter.channel.create_webhook(name=username)
        await webhook.send(
            content=message, username=username, avatar_url=avatar_url
        )
        await webhook.delete()
        await inter.followup.send(f"Вебхук отправлен от имени **{username}**!")

    @commands.slash_command(
        name="activate-ai",
        description="активировать терминатора",
        guild_ids=GUILD_IDS,
    )
    async def activate_ai(self, inter: disnake.ApplicationCommandInteraction):
        if inter.author.id not in OWNERS:
            await inter.response.send_message(
                "Only the server owner can use this command!", ephemeral=True
            )
            return
        channel = inter.channel
        self.active_channel_ids[channel.id] = Conversation(
            "Тебя зовут Шведушариум. Ты - бот на сервере под названием Кузосервер. Говори по-русски. "
            "Твоя цель - общаться. Удачи!"
        )
        await inter.response.send_message("ИИ активирован")

    @commands.slash_command(
        name="deactivate-ai",
        description="деактивировать терминатора",
        guild_ids=GUILD_IDS,
    )
    async def deactivate_ai(self, inter: disnake.ApplicationCommandInteraction):
        if inter.author.id not in OWNERS:
            await inter.response.send_message(
                "Only the server owner can use this command!", ephemeral=True
            )
            return
        channel = inter.channel
        del self.active_channel_ids[channel.id]
        await inter.response.send_message("ИИ деактивирован")

    @commands.Cog.listener()
    async def on_message(self, message: disnake.message.Message):
        channel = message.channel
        if channel.id not in self.active_channel_ids or message.author.bot:
            return

        conversation: Conversation = self.active_channel_ids[channel.id]
        conversation.add_message_disnake(message)

        await asyncio.sleep(3)
        history = await channel.history(limit=10).flatten()

        if message.id != history[0].id:
            return
        start = time.time()
        response = conversation.get_response()
        end = time.time()
        response += f"\n-# {end - start:.2f}"
        if len(response) > 2000:
            response = response[:2000]
        await channel.send(response)
        print(conversation.history)


def setup(bot):
    bot.add_cog(TestCog(bot))
