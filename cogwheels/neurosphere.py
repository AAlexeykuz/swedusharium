import json

import disnake
from disnake.ext import commands

from constants import GUILD_IDS
from neurosphere.objects import Character, Location, World, new_id
from neurosphere.worlds import Planet

WORLD_TYPES = {"planet": Planet}


class Neurosphere:
    def __init__(self, file_path):
        self._worlds: dict[int, World] = {}
        self._locations: dict[int, Location] = {}
        self._characters = dict[int, Character] = {}

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
            world.generate(new_id(self._worlds))
            world.generate_locations(self._locations)
            self._worlds[world.get_id()] = world

    def _read_locations(self, data: dict) -> None:
        locations = data["locations"]
        for location_data in locations:
            location = Location(location_data)
            self._locations[location.get_id()] = location

    def _read_characters(self, data: dict) -> None:
        characters = data["locations"]
        for character_data in characters:
            character = Character(character_data)
            # TODO сделать генерацию персонажей
            self._characters[character.get_id()] = character


class NeurosphereCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.neurosphere = None

    @commands.slash_command(
        name="neurosphere",
        description="Launches Neurosphere",
        guild_ids=GUILD_IDS,
    )
    async def launch_neurosphere(self, inter: disnake.ApplicationCommandInteraction) -> None:
        await inter.response.defer()
        await inter.followup.send("Нейросферы пока не существует.")

    @commands.slash_command(name="spectate", description="Spectate character", guild_ids=GUILD_IDS)
    async def spectate_character(self, inter: disnake.ApplicationCommandInteraction) -> None:
        if self.neurosphere is None:
            await inter.response.send_message("Нейросфера не запущена.", ephemeral=True)
            return


def setup(bot):
    bot.add_cog(NeurosphereCog(bot))
