import colorsys
import logging
import random


class Essence:
    def __init__(self, data):
        self.data: dict = data

    def get_id(self) -> int | None:
        return self.data["id"]

    def _set_id(self, object_id):
        self.data["id"] = object_id


class Location(Essence):
    def __init__(self, data):
        super().__init__(data)


class Item(Essence):
    def __init__(self, data):
        super().__init__(data)


class Character(Essence):
    def __init__(self, data):
        super().__init__(data)


class World(Essence):
    def __init__(self, data):
        super().__init__(data)

    def generate(self, new_id: int) -> None:  # noqa
        """Должен генерировать всё, чтобы мир смог сгенерировать карту локаций. Ставит ему новый айди."""
        logging.error("Метод generate не реализован")

    def generate_locations(self, location_holder: dict[int, Location]) -> None:  # noqa
        """Должен сгенерировать локации и добавить их к location_holder"""
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
