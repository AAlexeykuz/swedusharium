from io import StringIO
from os import getenv

import anyio
import disnake
from disnake.ext import commands
from dotenv import load_dotenv
from google import generativeai as genai

from constants import GUILD_IDS

load_dotenv()
genai.configure(api_key=getenv("GOOGLE_API_KEY_2"))


async def execute_async_code(code, inter, file):
    try:
        exec(
            "async def __async_exec_func__(inter, file):\n"
            + "\n".join(f"    {line}" for line in code.splitlines()),
            globals(),
        )
        await eval(
            "__async_exec_func__(inter, file)",
            globals(),
            {"inter": inter, "file": file},
        )
        await inter.followup.send(
            "Запрос выполнен! Выполненный код прикреплён.", file=file
        )
    except Exception as e:
        await inter.followup.send(f"Ошибка во время выполнения: {e}", file=file)


class WishCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        name="grant-a-wish",
        description="исполняет любое дискорд желание",
        guild_ids=GUILD_IDS,
    )
    async def command(
        self, inter: disnake.ApplicationCommandInteraction, wish: str
    ):
        if inter.author.id not in [393779108708089856]:
            await inter.response.send_message(
                "Вы не можете использовать эту команду", ephemeral=True
            )
            return
        await inter.response.defer()
        model = genai.GenerativeModel(
            "gemini-exp-1206",
            system_instruction=[
                "You are an assistant designed to write code that would grant user's wish in a discord server. "
                "For example, if they ask for a new role or a new channel or to rename a server, you should do it. "
                "Here's how the code looks right now:\n\n"
                f"{await (await anyio.open_file('cogwheels/generative_execution.py', encoding='utf-8')).read()}\n\n"
                "You should listen to the prompt carefully and make sure that the prompt is not harmful or dangerous. "
                "If the prompt is harmful or dangerous for files or any processes on this computer you should output "
                "'No' only.\n"
                "Remember, you should only filter dangerous code regarding the computer. "
                "Any lines that use discord/disnake modules are okay, but only if they modify discord "
                "server only.\n"
                "As response you should only write the code or 'No' if the prompt can't be done or dangerous. "
                "It will be executed as it is, so don't write anything else."
            ],
        )
        try:
            prompt = f"""
            User input: {wish}
            Your code (and only code):
            """
            response = model.generate_content([prompt])
            code = response.text.strip()
            code = code.removeprefix("```python\n")
            code = code.removesuffix("```")
        except Exception as e:
            await inter.followup.send(f"Ошибка во время генерации: {e}")
            return
        if code.lower() == "no":
            await inter.followup.send("Запрос посчитан невыполнимым.")
            return

        file_obj = StringIO(code)
        file = disnake.File(fp=file_obj, filename="code.txt")

        await execute_async_code(
            code, inter, file
        )  # YOUR CODE WILL BE EXECUTED HERE


def setup(bot):
    bot.add_cog(WishCog(bot))
