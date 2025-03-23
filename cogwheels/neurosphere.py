import json
import logging

import disnake
from disnake.ext import commands

from constants import GUILD_IDS
from neurosphere.objects import Character, Location, World, new_id
from neurosphere.worlds import Planet

WORLD_TYPES = {"planet": Planet}


class Neurosphere:
    def __init__(self, file_path="neurospheres/neurosphere/neurosphere0.json"):
        self._worlds: dict[int, World] = {}
        self._locations: dict[int, Location] = {}
        self._characters: dict[int, Character] = {}
        self._players = dict[int, int] = {}

        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        self._read_data(data)

    def _read_data(self, data: dict) -> None:
        self._read_worlds(data)
        self._read_locations(data)
        self._read_characters(data)

    def _read_worlds(self, data: dict) -> None:
        worlds = data["worlds"]
        not_generated_worlds = []

        for world_data in worlds:
            world_id = world_data["id"]
            if world_id is not None:
                world_class = WORLD_TYPES[world_data["type"]]
                world = world_class(world_data)
                self._worlds[world_id] = world
            else:
                not_generated_worlds.append(world_data)

        for world_data in not_generated_worlds:
            world_class = WORLD_TYPES[world_data["type"]]
            world = world_class(world_data)
            world.generate()
            world.generate_locations(self._locations)
            self._worlds[new_id(self._worlds)] = world

    def _read_locations(self, data: dict) -> None:
        locations = data["locations"]
        for location_data in locations:
            location_id = location_data["id"]
            location = Location(location_data)
            self._locations[location_id] = location

    def _read_characters(self, data: dict) -> None:
        characters = data["locations"]
        for character_data in characters:
            character_id = character_data["id"]
            character = Character(character_data)
            # TODO сделать генерацию персонажей
            self._characters[character_id] = character

    def get_player_message(self, char_id: int) -> str:
        world = self.get_world_by_char_id(char_id)
        location_id = self.get_location_id_by_char_id(char_id)
        output = world.get_location_description(location_id)
        return output

    def get_world_id_by_char_id(self, char_id: int) -> int:
        return self.get_location_by_char_id(char_id).get_world_id()

    def get_world_by_char_id(self, char_id: int) -> int:
        return self._worlds[self.get_world_id_by_char_id(char_id)]

    def get_location_id_by_char_id(self, char_id: int) -> int:
        return self._characters[char_id].get_location_id()

    def get_location_by_char_id(self, char_id: int) -> Location:
        return self._locations[self.get_location_id_by_char_id(char_id)]

    def is_char_controllable_by_player(self, char_id: int, player_id) -> bool:
        if char_id not in self._characters:
            logging.error("Нельзя контроллировать несуществующего персонажа")
            return False
        char = self._characters[char_id]
        if char.get_ai_level() != 0:
            logging.error("Нельзя контроллировать персонажа, контролируемого ИИ")
            return False
        return char_id not in self._players or self._players[char_id] == player_id

    def get_player_id(self, char_id: int) -> int | None:
        if char_id in self._players:
            return self._players[char_id]
        return None

    def set_player_id(self, char_id, player_id) -> None:
        self._players[char_id] = player_id

    def get_char_id(self, player_id: int) -> int | None:
        inverted_players = {v: k for k, v in self._players.items()}
        if player_id in inverted_players:
            return inverted_players[player_id]
        return None


class NeurosphereCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.neurosphere: Neurosphere = None
        self.game_messages: dict[int, disnake.Message] = {}  # id юзера: сообщение

    @commands.slash_command(
        name="neurosphere",
        description="Запуск нейросферы",
        guild_ids=GUILD_IDS,
    )
    async def launch_neurosphere(self, inter: disnake.ApplicationCommandInteraction) -> None:
        await inter.response.defer()
        self.neurosphere = Neurosphere()
        await inter.followup.send("Нейросфера запущена")

    @commands.slash_command(
        name="control-character", description="Контроллировать персонажа", guild_ids=GUILD_IDS
    )
    async def test(self, inter: disnake.ApplicationCommandInteraction, char_id: int) -> None:
        if self.neurosphere is None:
            await inter.response.send_message("Нейросфера не запущена.", ephemeral=True)
            return
        if not self.neurosphere.is_char_controllable_by_player(char_id, inter.author.id):
            await inter.response.send_message("Персонаж не может быть контролирован.")
            return

        player_id = self.neurosphere.get_player_id(char_id)
        if player_id is None:
            self.neurosphere.set_player_id(char_id, inter.author.id)
        if inter.author.id in self.game_messages:
            previous_game_message = self.game_messages[inter.author.id]
            await previous_game_message.delete()

        channel = inter.channel
        player_message: str = self.neurosphere.get_player_message(char_id)
        game_message: disnake.Message = await channel.send(player_message)
        self.game_messages[inter.author.id] = game_message

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.author.bot:
            return
        if self.neurosphere is None:
            return

        if message.content.startswith("!go"):
            try:
                coords = message.content.strip().split()[1:]

                if len(coords) >= 2:
                    # обработка координат
                    await message.channel.send(
                        f"Найдены координаты для перемещения: {' '.join(coords)}"
                    )
                    # тут надо логику
                else:
                    await message.channel.send(
                        "Недостаточно координат. используйте формат: !go {id локации}"
                    )
            except Exception:
                logging.exception("Тестовая ошибка !go")


def setup(bot):
    bot.add_cog(NeurosphereCog(bot))
