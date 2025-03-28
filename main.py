import logging
import os

import disnake
from disnake.ext import commands
from dotenv import load_dotenv

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
    logging.info(f"{bot.user} запустился!")


@bot.event
async def on_message(message: disnake.Message):
    if message.author == bot.user:
        return
    username: str = str(message.author)
    user_message: str = message.content
    channel: str = str(message.channel)
    if message.guild:
        logging.info(
            f"[{message.guild}] <{channel}> {username}: {user_message}"
        )
    else:
        logging.info(f"<!NEW DM!> {username}: {user_message}")


load()
bot.run(token=TOKEN)
