import os
import logging
import disnake
from disnake.ext import commands
from dotenv import load_dotenv
from constants import register

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
intents = disnake.Intents.all()
bot = commands.InteractionBot(intents=intents)

logging.basicConfig(level=logging.INFO)
logging.info("Приложение запущено")


def load():
    for filename in os.listdir("cogwheels"):
        if filename.endswith(".py"):
            bot.load_extension(f"cogwheels.{filename[:-3]}")


@bot.event
async def on_ready():
    print(f"{bot.user} запустился!")


@bot.event
async def on_message(message: disnake.Message):
    if message.author == bot.user:
        return
    username: str = str(message.author)
    user_message: str = message.content
    channel: str = str(message.channel)
    if message.guild:
        print(f"[{message.guild}] <{channel}> {username}: {user_message}")
    else:
        print(f"<!NEW DM!> {username}: {user_message}")
        register(message.author)

        # запись личных сообщений
        folder_name = f"{message.author.id}"
        path = f"data/users/{folder_name}/dm.txt"
        with open(path, "a", encoding="utf-8") as file:
            file.write(f"{username}: {user_message}\n")


@bot.event
async def on_member_join(member):
    register(member)
    with open(f"data/users/{member.id}/channel.txt", "w", encoding="utf-8") as file:
        file.write("")


load()
bot.run(token=TOKEN)
