import disnake
import os
from disnake.ui import Button

# general constants
GUILD_IDS = [1324774187583410249, 955168680474443777]
SWEDUSHARIUM_ID = GUILD_IDS[0]
# disnake constants
BLUE = disnake.ButtonStyle.primary
GRAY = disnake.ButtonStyle.secondary
GREEN = disnake.ButtonStyle.success
RED = disnake.ButtonStyle.danger
OWNERS = [393779108708089856, 972186190805614602]


# swedusharium constants
MESSAGES = {
    "nothing": {
        "content": "Nothing",
        "components": [],
    },
    "welcome": {
        "content": "https://images-ext-1.discordapp.net/external/2RvhWttulwcpeTPXh33P32VFA523JxWkiEFX0Kwai_4/https/i.gifer.com/origin/3c/3c82e43002a5c632edebf76eadc6499a_w200.webp?animated=true",
        "components": [
            Button(emoji="🌟", custom_id="verification_send", style=GREEN)
        ],
    },
}


def register(member: disnake.Member):
    if str(member.id) in os.listdir("data/users"):
        return
    path = f"data/users/{member.id}"
    os.mkdir(path)

    with open(f"{path}/usable_codes.txt", "w", encoding="utf-8") as file:
        codes = "123", "999", "147", "258", "369", "321", "111", "005", "759"
        file.write("".join([i + "\n" for i in codes]))
    with open(f"{path}/info.txt", "w", encoding="utf-8") as file:
        file.write(f"name: {member.name}\nglobal_name: {member.global_name}")

    with open(f"{path}/used_codes.txt", "w", encoding="utf-8") as file:
        file.write("")
    with open(f"{path}/channel.txt", "w", encoding="utf-8") as file:
        file.write("")
