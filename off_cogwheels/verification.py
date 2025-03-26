import disnake
from disnake.ext import commands
from disnake.ui import Button, ActionRow
from constants import PERSONAGES_ID, SWEDUSHARIUM_ID, STAR_ROLE_ID, register
active_messages = dict()
ID = "verification_"


async def make_personage_channel(inter: disnake.MessageInteraction,
                                 guild: disnake.Guild):
    category = disnake.utils.get(guild.categories, id=PERSONAGES_ID)
    overwrites = {
        guild.default_role: disnake.PermissionOverwrite(read_messages=False),
        inter.author: disnake.PermissionOverwrite(read_messages=True)
    }
    channel = await category.create_text_channel(inter.author.display_name, overwrites=overwrites)

    # запомнить айди
    with open(f"data/users/{inter.author.id}/channel.txt", "w", encoding="utf-8") as file:
        file.write(str(channel.id))


def increment_verifications():
    with open("data/verifications.txt", "r+") as f:
        number = int(f.read())
        f.seek(0)
        f.write(str(number + 1))


class Safe:
    def __init__(self, user_id):
        self.numbers = list()
        self.user_id = user_id

    def get_embed(self) -> disnake.Embed:
        embed = disnake.Embed(
            title="Enter a three-digit code",
            description=f"\n{self.get_numbers_string()}"
        )
        return embed

    def get_components(self, correct=0):
        if correct == 1:
            return ActionRow(Button(emoji="⭐", style=disnake.ButtonStyle.success, disabled=True))
        elif correct == 0:
            indicator = Button(emoji="🔒", disabled=True)
        else:
            indicator = Button(emoji="❌", disabled=True)
        buttons = [ActionRow(Button(label="7", custom_id=ID + "7"),
                             Button(label="8", custom_id=ID + "8"),
                             Button(label="9", custom_id=ID + "9"), ),
                   ActionRow(Button(label="4", custom_id=ID + "4"),
                             Button(label="5", custom_id=ID + "5"),
                             Button(label="6", custom_id=ID + "6"), ),
                   ActionRow(Button(label="1", custom_id=ID + "1"),
                             Button(label="2", custom_id=ID + "2"),
                             Button(label="3", custom_id=ID + "3"), ),
                   ActionRow(Button(emoji="🔑", custom_id=ID + "key", disabled=not self.numbers_are_full()),
                             Button(label="0", custom_id=ID + "0"),
                             indicator, ),
                   ]
        return buttons

    def is_opened(self) -> int:
        usable_codes = [list(code.strip()) for code in
                        open(f"data/users/{self.user_id}/usable_codes.txt", encoding="utf-8").readlines()]
        used_codes = [list(code.strip()) for code in
                      open(f"data/users/{self.user_id}/used_codes.txt", encoding="utf-8").readlines()]
        if self.numbers in used_codes:
            return -1
        elif self.numbers in usable_codes:
            return 1
        else:
            return 0

    def numbers_are_full(self) -> bool:
        return len(self.numbers) == 3

    def get_numbers_string(self) -> str:
        numbers = [':zero:', ':one:', ':two:', ':three:', ':four:', ':five:', ':six:', ':seven:', ':eight:', ':nine:']
        output = ""
        for i in self.numbers:
            output += numbers[int(i)]
        output += ":hash:" * (3 - len(self.numbers))
        return output

    def insert_number(self, number: str) -> None:
        self.numbers.append(number)

    def clear_numbers(self) -> None:
        self.numbers = list()


class Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener("on_button_click")
    async def help_listener(self, inter: disnake.MessageInteraction):
        if not inter.component.custom_id.startswith(ID):
            return
        else:
            action = inter.component.custom_id[len(ID):]
        guild = self.bot.get_guild(SWEDUSHARIUM_ID)
        if guild.get_member(inter.author.id) is None:
            await inter.response.send_message("You are not a part of Swedusharium yet.\nhttps://discord.gg/CNRGQKCGMH",
                                              ephemeral=True)
            return

        global active_messages
        register(inter.author)

        with open(f"data/users/{inter.author.id}/channel.txt", "r", encoding="utf-8") as f:
            if f.read():
                await inter.response.send_message("Your registration has already been completed.",
                                                  ephemeral=True)
                return

        if action == "send":
            try:
                safe = Safe(inter.author.id)
                message = await inter.author.send(
                    embed=safe.get_embed(),
                    components=safe.get_components()
                )
                active_messages[message.id] = safe
                await inter.response.send_message("⭐", ephemeral=True)
            except disnake.errors.Forbidden:
                await inter.response.send_message("Everything happens for the best.", ephemeral=True)
            except Exception as e:
                print("Непредвиденная ошибка, verification_send")
                print(e)
            return

        if inter.message.id in active_messages:
            safe = active_messages[inter.message.id]
        else:
            await inter.response.send_message("This is an old message. Please try pressing the button again.",
                                              ephemeral=True)
            return

        if action == "key":
            attempt = "".join(safe.numbers)
            print(f"{inter.author}'s verification attempt: {attempt}")
            opened = safe.is_opened()  # 0 - неверный, -1 - использованный, 1 - правильный
            if opened == 1:
                with open(f"data/users/{inter.author.id}/used_codes.txt", "a", encoding="utf-8") as file:
                    file.write(attempt + "\n")
                await inter.response.edit_message(embed=safe.get_embed(), components=safe.get_components(correct=1))

                member = guild.get_member(inter.author.id)
                await make_personage_channel(inter, guild)
                await member.add_roles(guild.get_role(STAR_ROLE_ID))
                increment_verifications()

            elif opened == -1:
                safe.clear_numbers()
                await inter.response.send_message("The same code cannot be used twice.", ephemeral=True)
                await inter.message.edit(embed=safe.get_embed(), components=safe.get_components(correct=-1))
            else:
                safe.clear_numbers()
                await inter.response.edit_message(embed=safe.get_embed(), components=safe.get_components(correct=-1))
            return
        elif safe.numbers_are_full():
            await inter.response.send_message("After entering the code, press the key button to proceed.",
                                              ephemeral=True)
            return
        else:
            safe.insert_number(action)
            await inter.response.edit_message(embed=safe.get_embed(), components=safe.get_components())
            return


def setup(bot):
    bot.add_cog(Cog(bot))
