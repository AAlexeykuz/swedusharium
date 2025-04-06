import colorsys
import logging
import random

import disnake


class Essence:
    def __init__(self, data: dict):
        self.data: dict = data

    def get_data(self, *names):
        # По возможности не использовать
        data = self.data
        for name in names:
            data = data[name]
        return data

    def get_id(self) -> int:
        return self.data["id"]

    def set_id(self, new_id: int) -> None:
        self.data["id"] = new_id


class Location(Essence):
    def __init__(self, data: dict):
        super().__init__(data)
        self.characters: list[int] = self.data["references"]["characters"]

    def get_world_id(self):
        return self.data["world_id"]

    def add_character_id(self, char_id: int) -> None:
        if char_id in self.characters:
            logging.error("Два одинаковых персонажа на одной локации")
        self.characters.append(char_id)

    def remove_character_id(self, char_id: int) -> None:
        if char_id not in self.characters:
            logging.error("Попытка удалить пероснажа из локации, где его нет")
        self.characters.remove(char_id)


class Item(Essence):
    def __init__(self, data: dict):
        super().__init__(data)


class Action(Essence):
    def __init__(self, data: dict):
        super().__init__(data)

    def get_name(self):
        return self.data["name"]

    def get_arguments(self):
        return self.data["arguments"]


class Character(Essence):
    def __init__(self, data: dict):
        super().__init__(data)

    def get_location_id(self) -> int:
        return self.data["location_id"]

    def get_state(self) -> int:
        return self.data["state"]

    def set_active(self, active: bool) -> None:
        self.data["active"] = active

    def get_active(self) -> bool:
        return self.data["active"]

    def is_busy(self) -> bool:
        return bool(self.data["actions"])

    def get_actions(self) -> list[dict[str]]:
        return self.data["actions"]

    def set_actions(self, actions: list[dict[str]]) -> None:
        self.data["actions"] = actions

    def get_possible_actions(self) -> list[dict[str]]:
        return self.data["possible_actions"]

    def set_possible_actions(self, possible_actions: list[dict[str]]) -> None:
        self.data["possible_actions"] = possible_actions


class Controller(Essence):
    def __init__(self, data):
        super().__init__(data)

    def update(self, neurosphere) -> None:  # noqa
        """Вызывается, когда действия персонажа заканчиваются.
        Обновляет возможные действия и побуждает управляющего дать новые действия."""
        logging.error(f"Метод act в {type(self)} не реализован")

    def to_dict(self) -> dict:
        """Превращает контроллер в словарь для json"""
        logging.error(f"Метод to_dict в {type(self)} не реализован")


class GPTController(Controller):
    """Контроллер для GPT"""

    def __init__(self, data) -> None:
        super().__init__(data)


class PlayerController(Controller):
    """Контроллер для людей"""

    def __init__(self, data) -> None:
        super().__init__(data)
        self.game_message: disnake.Message | None = None

    async def set_game_message(self, message: disnake.Message | None) -> None:
        if self.game_message is not None:
            await self.game_message.delete()
        self.game_message = message


class World(Essence):
    def __init__(self, data):
        super().__init__(data)

    def generate(self) -> None:
        """Генерирует всё, чтобы мир смог сгенерировать карту локаций."""
        logging.error(f"Метод generate в {type(self)} не реализован")

    def generate_locations(self, location_holder: dict[int, Location]) -> None:  # noqa
        """Генерирует локации и добавляет их к location_holder."""
        logging.error(f"Метод generate_locations в {type(self)} не реализован")

    def generate_character(
        self,
        character_data: dict,  # noqa
        character_holder: dict[int, Character],  # noqa
        item_holder: dict[int, Item],  # noqa
    ) -> None:
        """Генерирует персонажа, устанавливает ему id локации и добавляет его к character_holder.
        Генерирует его предметы и добавляет их к item_holder."""
        logging.error(f"Метод generate_character в {type(self)} не реализован")

    def get_location_description(self, location: Location) -> str:  # noqa
        """Возвращает строку с описанием локации для данного мира."""
        logging.error(f"Метод generate_locations в {type(self)} не реализован")


def generate_pleasant_color() -> tuple[int, int, int]:
    hue = random.uniform(0, 360)
    saturation = random.uniform(0.25, 0.45)
    brightness = random.uniform(0.5, 0.85)
    r, g, b = colorsys.hsv_to_rgb(hue / 360, saturation, brightness)
    return int(r * 255), int(g * 255), int(b * 255)


def new_id(holder: dict) -> int:
    if not holder:
        return 0
    return max(holder.keys()) + 1


def embeds_are_equal(embed1: disnake.Embed, embed2: disnake.Embed) -> bool:
    embed1 = embed1.to_dict()
    embed2 = embed2.to_dict()
    for key in embed1:
        value = embed1[key]
        if type(value) is str:
            embed1[key] = value.strip()
        else:
            del embed1[key]
    for key in embed2:
        value = embed2[key]
        if type(value) is str:
            embed2[key] = value.strip()
        else:
            del embed2[key]
    return embed1 == embed2
