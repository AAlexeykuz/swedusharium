import colorsys
import logging
import random
from typing import TYPE_CHECKING

import disnake

if TYPE_CHECKING:
    from cogwheels.neurosphere import Neurosphere


class Essence:
    def __init__(self, data: dict):
        self.data: dict = data

    def get_data(self, *names):
        # По возможности не использовать
        data = self.data
        for name in names:
            data = data[name]
        return data

    def to_dict(self) -> dict:
        return self.data

    def get_id(self) -> int:
        return self.data["id"]

    def set_id(self, new_id: int) -> None:
        self.data["id"] = new_id


class Location(Essence):
    def __init__(self, data: dict):
        super().__init__(data)

    def get_world_id(self):
        return self.data["world_id"]

    def add_character_id(self, char_id: int) -> None:
        characters: list[int] = self.data["references"]["characters"]
        if char_id in characters:
            logging.error("Два одинаковых персонажа на одной локации")
        characters.append(char_id)

    def remove_character_id(self, char_id: int) -> None:
        characters: list[int] = self.data["references"]["characters"]
        if char_id not in characters:
            logging.error("Попытка удалить персонажа из локации, где его нет")
        characters.remove(char_id)


class Item(Essence):
    def __init__(self, data: dict):
        super().__init__(data)


class Character(Essence):
    def __init__(self, data: dict):
        super().__init__(data)

    def get_location_id(self) -> int:
        return self.data["location_id"]

    def set_active(self, active: bool) -> None:
        self.data["active"] = active

    def is_active(self) -> bool:
        return self.data["active"]

    def is_busy(self) -> bool:
        return bool(self.data["actions"])

    def get_actions(self) -> list[dict[str]]:
        return self.data["actions"]

    def set_actions(self, actions: list[dict[str]]) -> None:
        self.data["actions"] = actions

    def get_commands(self) -> list[dict[str]]:
        return self.data["commands"]

    def set_commands(self, possible_actions: list[dict[str]]) -> None:
        self.data["commands"] = possible_actions


class Controller(Essence):
    def __init__(self, data):
        super().__init__(data)

    def update(self, neurosphere: "Neurosphere") -> None:  # noqa
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

    def update(self, neurosphere: "Neurosphere"):
        pass


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

    # region Методы действий

    def update_item_commands(self, character: Character, ns: "Neurosphere") -> None:  # noqa
        """Ставит персонажу команды для взаимодействия с предметами в инвентаре"""
        logging.error(f"Метод update_item_commands в {type(self)} не реализован")

    def update_character_commands(self, character: Character, ns: "Neurosphere") -> None:  # noqa
        """Ставит персонажу команды для взаимодействия с другими персонажами"""
        logging.error(f"Метод update_character_commands в {type(self)} не реализован")

    def update_structure_commands(self, character: Character, ns: "Neurosphere") -> None:  # noqa
        """Ставит персонажу команды для взаимодействия со структурами"""
        logging.error(f"Метод update_structure_commands в {type(self)} не реализован")

    def update_accessible_location_commands(
        self,
        character: Character,  # noqa
        ns: "Neurosphere",  # noqa
    ) -> None:
        """Ставит персонажу команды для перехода к другим локациям"""
        logging.error(
            f"Метод update_accessible_location_commands в {type(self)} не реализован"
        )

    # endregion Методы действий

    # region Методы отображения

    def get_character_description(self, character: Character, ns: "Neurosphere") -> str:  # noqa
        """Возвращает описание персонажа, его харатеристик и т.п."""
        logging.error(f"Метод get_character_description в {type(self)} не реализован")

    def get_item_descriptions(
        self,
        character: Character,  # noqa
        ns: "Neurosphere",  # noqa
    ) -> dict[int, str]:
        """Возвращает словарь item_id -> описание"""
        logging.error(f"Метод get_item_descriptions в {type(self)} не реализован")

    def get_location_description(self, character: Character, ns: "Neurosphere") -> str:  # noqa
        """Возвращает строку с описанием локации для данного мира."""
        logging.error(f"Метод generate_locations в {type(self)} не реализован")

    def get_character_descriptions(
        self,
        character: "Character",  # noqa
        ns: "Neurosphere",  # noqa
    ) -> dict[int, str]:
        """Возвращает словарь character_id -> описание"""
        logging.error(f"Метод get_character_descriptions в {type(self)} не реализован")

    def get_structure_descriptions(
        self,
        character: "Character",  # noqa
        ns: "Neurosphere",  # noqa
    ) -> dict[int, str]:
        """Возвращает словарь structure_id -> описание"""
        logging.error(f"Метод structure_descriptions в {type(self)} не реализован")

    def get_accessible_location_descriptions(
        self,
        character: Character,  # noqa
        ns: "Neurosphere",  # noqa
    ) -> dict[int, str]:
        """Возвращает словарь: id доступной локации -> описание локации."""
        logging.error(
            f"Метод get_accessible_location_descriptions в {type(self)} не реализован"
        )

    # endregion Методы отображения


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
    embed1: dict = embed1.to_dict()
    embed2: dict = embed2.to_dict()
    for key in embed1.copy():
        value = embed1[key]
        if type(value) is str:
            embed1[key] = value.strip()
        else:
            del embed1[key]
    for key in embed2.copy():
        value = embed2[key]
        if type(value) is str:
            embed2[key] = value.strip()
        else:
            del embed2[key]
    return embed1 == embed2
