import json
import logging

import disnake
from disnake.ext import commands

from constants import GUILD_IDS
from neurosphere.objects import (
    Character,
    Location,
    World,
    new_id,
)
from neurosphere.worlds import Planet

WORLD_TYPES = {"planet": Planet}


class Neurosphere:
    """Нейросфера - название симуляции генеративных агентов. Не обязательно происходит на сфере."""

    def __init__(self, file_path="neurosphere/neurospheres/neurosphere0.json"):
        self._worlds: dict[int, World] = {}
        self._locations: dict[int, Location] = {}
        self._characters: dict[int, Character] = {}
        self._players: dict[int, int] = {}  # user id -> char id
        self._game_messages: dict[int, disnake.Message] = {}
        self._time: int = 0
        self._action_handler = None  # TODO сделать действия

        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        self._read_data(data)

    # region Методы симуляции

    def tick(self) -> None:
        self._time += 1
        # проитерировать

    # endregion Методы симуляции

    # region JSON Методы

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
            # World generation
            new_id_ = new_id(self._worlds)
            world_data["id"] = new_id_
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
        characters = data["characters"]
        not_generated_characters = []

        for character_data in characters:
            character_id = character_data["id"]
            if character_id is not None:
                character = Character(character_data)
                self._characters[character_id] = character
            else:
                not_generated_characters.append(character_data)

        for character_data in not_generated_characters:
            # Character generation
            new_id_ = new_id(self._characters)
            character_data["id"] = new_id_
            world_id = character_data["generation"]["world_id"]
            world = self._worlds[world_id]
            character = world.generate_character(character_data)
            # world.generate_character_items() тоже
            self._add_character(character)
            # self._add_items() тоже

    # endregion JSON Методы

    # region Методы управления

    def _add_character(self, character: Character) -> None:
        """Добавляет персонажа в нейросферу"""
        char_id = character.get_id()
        location = self._get_location_by_char_id(char_id)
        location.add_character_id(char_id)
        character.set_active(True)

    def _remove_character(self, character: Character) -> None:
        """Убирает персонажа из нейросферы"""
        char_id = character.get_id()
        location = self._get_location_by_char_id(char_id)
        location.remove_character_id(char_id)
        character.set_active(False)

    def _add_character_id_to_location(self, char_id, location_id):
        location = self._locations[location_id]
        location.add_character_id(char_id)

    # endregion

    # region Методы информации

    def get_player_message(self, char_id: int) -> str:
        world = self._get_world_by_char_id(char_id)
        location = self._get_location_by_char_id(char_id)
        return world.get_location_description(location)

    def _get_world_id_by_char_id(self, char_id: int) -> int:
        return self._get_location_by_char_id(char_id).get_world_id()

    def _get_world_by_char_id(self, char_id: int) -> World:
        return self._worlds[self._get_world_id_by_char_id(char_id)]

    def _get_world_by_location_id(self, location_id: int) -> World:
        return self._worlds[self._locations[location_id].get_world_id()]

    def _get_location_id_by_char_id(self, char_id: int) -> int:
        return self._characters[char_id].get_location_id()

    def _get_location_by_char_id(self, char_id: int) -> Location:
        return self._locations[self._get_location_id_by_char_id(char_id)]

    def is_char_controllable_by_player(self, char_id: int, player_id) -> bool:
        if char_id not in self._characters:
            logging.error("Нельзя контроллировать несуществующего персонажа")
            return False
        char = self._characters[char_id]
        if char.get_ai_level() != 0:
            logging.error(
                "Нельзя контроллировать персонажа, контролируемого ИИ"
            )
            return False
        return (
            char_id not in self._players or self._players[char_id] == player_id
        )

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

    # endregion Методы информации

    # region API

    def _parse_input(self, input_: str) -> list[str]:
        pass

    def handle_input(self, input_: str) -> bool:
        actions = self._parse_input(input_)
        if not actions:
            return False
        # логика
        return True

    # endregion API

    # region Actions

    # def handle

    # endregion Actions


class NeurosphereCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.neurosphere: Neurosphere = None
        self.game_channels: dict[int, int] = {}  # id юзера: id канала

    @commands.slash_command(
        name="neurosphere",
        description="Запуск нейросферы",
        guild_ids=GUILD_IDS,
    )
    async def launch_neurosphere(
        self, inter: disnake.ApplicationCommandInteraction
    ) -> None:
        await inter.response.defer()
        self.neurosphere = Neurosphere()
        await inter.followup.send("Нейросфера запущена")

    @commands.slash_command(
        name="play",
        description="Играйте за персонажа в нейросфере!",
        guild_ids=GUILD_IDS,
    )
    async def add_player(
        self, inter: disnake.ApplicationCommandInteraction, char_id: int
    ) -> None:
        if self.neurosphere is None:
            await inter.response.send_message(
                "Нейросфера не запущена.", ephemeral=True
            )
            return
        # TODO реализовать

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.author.bot:
            return
        if self.neurosphere is None:
            return
        game_channel_id = self.game_channels[message.author.id]
        if message.channel.id != game_channel_id:
            return
        self.neurosphere.handle_input()

        # if message.content.startswith("!go"):
        #     try:
        #         coords = message.content.strip().split()[1:]

        #         if len(coords) >= 2:
        #             # обработка координат
        #             await message.channel.send(
        #                 f"Найдены координаты для перемещения: {' '.join(coords)}"
        #             )
        #             # тут надо логику
        #         else:
        #             await message.channel.send(
        #                 "Недостаточно координат. используйте формат: !go {id локации}"
        #             )
        #     except Exception:
        #         logging.exception("Тестовая ошибка !go")


def setup(bot):
    bot.add_cog(NeurosphereCog(bot))
