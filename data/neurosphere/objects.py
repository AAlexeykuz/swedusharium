import colorsys
import logging
import random

# еее


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

    def get_ai_level(self) -> int:
        """0 - Игрок. 1 - Первостепенный ИИ. 2 - Второстепенный ИИ. 3 - Третьестепенный ИИ."""
        return self.data["ai_level"]

    def set_active(self, active: bool) -> None:
        self.data["active"] = active

    def get_active(self) -> bool:
        return self.data["active"]


class Player(Character):
    def __init__(self, data: dict):
        super().__init__(data)
        self._game_message = None


class World(Essence):
    def __init__(self, data):
        super().__init__(data)

    def generate(self) -> None:
        """Генерирует всё, чтобы мир смог сгенерировать карту локаций."""
        logging.error("Метод generate не реализован")

    def generate_locations(self, location_holder: dict[int, Location]) -> None:  # noqa
        """Должен сгенерировать локации и добавить их к location_holder."""
        logging.error("Метод generate_locations не реализован")

    def generate_character(self, character_data: dict) -> Character:  # noqa
        """Генерирует персонажа, устанавливает ему id локации в этом мире."""
        logging.error("Метод generate_character не реализован")

    def get_location_description(self, location: Location) -> str:  # noqa
        """Должен давать строку с описанием локации для данного мира."""
        logging.error("Метод generate_locations не реализован")


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
