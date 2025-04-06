import asyncio
import contextlib
import json
import logging

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
    embeds_are_equal,
    new_id,
)
from data.neurosphere.worlds import Planet

WORLD_TYPES: dict[str, type[World]] = {"planet": Planet}
CONTROLLER_TYPES: dict[str, type[Controller]] = {"player": PlayerController}


class Neurosphere:
    def __init__(self, name="neurosphere0"):
        self._worlds: dict[int, World] = {}
        self._locations: dict[int, Location] = {}
        self._characters: dict[int, Character] = {}
        self._items: dict[int, Item] = {}

        self._players: dict[int, int] = {}  # user id -> character id
        self._controllers: dict[int, Controller] = {}  # character id -> controller
        self._windows: dict[int, disnake.Message] = {}  # character id -> message

        self._time: int = 0
        self._tick_time: float = 1
        self._tick_task: asyncio.Task | None = None

        with open(f"data/neurosphere/neurospheres/{name}.json", encoding="utf-8") as f:
            data = json.load(f)

        self._read_data(data)

    # region Методы симуляции

    async def start_ticking(self):
        self._tick_task = asyncio.create_task(self._tick_loop())

    async def _tick_loop(self):
        try:
            while True:
                await self.tick()
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logging.error(f"Neurosphere tick loop error: {e}")

    async def stop_ticking(self):
        if self._tick_task:
            self._tick_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._tick_task
            self._tick_task = None

    async def tick(self) -> None:
        self._time += 1
        for character_id in self._characters:
            character = self._characters[character_id]
            self._update_actions(character)
            self._update_possible_actions(character_id)

        for character_id in self._characters:
            character = self._characters[character_id]
            if not character.is_busy():
                controller = self._controllers[character_id]
                try:
                    controller.update(self)
                except Exception as e:
                    logging.error(f"Neurosphere controller update error: {e}")

        for character_id in self._characters:
            if character_id not in self._windows:
                continue
            try:
                await self.update_window(character_id)
            except Exception as e:
                logging.error(f"Neurosphere window update error: {e}")

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
        # генерация игрока
        with open("data/neurosphere/characters/player.json", encoding="utf-8") as file:
            character_data = json.load(file)
        self._generate_character(character_data)
        self._players[player_id] = character_data["id"]

    def remove_player(self, player_id: int) -> None:
        character = self._get_character_by_player_id(player_id)
        self._remove_character(character)

    # endregion

    # region Методы отображения

    async def update_window(self, character_id: int) -> None:
        window = self._windows[character_id]
        new_embed = self._get_viewer_embed(character_id)
        old_embed = window.embeds[0]
        if not embeds_are_equal(new_embed, old_embed):
            await window.edit(embed=new_embed)

    async def add_window(
        self, character_id: int, channel: disnake.abc.Messageable
    ) -> None:
        embed = self._get_viewer_embed(character_id)
        window = await channel.send(embed=embed)
        self._windows[character_id] = window

    async def remove_window(self, character_id: int) -> None:
        window = self._windows[character_id]
        del self._windows[character_id]
        await window.delete()

    def _get_viewer_embed(self, character_id: int) -> disnake.Embed:
        """Генерирует Embed для наблюдателя, основанное на локации, её мире, персонаже и его предметах."""

        world = self._get_world_by_character_id(character_id)
        location = self._get_location_by_character_id(character_id)
        location_description = world.get_location_description(location)

        return disnake.Embed(
            title=f"char_{character_id}",
            description=location_description,
        )

    # endregion методы отображения

    # region Методы информации

    def _get_world_id_by_character_id(self, char_id: int) -> int:
        return self._get_location_by_character_id(char_id).get_world_id()

    def _get_world_by_character_id(self, char_id: int) -> World:
        return self._worlds[self._get_world_id_by_character_id(char_id)]

    def _get_location_id_by_character_id(self, char_id: int) -> int:
        return self._characters[char_id].get_location_id()

    def _get_location_by_character_id(self, char_id: int) -> Location:
        return self._locations[self._get_location_id_by_character_id(char_id)]

    def _get_character_by_player_id(self, player_id: int) -> Character:
        return self._characters[self._players[player_id]]

    def get_character_id_by_player_id(self, player_id: int) -> int:
        return self._characters[self._players[player_id]].get_id()

    def get_controller_by_player_id(self, player_id: int) -> Controller:
        return self._controllers[self._players[player_id]]

    # endregion Методы информации

    # region Методы действий

    def _update_actions(self, character_id: int) -> None:
        """Выполняет нужные по времени действия"""

    def _update_possible_actions(self, character_id: int) -> None:
        """Обновляет possible_actions в character data"""

    # endregion Методы действий


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
        self,
        inter: disnake.ApplicationCommandInteraction,
        name: str = "neurosphere0",
    ) -> None:
        if self.neurosphere:
            await inter.response.send_message("Нейросфера уже запущена", ephemeral=True)
            return
        await inter.response.defer()
        self.neurosphere = Neurosphere(name)
        await self.neurosphere.start_ticking()
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
        await inter.response.send_message("Загрузка...", ephemeral=True, delete_after=1)
        neurosphere = self.neurosphere
        player_id = inter.author.id
        neurosphere.add_player(player_id)
        character_id = neurosphere.get_character_id_by_player_id(player_id)
        await neurosphere.add_window(character_id, inter.channel)

    @commands.slash_command(
        name="leave",
        description="Выйти из Нейросферы",
        guild_ids=GUILD_IDS,
    )
    async def remove_player(
        self,
        inter: disnake.ApplicationCommandInteraction,
    ) -> None:
        if self.neurosphere is None:
            await inter.response.send_message("Нейросфера не запущена.", ephemeral=True)
            return
        await inter.response.send_message("Загрузка...", ephemeral=True, delete_after=1)
        neurosphere = self.neurosphere
        player_id = inter.author.id
        neurosphere.remove_player(player_id)
        character_id = neurosphere.get_character_id_by_player_id(player_id)
        await neurosphere.remove_window(character_id)

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if self.neurosphere is None:
            return
        if message.author.bot:
            return
        # TODO Обработку для PlayerController


def setup(bot):
    bot.add_cog(NeurosphereCog(bot))
