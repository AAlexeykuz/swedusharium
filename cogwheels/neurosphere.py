import json

import disnake
from disnake.ext import commands

from constants import GUILD_IDS
from data.neurosphere.objects import (
    Character,
    Controller,
    Item,
    Location,
    PlayerController,
    World,
    new_id,
)
from data.neurosphere.worlds import Planet

WORLD_TYPES = {"planet": Planet}
CONTROLLER_TYPES = {"player": PlayerController}


class Neurosphere:
    def __init__(self, file_path="data/neurosphere/neurospheres/neurosphere0.json"):
        self._worlds: dict[int, World] = {}
        self._locations: dict[int, Location] = {}
        self._characters: dict[int, Character] = {}
        self._items: dict[int, Item] = {}

        self._players: dict[int, int] = {}  # user id -> character id
        self._controllers: dict[int, Controller] = {}  # character id -> controller
        self._windows: dict[int, disnake.Message] = {}  # character id -> message

        self._time: int = 0

        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        self._read_data(data)

    # region Методы симуляции

    def tick(self) -> None:
        self._time += 1
        # TODO Итерация цикла выполнения действий
        # TODO Итерация цикла получения новых действий

    # endregion Методы симуляции

    # region JSON Методы

    def _read_data(self, data: dict) -> None:
        self._read_locations(data)  # первыми локации, чтобы id не перезаписывались
        self._read_worlds(data)
        self._read_characters(data)

    def _read_worlds(self, data: dict) -> None:
        worlds = data["worlds"]
        not_generated_worlds = []

        for world_data in worlds:
            if world_data["id"] is not None:
                world_class = WORLD_TYPES[world_data["type"]]
                world = world_class(world_data)
                self._worlds[world_data["id"]] = world
            else:
                not_generated_worlds.append(world_data)

        for world_data in not_generated_worlds:
            self._generate_world(world_data)

    def _read_locations(self, data: dict) -> None:
        locations = data["locations"]
        for location_data in locations:
            location_id = location_data["id"]
            location = Location(location_data)
            self._locations[location_id] = location

    def _read_characters(self, data: dict) -> None:
        """Загружает персонажей в self._characters если у них есть id
        Если id нет, то генерирует их через мир и добавляет в локацию"""
        characters = data["characters"]
        not_generated_characters = []

        for character_data in characters:
            if character_data["id"] is not None:
                character = Character(character_data)
                self._characters[character_data["id"]] = character
            else:
                not_generated_characters.append(character_data)

        for character_data in not_generated_characters:
            self._generate_character(character_data)

    # endregion JSON Методы

    # region Методы управления

    def _generate_world(self, world_data) -> None:
        new_id_ = new_id(self._worlds)
        world_data["id"] = new_id_
        world_class = WORLD_TYPES[world_data["type"]]
        world = world_class(world_data)
        world.generate()
        world.generate_locations(self._locations)
        self._worlds[new_id(self._worlds)] = world

    def _generate_character(self, character_data) -> None:
        """Генерирует персонажа и добавляет его в Нейросферу"""
        character_id = new_id(self._characters)
        character_data["id"] = character_id
        world_id = character_data["generation"]["world_id"]
        world = self._worlds[world_id]
        world.generate_character(character_data, self._characters, self._items)
        character = self._characters[character_id]
        self._add_character(character)
        self._generate_controller(character_id, character_data["controller"])

    def _generate_controller(self, character_id: int, controller_data) -> None:
        controller_class = CONTROLLER_TYPES[controller_data["type"]]
        controller = controller_class(controller_data)
        self._controllers[character_id] = controller

    def _add_character(self, character: Character) -> None:
        """Включает персонажа и добавляет его в локацию"""
        char_id = character.get_id()
        location = self._get_location_by_character_id(char_id)
        location.add_character_id(char_id)
        character.set_active(True)

    def _remove_character(self, character: Character) -> None:
        """Выключает персонажа и удаляет его из локации"""
        char_id = character.get_id()
        location = self._get_location_by_character_id(char_id)
        location.remove_character_id(char_id)
        character.set_active(False)

    def add_player(self, player_id: int) -> None:
        if player_id in self._players:
            character = self._get_character_by_player_id(player_id)
            self._add_character(character)
            return
        with open("data/neurosphere/characters/player.json", encoding="utf-8") as file:
            character_data = json.load(file)
        self._generate_character(character_data)
        self._players[player_id] = character_data["id"]

    # endregion

    # region Методы отображения

    def get_player_embed(self, player_id: int) -> disnake.Embed:
        """Генерирует Embed для наблюдателя, основанное на локации, её мире, персонаже и его предметах."""
        character = self._get_character_by_player_id(player_id)
        character_id = character.get_id()

        world = self._get_world_by_character_id(character_id)
        location = self._get_location_by_character_id(character_id)
        location_description = world.get_location_description(location)

        return disnake.Embed(
            title=f"Персонаж char_{character_id}",
            description=location_description,
        )

    # endregion методы отображения

    # region Методы информации

    def _get_world_id_by_char_id(self, char_id: int) -> int:
        return self._get_location_by_character_id(char_id).get_world_id()

    def _get_world_by_character_id(self, char_id: int) -> World:
        return self._worlds[self._get_world_id_by_char_id(char_id)]

    def _get_location_id_by_character_id(self, char_id: int) -> int:
        return self._characters[char_id].get_location_id()

    def _get_location_by_character_id(self, char_id: int) -> Location:
        return self._locations[self._get_location_id_by_character_id(char_id)]

    def _get_character_by_player_id(self, player_id: int) -> Character:
        return self._characters[self._players[player_id]]

    def get_controller_by_player_id(self, player_id: int) -> Controller:
        return self._controllers[self._players[player_id]]

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
        self.neurosphere: Neurosphere | None = None
        self.game_channels: dict[int, int] = {}  # id юзера: id канала

    @commands.slash_command(
        name="neurosphere",
        description="Запуск Нейросферы",
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
        description="Играйте за персонажа в Нейросфере!",
        guild_ids=GUILD_IDS,
    )
    async def add_player(
        self,
        inter: disnake.ApplicationCommandInteraction,
    ) -> None:
        if self.neurosphere is None:
            await inter.response.send_message("Нейросфера не запущена.", ephemeral=True)
            return
        await inter.response.send_message("Загрузка...", delete_after=1)
        neurosphere = self.neurosphere
        player_id = inter.author.id
        neurosphere.add_player(player_id)
        embed = neurosphere.get_player_embed(player_id)
        await inter.channel.send(embed=embed)

        # TODO сделать контроллер

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if self.neurosphere is None:
            return
        if message.author.bot:
            return
        game_channel_id = self.game_channels[message.author.id]
        if message.channel.id != game_channel_id:
            return
        self.neurosphere.handle_input()


def setup(bot):
    bot.add_cog(NeurosphereCog(bot))
