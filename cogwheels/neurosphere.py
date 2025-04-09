import asyncio
import contextlib
import json
import logging

import disnake
from disnake.ext import commands

from constants import GUILD_IDS, owner_only
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
        self.worlds: dict[int, World] = {}
        self.locations: dict[int, Location] = {}
        self.characters: dict[int, Character] = {}
        self.items: dict[int, Item] = {}

        self.players: dict[int, int] = {}  # user id -> character id
        self.controllers: dict[int, Controller] = {}  # character id -> controller
        self.windows: dict[int, disnake.Message] = {}  # character id -> message

        self._time: int = 0
        self._tick_time: float = 1
        self._tick_task: asyncio.Task | None = None

        with open(f"data/neurosphere/neurospheres/{name}.json", encoding="utf-8") as f:
            data = json.load(f)

        self._read_data(data)

    # region Методы симуляции

    async def start_ticking(self):
        self._tick_task = asyncio.create_task(self._tick_loop())

    async def stop_ticking(self):
        if self._tick_task:
            self._tick_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._tick_task
            self._tick_task = None

    async def _tick_loop(self):
        try:
            while True:
                await self.tick()
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass

    async def tick(self) -> None:
        self._time += 1

        characters = {
            character_id: character
            for character_id, character in self.characters.items()
            if character.is_active()
        }

        for character_id, character in characters.items():
            self._update_actions(character)
            if not character.is_busy():
                try:
                    controller = self.controllers[character_id]
                    self._update_commands(character)
                    controller.update(self)
                except Exception as e:
                    logging.error(f"Neurosphere controller update error: {e}")

        for character_id in self.characters:
            if character_id not in self.windows:
                continue
            try:
                await self.update_window(character_id)
            except Exception as e:
                logging.error(f"Neurosphere window update error: {e}")

    # endregion Методы симуляции

    # region JSON Методы

    def _read_data(self, data: dict) -> None:
        # первыми негенерируемые объекты, чтобы id не перезаписывались
        self._read_locations(data["locations"])
        self._read_items(data["items"])

        self._read_worlds(data["worlds"])
        self._read_characters(data["characters"])
        self._read_players(data["players"])
        self._time = data["time"]

    def _read_worlds(self, worlds: dict) -> None:
        not_generated_worlds = []

        for world_data in worlds:
            if world_data["id"] is not None:
                world_class = WORLD_TYPES[world_data["type"]]
                world = world_class(world_data)
                self.worlds[world_data["id"]] = world
            else:
                not_generated_worlds.append(world_data)

        for world_data in not_generated_worlds:
            self._generate_world(world_data)

    def _read_locations(self, locations: dict) -> None:
        for location_data in locations:
            location = Location(location_data)
            self.locations[location_data["id"]] = location

    def _read_characters(self, characters: dict) -> None:
        """Загружает персонажей в self._characters если у них есть id
        Если id нет, то генерирует их через мир и добавляет в локацию"""
        not_generated_characters = []

        for character_data in characters:
            if character_data["id"] is not None:
                character = Character(character_data)
                self.characters[character_data["id"]] = character
                self._add_controller(
                    character_data["id"],
                    character_data["controller"],
                )
                if type(self.controllers[character_data["id"]]) is PlayerController:
                    character.data["active"] = False
            else:
                not_generated_characters.append(character_data)

        for character_data in not_generated_characters:
            self._generate_character(character_data)

    def _read_items(self, items: dict) -> None:
        for item_data in items:
            item = Item(item_data)
            self.locations[item_data["id"]] = item

    def _read_players(self, players: dict[str, int]) -> None:
        self.players = {int(k): v for k, v in players.items()}

    def write_data(self, name: str) -> None:
        """Сохраняет Нейросферу как json в data/neurosphere/neurospheres/{name}.json

        Args:
            name (str): Название json файла (без .json)
        """
        active_player_characters = []
        for character_id, character in self.characters.items():
            controller = self.controllers[character_id]
            if type(controller) is PlayerController:
                self._remove_character(character)
                active_player_characters.append(character)
        data = {
            "worlds": [world.to_dict() for world in self.worlds.values()],
            "locations": [location.to_dict() for location in self.locations.values()],
            "characters": [character.to_dict() for character in self.characters.values()],
            "items": [item.to_dict() for item in self.items.values()],
            "players": self.players,
            "time": self._time,
        }
        for character in active_player_characters:
            self._add_character(character)

        # def custom_serializer(obj):
        #     if isinstance(obj, np.integer):
        #         return int(obj)  # Convert NumPy integers to Python int
        #     if isinstance(obj, np.floating):
        #         return float(obj)  # Convert NumPy floats to Python float
        #     if isinstance(obj, np.ndarray):
        #         return obj.tolist()  # Convert NumPy arrays to lists
        #     raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        with open(
            f"data/neurosphere/neurospheres/{name}.json", "w", encoding="utf-8"
        ) as file:
            json.dump(data, file, indent=2, ensure_ascii=False)

    # endregion JSON Методы

    # region Методы управления

    def _generate_world(self, world_data) -> None:
        new_id_ = new_id(self.worlds)
        world_data["id"] = new_id_
        world_class = WORLD_TYPES[world_data["type"]]
        world = world_class(world_data)
        world.generate()
        world.generate_locations(self.locations)
        self.worlds[new_id(self.worlds)] = world

    def _generate_character(self, character_data) -> None:
        """Генерирует персонажа и добавляет его в Нейросферу"""
        character_id = new_id(self.characters)
        character_data["id"] = character_id
        world_id = character_data["generation"]["world_id"]
        world = self.worlds[world_id]
        world.generate_character(character_data, self.characters, self.items)
        character = self.characters[character_id]
        self._add_character(character)
        self._add_controller(character_id, character_data["controller"])

    def _add_controller(self, character_id: int, controller_data) -> None:
        controller_class = CONTROLLER_TYPES[controller_data["type"]]
        controller = controller_class(controller_data)
        self.controllers[character_id] = controller

    def _add_character(self, character: Character) -> None:
        """Включает персонажа и добавляет его в локацию"""
        char_id = character.get_id()
        location = self.get_location_by_character_id(char_id)
        location.add_character_id(char_id)
        character.set_active(True)

    def _remove_character(self, character: Character) -> None:
        """Выключает персонажа и удаляет его из локации"""
        char_id = character.get_id()
        location = self.get_location_by_character_id(char_id)
        location.remove_character_id(char_id)
        character.set_active(False)

    def add_player(self, player_id: int) -> None:
        if player_id in self.players:
            character = self.get_character_by_player_id(player_id)
            if not character.is_active():
                self._add_character(character)
            return
        # генерация игрока
        with open("data/neurosphere/characters/player.json", encoding="utf-8") as file:
            character_data = json.load(file)
        self._generate_character(character_data)
        self.players[player_id] = character_data["id"]

    def remove_player(self, player_id: int) -> None:
        character = self.get_character_by_player_id(player_id)
        self._remove_character(character)

    # endregion

    # region Методы отображения

    async def update_window(self, character_id: int) -> None:
        window = self.windows[character_id]
        new_embed = self._get_viewer_embed(character_id)
        old_embed = window.embeds[0]
        if not embeds_are_equal(new_embed, old_embed):
            await window.edit(embed=new_embed)

    async def add_window(
        self, character_id: int, channel: disnake.abc.Messageable
    ) -> None:
        embed = self._get_viewer_embed(character_id)
        window = await channel.send(embed=embed)
        self.windows[character_id] = window

    async def remove_window(self, character_id: int) -> None:
        window = self.windows[character_id]
        del self.windows[character_id]
        await window.delete()

    def _get_viewer_embed(self, character_id: int) -> disnake.Embed:
        """Генерирует Embed для наблюдателя, основываясь на локации, мире и персонаже.
        Запускается с готовыми commands и actions в персонаже.

        Args:
            character_id (int): Id персонажа, для которого создаётся embed

        Returns:
            disnake.Embed: Embed, содержащий всю нужную информацию для наблюдения за персонажем
        """

        world = self.get_world_by_character_id(character_id)
        location = self.get_location_by_character_id(character_id)
        character = self.characters[character_id]
        commands = character.get_commands()

        location_description = world.get_location_description(location)
        accessible_location_descriptions = world.get_accessible_location_descriptions(
            location, self
        )

        character_description = character.get_description()
        item_descriptions = character.get_item_descriptions(self)

        character_descriptions = location.get_character_descriptions(self)
        structure_descriptions = location.get_structure_descriptions(self)

        embed = disnake.Embed(
            description=character_description,
        )

        embed.add_field(
            name="Инвентарь",
            value=self._make_embed_value(item_descriptions, commands, "items"),
            inline=False,
        )

        embed.add_field(
            name="Локация",
            value=location_description,
            inline=False,
        )

        embed.add_field(
            name="Персонажи рядом",
            value=self._make_embed_value(character_descriptions, commands, "characters"),
            inline=False,
        )
        embed.add_field(
            name="Структуры рядом",
            value=self._make_embed_value(structure_descriptions, commands, "structures"),
            inline=False,
        )

        embed.add_field(
            name="Куда пойти",
            value=self._make_embed_value(
                accessible_location_descriptions, commands, "locations"
            ),
            inline=False,
        )

        embed.set_author(
            name=f"Char_{character_id}",
        )

        return embed

    @staticmethod
    def _make_embed_value(
        descriptions: dict[int, str], commands: list[dict], category: str
    ) -> str:
        """Собирает описания вместе с командами в одну строку"""
        commands = [command for command in commands if command["category"] == category]
        output = []
        for object_id, description in descriptions.items():
            line = description
            command_descriptions = [
                f"\t(!{command['name']})"
                for command in commands
                if command["object_id"] == object_id
            ]
            if command_descriptions:
                line += "\n" + "\n".join(command_descriptions)
            output.append(line)
        return "\n".join(output)

    # endregion Методы отображения

    # region Методы информации

    def is_player(self, player_id) -> bool:
        return player_id in self.players

    def get_world_id_by_character_id(self, char_id: int) -> int:
        return self.get_location_by_character_id(char_id).get_world_id()

    def get_world_by_character_id(self, char_id: int) -> World:
        return self.worlds[self.get_world_id_by_character_id(char_id)]

    def get_location_id_by_character_id(self, char_id: int) -> int:
        return self.characters[char_id].get_location_id()

    def get_location_by_character_id(self, char_id: int) -> Location:
        return self.locations[self.get_location_id_by_character_id(char_id)]

    def get_character_by_player_id(self, player_id: int) -> Character:
        return self.characters[self.players[player_id]]

    def get_character_id_by_player_id(self, player_id: int) -> int:
        return self.characters[self.players[player_id]].get_id()

    def get_controller_by_player_id(self, player_id: int) -> Controller:
        return self.controllers[self.players[player_id]]

    # endregion Методы информации

    # region Методы действий

    def _update_actions(self, character: Character) -> None:
        """Выполняет нужные по времени действия"""
        # TODO Реализовать

    def _update_commands(self, character: Character) -> None:
        """Обновляет commands в character data"""
        # TODO Реализовать

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
        name="save-neurosphere",
        description="Сохранить Нейросферу",
        guild_ids=GUILD_IDS,
    )
    @owner_only()
    async def save_neurosphere(
        self,
        inter: disnake.ApplicationCommandInteraction,
        name: str,
    ) -> None:
        if name == "neurosphere0":
            await inter.response.send_message(
                "Нельзя сохранить Нейросферу под таким именем"
            )
            return
        if self.neurosphere is None:
            await inter.response.send_message("Нейросфера не запущена", ephemeral=True)
            return
        self.neurosphere.write_data(name)
        await inter.response.send_message("Нейросфера сохранена")

    @commands.slash_command(
        name="play",
        description="Играть в Нейросфере",
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
        ns = self.neurosphere
        player_id = inter.author.id
        ns.add_player(player_id)
        character_id = ns.get_character_id_by_player_id(player_id)
        if character_id in ns.windows:
            await ns.windows[character_id].delete()
        await ns.add_window(character_id, inter.channel)

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
