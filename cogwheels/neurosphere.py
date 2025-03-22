import colorsys
import json
import logging
import random
import time

import disnake
import noise
import numpy as np
from disnake.ext import commands
from sklearn.neighbors import BallTree

from constants import GUILD_IDS


class Character:
    def __init__(self, data):
        self.data = data

        # TODO: добавить current_action персонажу


def generate_pleasant_color():
    hue = random.uniform(0, 360)  # Full hue spectrum
    # Avoid very pale or overly intense colors
    saturation = random.uniform(0.25, 0.45)
    brightness = random.uniform(0.5, 0.85)
    # Keep colors from being too dark or too bright
    r, g, b = colorsys.hsv_to_rgb(hue / 360, saturation, brightness)
    return int(r * 255), int(g * 255), int(b * 255)


class Item:
    def __init__(self):
        pass


class Location:
    def __init__(self):
        self.biome = None

    def set_biome(self, biome):
        self.biome = biome


class World:
    def __init__(self):
        self.locations = {}

    def get_location(self, *_):
        logging.error("Метод get_location не реализован")

    def get_accessible_location(self, *_):
        logging.error("Метод get_accessible_location не реализован")


class Planet(World):
    def __init__(self, file_path):
        super().__init__()

        with open(file_path, encoding="utf-8") as f:
            self.data = json.load(f)

        self.points = np.array(self.data["points"])
        self.tree: BallTree = None  # type: ignore
        self.radius: float = self.data["generation"]["radius"]

        self.tectonic_map: dict[tuple[float, float], int] = {}
        self.height_map: dict[tuple[float, float], float] = {}
        self.heat_map: dict[tuple[float, float], float] = {}
        self.precipitation_map: dict[tuple[float, float], int] = {}

        biome_string = """polar	tundra	tundra	tundra	taiga	taiga	taiga	taiga	temperate_rainforest	temperate_rainforest	temperate_rainforest	temperate_rainforest	temperate_rainforest	swamp	swamp	swamp	swamp	tropical_rainforest	tropical_rainforest	tropical_rainforest
polar	tundra	tundra	tundra	taiga	taiga	taiga	taiga	temperate_rainforest	temperate_rainforest	temperate_rainforest	temperate_rainforest	swamp	swamp	swamp	swamp	tropical_rainforest	tropical_rainforest	tropical_rainforest	tropical_rainforest
polar	tundra	tundra	tundra	taiga	taiga	taiga	taiga	seasonal_forest	seasonal_forest	seasonal_forest	seasonal_forest	seasonal_forest	seasonal_forest	seasonal_forest	seasonal_forest	tropical_seasonal_forest	tropical_seasonal_forest	tropical_seasonal_forest	tropical_seasonal_forest
polar	tundra	tundra	tundra	taiga	taiga	taiga	taiga	seasonal_forest	seasonal_forest	seasonal_forest	seasonal_forest	seasonal_forest	seasonal_forest	seasonal_forest	tropical_seasonal_forest	tropical_seasonal_forest	tropical_seasonal_forest	tropical_seasonal_forest	tropical_seasonal_forest
polar	tundra	tundra	tundra	taiga	taiga	taiga	taiga	seasonal_forest	seasonal_forest	seasonal_forest	seasonal_forest	plains	plains	plains	plains	savanna	savanna	savanna	savanna
polar	tundra	tundra	tundra	taiga	taiga	taiga	taiga	plains	plains	plains	plains	plains	plains	plains	savanna	savanna	savanna	savanna	savanna
polar	tundra	tundra	tundra	taiga	taiga	taiga	taiga	plains	plains	plains	plains	plains	plains	plains	savanna	savanna	savanna	savanna	savanna
polar	tundra	tundra	tundra	taiga	taiga	taiga	taiga	plains	plains	plains	plains	steppe	steppe	steppe	desert	tropical_desert	tropical_desert	tropical_desert	tropical_desert
polar	tundra	tundra	tundra	taiga	taiga	plains	plains	steppe	steppe	steppe	steppe	desert	desert	desert	desert	tropical_desert	tropical_desert	tropical_desert	tropical_desert
polar	tundra	tundra	tundra	taiga	plains	plains	steppe	steppe	steppe	steppe	steppe	desert	desert	desert	desert	tropical_desert	tropical_desert	tropical_desert	tropical_desert
"""
        self.biome_table = self._table(biome_string)[::-1]

        # debug
        self.draw_tectonics: bool = False
        self.borders: list[tuple[float, float]] = []

        self.read_data()

    def read_data(self):
        if self.data["generated"]:
            self.tree = BallTree(self.points, metric="haversine")
            return
        self._generate()
        # self._load_maps()

    def _load_maps(self):
        for lat, lon in self.tectonic_map.items():
            print(lat, lon)

    def statistics(self):
        ground_temperatures = []
        for point in self.points:
            point_key = tuple(point.tolist())
            height = self.height_map[point_key]
            if height > self.data["generation"]["water_level"]:
                ground_temperatures.append(self.heat_map[point_key])
        logging.info(f"Средняя температура: {np.average(list(self.heat_map.values()))}")
        logging.info(f"Средняя температура на суше: {np.average(ground_temperatures)}")

    # region Методы генерации

    @staticmethod
    def _table(biome_string):
        return [line.split("\t") for line in biome_string.split("\n") if line]

    def _generate(self):
        start_time = time.time()

        # устанавливаем сид
        seed = self.data["generation"]["seed"]
        if seed is None:
            seed = random.randint(0, 10000)
            self.data["generation"]["seed"] = seed
        random.seed(seed)
        logging.info(f"Seed: {seed}")

        # генерируем точки на сфере
        self.points = self._generate_sphere_points()
        self.tree = BallTree(self.points, metric="haversine")

        # генерируем карты
        self._generate_tectonic_map()
        self._generate_height_map()
        self._generate_heat_map()
        self._generate_precipitation_map()
        self._generate_locations()

        logging.info(f"Генерация планеты заняла {time.time() - start_time:.2f}с")

    def _generate_sphere_points(self):
        """Генерирует n точек (вычисляется по площади сферы) на сфере и возвращает массив из широты и долготы"""
        n = round(4 * np.pi * self.radius**2)
        indices = np.arange(n, dtype=np.float32) + 0.5
        phi = np.arccos(1 - 2 * indices / n)
        theta = (np.pi * (1 + 5**0.5)) * indices
        latitude = np.pi / 2 - phi
        longitude = theta % (2 * np.pi)
        return np.column_stack((latitude, longitude))

    def _generate_tectonic_map(self):
        start_time = time.time()

        noise_point_keys = self._generate_tectonic_noise_point_keys()

        big_tectonics_tree, small_plate_generation_points = self._generate_big_tectonic_plates(
            noise_point_keys,
        )

        self._generate_small_tectonic_plates(
            noise_point_keys,
            big_tectonics_tree,
            small_plate_generation_points,
        )

        logging.info(f"Генерация тектонических плит: {time.time() - start_time:.2f}с")

    def _generate_tectonic_noise_point_keys(self):
        noise_point_keys: dict[tuple[float, float], tuple[float, float]] = {}

        tectonics_data = self.data["generation"]["tectonics"]

        noise_map_distance = self._generate_perlin_noise(
            tectonics_data["tectonic_distance_noise_octaves"],
            tectonics_data["tectonic_distance_noise_coefficients"],
        )
        noise_map_bearing = self._generate_perlin_noise(
            tectonics_data["tectonic_bearing_noise_octaves"],
            tectonics_data["tectonic_bearing_noise_coefficients"],
        )

        for point in self.points:
            point_key = tuple(point.tolist())
            noise_distance = noise_map_distance[point_key] / self.radius
            noise_bearing = noise_map_bearing[point_key]
            lat, lon = point
            noise_point_keys[point_key] = self._haversine_move(
                lat, lon, noise_bearing, noise_distance
            )

        return noise_point_keys

    def _generate_big_tectonic_plates(self, noise_point_keys):
        tectonics_data = self.data["generation"]["tectonics"]

        random_points = np.array(
            random.choices(self.points, k=tectonics_data["big_tectonics_number"])
        )
        big_tectonics_points = self._relaxate_points(random_points)
        big_tectonics_tree = BallTree(big_tectonics_points, metric="haversine")

        small_plate_generation_points: list[tuple[float, float]] = []
        for point in self.points:
            point_key = tuple(point.tolist())
            query_point = [noise_point_keys[point_key]]
            dist, indices = big_tectonics_tree.query(query_point, k=2)
            dist, indices = dist[0], indices[0]

            distance_delta = abs(dist[0] - dist[1])
            if distance_delta < tectonics_data["small_tectonics_delta"]:
                small_plate_generation_points.append(point)
            else:
                self.tectonic_map[point_key] = indices[0]

        return big_tectonics_tree, small_plate_generation_points

    def _generate_small_tectonic_plates(
        self,
        noise_point_keys,
        big_tectonics_tree,
        small_plate_generation_points,
    ):
        tectonics_data = self.data["generation"]["tectonics"]

        small_tectonics_points = np.array(
            random.choices(
                small_plate_generation_points,
                k=tectonics_data["small_tectonics_number"],
            )
        )
        small_tectonics_tree = BallTree(small_tectonics_points, metric="haversine")

        for point in small_plate_generation_points:
            point_key = tuple(point.tolist())
            query_point = [noise_point_keys[point_key]]
            dist, indices = small_tectonics_tree.query(query_point, k=1)
            dist, indices = dist[0], indices[0]
            dist, index = (
                dist[0],
                indices[0] + tectonics_data["big_tectonics_number"],
            )

            if dist > tectonics_data["small_tectonics_max_distance"]:
                index = big_tectonics_tree.query(query_point, k=1, return_distance=False)[0][0]
            self.tectonic_map[point_key] = index

    def _generate_height_map(self):
        start_time = time.time()

        height_data = self.data["generation"]["height"]
        tectonics_data = self.data["generation"]["tectonics"]
        tectonics_number: int = (
            tectonics_data["big_tectonics_number"] + tectonics_data["small_tectonics_number"]
        )

        self._generate_height_noise(tectonics_number)

        # распределение плит на океанические и континентальные
        numbers = list(range(tectonics_number))
        random.shuffle(numbers)
        ratio = round(len(numbers) * height_data["oceanic_plates_ratio"])
        oceanic_plates = numbers[:ratio]

        self._add_plate_type_delta_to_height_map(oceanic_plates)

        self._add_plate_conflict_to_height_map(tectonics_number, oceanic_plates)

        self.height_map = self._normalize_map_by_min_max(
            self.height_map,
            height_data["min_height"],
            height_data["max_height"],
        )

        # считаем уровень моря и гор
        self.data["generation"]["water_level"] = np.percentile(
            np.array(list(self.height_map.values())),
            height_data["water_percentage"],
        )

        self.data["generation"]["mountain_height"] = np.percentile(
            np.array(list(self.height_map.values())),
            100 - height_data["mountain_percentage"],
        )

        # debug
        if self.draw_tectonics:
            self._draw_tectonic_borders()

        logging.info(f"Генерация карты высот: {time.time() - start_time:.2f}с")

    def _generate_height_noise(self, tectonics_number) -> None:
        """Заполняет self.heigth_map значениями шума от 0 до 1 с разным сдвигом по плитам"""
        height_data = self.data["generation"]["height"]

        tectonic_shifts = [
            np.array(
                [
                    (random.random() - 0.5) * 2,
                    (random.random() - 0.5) * 2,
                    (random.random() - 0.5) * 2,
                ]
            )
            for _ in range(tectonics_number)
        ]

        for point_key in self.tectonic_map:
            index = self.tectonic_map[point_key]
            x, y, z = self._spherical_to_cartesian(*point_key) + tectonic_shifts[index]
            noise_value = 0
            for octave, k in zip(
                height_data["height_noise_octaves"],
                height_data["height_noise_coefficients"],
            ):
                noise_value += k * noise.pnoise3(x, y, z, octaves=octave)
            self.height_map[point_key] = noise_value
        self.height_map = self._normalize_map_by_min_max(self.height_map, 0, 1)

    def _add_plate_type_delta_to_height_map(self, oceanic_plates):
        height_data = self.data["generation"]["height"]
        for point in self.points:
            point_key: tuple[float, float] = tuple(point.tolist())
            tectonic_index = self.tectonic_map[point_key]
            if tectonic_index in oceanic_plates:
                self.height_map[point_key] += height_data["oceanic_plate_height_delta"]
            else:
                self.height_map[point_key] += height_data["continental_plate_height_delta"]

    def _add_plate_conflict_to_height_map(self, tectonics_number, oceanic_plates):
        height_data = self.data["generation"]["height"]
        tectonic_movement: list[tuple[float, float]] = [
            (
                random.random() * 2 * np.pi,
                random.random() * height_data["max_tectonic_speed"],
            )
            for _ in range(tectonics_number)
        ]
        for point1 in self.points:
            point_key_1 = tuple(point1.tolist())
            lat, lon = point_key_1
            nearest_points = self._find_nearest_points_by_distance(
                lat, lon, height_data["mountain_width"]
            )
            tectonic_index_1 = self.tectonic_map[point_key_1]
            conflict_height_delta = 0
            for point2 in nearest_points:
                x1, y1 = point1
                x2, y2 = point2

                if (x1, y1) == (x2, y2):
                    continue

                point_key_2 = tuple(point2.tolist())
                tectonic_index_2 = self.tectonic_map[point_key_2]
                if tectonic_index_1 == tectonic_index_2:
                    continue

                # вычисляем конфликт векторов AB и CD
                point_a: tuple[float, float] = point_key_1
                vector1: tuple[float, float] = tectonic_movement[tectonic_index_1]
                point_b = self._haversine_move(*point_a, *vector1)

                point_c: tuple[float, float] = point_key_2
                vector2: tuple[float, float] = tectonic_movement[tectonic_index_2]
                point_d = self._haversine_move(*point_c, *vector2)

                conflict = self._calculate_vector_conflict(point_a, point_b, point_c, point_d)

                if tectonic_index_1 in oceanic_plates and tectonic_index_2 in oceanic_plates:
                    k = height_data["oceanic_tectonic_conflict_coefficient"]
                else:
                    k = height_data["tectonic_conflict_coefficient"]
                conflict_height_delta += conflict / (2 * height_data["max_tectonic_speed"]) * k

            self.height_map[point_key_1] += conflict_height_delta

    def _draw_tectonic_borders(self):
        for point in self.points:
            point_key = tuple(point.tolist())
            tectonic_index = self.tectonic_map[point_key]
            lat, lon = point
            nearest_points = self._find_nearest_points_by_distance(lat, lon, 1.1 / self.radius)
            for point2 in nearest_points:
                x1, y1 = point
                x2, y2 = point2
                if (x1, y1) == (x2, y2):
                    continue
                point_key_2 = tuple(point2.tolist())
                tectonic_index_2 = self.tectonic_map[point_key_2]
                if tectonic_index == tectonic_index_2:
                    continue
                self.borders.append(point_key)

    def _generate_heat_map(self):
        start_time = time.time()

        self._generate_heat_noise()
        self._add_latitude_delta_to_heat_map()
        self._add_height_delta_to_heat_map()

        logging.info(f"Генерация карты тепла: {time.time() - start_time:.2f}с")

    def _generate_heat_noise(self):
        heat_data = self.data["generation"]["temperature"]

        # генерируем шум
        noise_map = self._generate_perlin_noise(
            heat_data["heat_noise_octaves"], heat_data["heat_noise_coefficients"]
        )

        # нормализуем шум
        noise_map = self._normalize_map_by_min_max(
            noise_map, heat_data["min_heat_noise"], heat_data["max_heat_noise"]
        )

        for point in self.points:
            point_key = tuple(point.tolist())
            self.heat_map[point_key] = noise_map[point_key]
        self.heat_map = self._normalize_map_by_min_max(self.heat_map, 0, 1)

    def _add_latitude_delta_to_heat_map(self):
        heat_data = self.data["generation"]["temperature"]
        for point in self.points:
            # вычисление температуры от -1 до 1 по косинусу + смещение от чатагпт
            point_key = tuple(point.tolist())
            lat, lon = point
            x = np.cos(lat) * np.cos(lon)
            y = np.cos(lat) * np.sin(lon)
            z = np.sin(lat)
            y1 = (
                np.sin(heat_data["heat_rotation_angle"]) * x
                + np.cos(heat_data["heat_rotation_angle"]) * y
            )
            z1 = z
            z2 = (
                np.sin(heat_data["heat_tilt_angle"]) * y1
                + np.cos(heat_data["heat_tilt_angle"]) * z1
            )
            effective_lat = np.arcsin(z2)
            self.heat_map[point_key] += np.cos(effective_lat) + heat_data["heat_delta"]
        self.heat_map = self._normalize_map_by_min_max(
            self.heat_map, heat_data["min_temp"], heat_data["max_temp"]
        )

    def _add_height_delta_to_heat_map(self):
        heat_data = self.data["generation"]["temperature"]
        water_level = self.data["generation"]["water_level"]
        for point in self.points:
            point_key = tuple(point.tolist())
            height = self.height_map[point_key]
            if height > water_level:
                self.heat_map[point_key] -= (height - water_level) * heat_data["altitude_heat_k"]

        self.heat_map = self._normalize_map_by_min_max(
            self.heat_map, heat_data["min_temp"], heat_data["max_temp"]
        )

    def _generate_precipitation_map(self):
        start_time = time.time()

        self._generate_precipitation_noise()
        self._add_latitude_delta_to_precipitation_map()
        self._add_height_delta_to_precipitation_map()

        logging.info(f"Генерация карты осадков: {time.time() - start_time:.2f}с")

    def _generate_precipitation_noise(self):
        precipitation_data = self.data["generation"]["precipitation"]

        # генерируем шум
        noise_map = self._generate_perlin_noise(
            precipitation_data["precipitation_noise_octaves"],
            precipitation_data["precipitation_noise_coefficients"],
        )

        # нормализуем шум
        noise_map = self._normalize_map_by_min_max(
            noise_map,
            precipitation_data["min_precipitation_noise"],
            precipitation_data["max_precipitation_noise"],
        )

        for point in self.points:
            point_key = tuple(point.tolist())
            self.precipitation_map[point_key] = noise_map[point_key]

        self.precipitation_map = self._normalize_map_by_min_max(self.precipitation_map, 0, 1)

    def _add_latitude_delta_to_precipitation_map(self):
        precipitation_data = self.data["generation"]["precipitation"]
        for point in self.points:
            # вычисление осадков от -1 до 1 по косинусу ((4x + пи)/2) в квадрате + вращение от чатагпт
            point_key = tuple(point.tolist())
            lat, lon = point
            x = np.cos(lat) * np.cos(lon)
            y = np.cos(lat) * np.sin(lon)
            z = np.sin(lat)
            y1 = (
                np.sin(precipitation_data["precipitation_rotation_angle"]) * x
                + np.cos(precipitation_data["precipitation_rotation_angle"]) * y
            )
            z1 = z
            z2 = (
                np.sin(precipitation_data["precipitation_tilt_angle"]) * y1
                + np.cos(precipitation_data["precipitation_tilt_angle"]) * z1
            )
            effective_lat = np.arcsin(z2)
            self.precipitation_map[point_key] += (
                np.cos((4 * effective_lat + np.pi) / 2) ** 2
                + precipitation_data["precipitation_delta"]
            )
        self.precipitation_map = self._normalize_map_by_min_max(
            self.precipitation_map,
            precipitation_data["min_precipitation"],
            precipitation_data["max_precipitation"],
        )

    def _add_height_delta_to_precipitation_map(self):
        precipitation_data = self.data["generation"]["precipitation"]
        water_level = self.data["generation"]["water_level"]
        for point in self.points:
            point_key = tuple(point.tolist())
            height = self.height_map[point_key]
            if (
                water_level
                < height
                < water_level + precipitation_data["precipitation_increase_level"]
            ):
                self.precipitation_map[point_key] += precipitation_data[
                    "water_precipitation_increase"
                ]
            elif height > water_level:
                self.precipitation_map[point_key] += (height - water_level) * precipitation_data[
                    "altitude_precipitation_k"
                ]
        self.precipitation_map = self._normalize_map_by_min_max(
            self.precipitation_map,
            precipitation_data["min_precipitation"],
            precipitation_data["max_precipitation"],
        )

    @staticmethod
    def _generate_perlin_noise_static(points, octaves: list[float], coefficients: list[float]):
        noise_map = {}

        for point in points:
            lat, lon = point
            x, y, z = Planet._spherical_to_cartesian(lat, lon)

            noise_value = 0

            for octave, k in zip(octaves, coefficients):
                noise_value += k * noise.pnoise3(x, y, z, octaves=octave)

            point_key = tuple(point.tolist())
            noise_map[point_key] = noise_value

        return noise_map

    def _generate_perlin_noise(self, octaves: list[float], coefficients: list[float]):
        return self._generate_perlin_noise_static(self.points, octaves, coefficients)

    def _generate_locations(self, *_):
        for point in self.points:
            point_key = tuple(point.tolist())
            location = Location()
            height = self.height_map[point_key]
            temperature = self.heat_map[point_key]
            precipitation = self.precipitation_map[point_key]
            biome = self._generate_biome(height, temperature, precipitation)
            location.set_biome(biome)
            self.locations[point_key] = location

    def _generate_biome(self, height, temperature, precipitation):
        water_level = self.data["generation"]["water_level"]
        mountain_height = self.data["generation"]["mountain_height"]
        if height < water_level:
            if temperature < -60:
                return "glacier"
            return "marine"
        if height > mountain_height:
            if temperature < -60:
                return "snowy_mountain"
            return "mountain"

        # expecting values from -100 to 100
        horizontal_index = int((temperature + 100) // 10)
        if horizontal_index > 19:
            horizontal_index = 19
        elif horizontal_index < 0:
            horizontal_index = 0

        vertical_index = int(precipitation // 10)
        if vertical_index >= 10:
            vertical_index = 9
        elif vertical_index < 0:
            vertical_index = 0

        return self.biome_table[vertical_index][horizontal_index]

    def generate_colors_by_map(self, point_map):
        colors = {}
        point_map = self._normalize_map_by_min_max(point_map, 0, 1)
        for point in self.points:
            point_key = tuple(point.tolist())
            c = round(point_map[point_key] * 255)
            colors[point_key] = (c, c, c)
        return colors

    def generate_colors_by_height_map(self, height_map):
        colors = {}
        height_map = self._normalize_map_by_min_max(height_map, 0, 1)
        threshold = np.percentile(
            np.array(list(height_map.values())),
            self.data["generation"]["height"]["water_percentage"],
        )
        for point in self.points:
            point_key = tuple(point.tolist())
            height = height_map[point_key]
            if height > threshold:
                color = (height * 255, height * 255, height * 255)
            else:
                color = (0, 0, 230)
            if point_key in self.borders:
                color = (color[0] / 2, color[1] / 2, color[2] / 2)
            colors[point_key] = color
        return colors

    def generate_colors_by_tectonic(self, tectonics, tectonic_colors):
        colors = {}
        for point in self.points:
            point_key = tuple(point.tolist())
            if point_key in tectonics:
                index = tectonics[point_key]
                color = tectonic_colors[index]
                if index >= 8:
                    r, g, b = color
                    color = (r // 2), (g // 2), (b // 2)
            else:
                color = (0, 0, 0)
            colors[point_key] = color
        return colors

    def generate_colors_by_biomes(self):
        biome_hsv = {
            "marine": (210, 90, 70),
            "desert": (45, 85, 90),
            "savanna": (65, 85, 80),
            "polar": (190, 0, 100),
            "tundra": (200, 50, 85),
            "taiga": (150, 70, 60),
            "plains": (85, 75, 75),
            "seasonal_forest": (100, 80, 70),
            "temperate_rainforest": (120, 90, 80),
            "swamp": (100, 60, 60),
            "steppe": (70, 65, 80),
            "tropical_desert": (37, 80, 90),
            "tropical_seasonal_forest": (110, 85, 75),
            "tropical_rainforest": (140, 95, 60),
            "glacier": (190, 15, 85),
            "mountain": (0, 0, 75),
            "snowy_mountain": (0, 0, 95),
        }
        biome_colors = {
            None: (255, 255, 255),
        }
        colors = {}
        for point_key in self.locations:
            location = self.locations[point_key]
            biome = location.biome.lower()
            if biome not in biome_hsv:
                colors[point_key] = biome_colors[biome]
                continue
            hue, saturation, value = biome_hsv[biome]
            r, g, b = colorsys.hsv_to_rgb(hue / 360, saturation / 100, value / 100)
            if point_key in self.borders:
                r /= 3
                g /= 3
                b /= 3
            color = int(r * 255), int(g * 255), int(b * 255)
            colors[point_key] = color
        return colors

    # endregion Методы генерации

    # region Математические методы

    @staticmethod
    def _calculate_vector_conflict(
        a: tuple[float, float],
        b: tuple[float, float],
        c: tuple[float, float],
        d: tuple[float, float],
    ) -> float:
        d_ab = Planet._haversine_distance(a[0], a[1], b[0], b[1])
        d_ac = Planet._haversine_distance(a[0], a[1], c[0], c[1])
        d_bc = Planet._haversine_distance(b[0], b[1], c[0], c[1])

        denom_a = np.sin(d_ac) * np.sin(d_ab)
        if abs(denom_a) < 1e-10:
            angle_a = 0.0
        else:
            val_a = (np.cos(d_bc) - np.cos(d_ac) * np.cos(d_ab)) / denom_a
            val_a = max(min(val_a, 1), -1)
            angle_a = np.acos(val_a)

        d_cd = Planet._haversine_distance(c[0], c[1], d[0], d[1])
        d_ad = Planet._haversine_distance(a[0], a[1], d[0], d[1])

        denom_c = np.sin(d_ac) * np.sin(d_cd)
        if abs(denom_c) < 1e-10:
            angle_c = 0.0
        else:
            val_c = (np.cos(d_ad) - np.cos(d_ac) * np.cos(d_cd)) / denom_c
            val_c = max(min(val_c, 1), -1)
            angle_c = np.acos(val_c)

        return np.cos(angle_a) * d_ab + np.cos(angle_c) * d_cd

    @staticmethod
    def _normalize_map_by_min_max(point_map, min_value: float, max_value: float):
        k = max_value - min_value
        d = (min_value + max_value) / k
        return Planet._normalize_map(point_map, k, d)

    @staticmethod
    def _normalize_map(point_map, k: float = 0, d: float = 0):
        new_point_map = {}
        min_value = min(point_map.values())
        for i in point_map:
            new_point_map[i] = point_map[i] - min_value
        max_value = max(new_point_map.values())
        if k:
            for i in point_map:
                new_point_map[i] *= k / max_value
        for i in point_map:
            new_point_map[i] += k / 2 * (d - 1)
        return new_point_map

    @staticmethod
    def _spherical_to_cartesian(lat, lon):
        """Convert spherical coordinates (lat, lon in radians) to Cartesian (x, y, z)."""
        x = np.cos(lat) * np.cos(lon)
        y = np.cos(lat) * np.sin(lon)
        z = np.sin(lat)
        return np.array([x, y, z])

    @staticmethod
    def _cartesian_to_spherical(vec):
        """Convert a normalized Cartesian vector (x, y, z) to spherical (lat, lon in radians)."""
        x, y, z = vec
        lat = np.arcsin(z)
        lon = np.arctan2(y, x)
        return lat, lon

    @staticmethod
    def _relaxate_points(points, iterations=100, step_size=0.01, min_dist=1e-6):
        n = points.shape[0]
        # Convert all points to Cartesian coordinates
        coords = np.array([Planet._spherical_to_cartesian(lat, lon) for lat, lon in points])

        # Iteratively adjust points by repulsion forces
        for _ in range(iterations):
            forces = np.zeros_like(coords)
            # Compute repulsive forces between all pairs of points
            for i in range(n):
                for j in range(n):
                    if i != j:
                        diff = coords[i] - coords[j]
                        dist = np.linalg.norm(diff) + min_dist
                        forces[i] += diff / (dist**3)
            coords = coords + step_size * forces
            coords = np.array([v / np.linalg.norm(v) for v in coords])

        return np.array([Planet._cartesian_to_spherical(v) for v in coords])

    @staticmethod
    def _haversine_distance(lat1, lon1, lat2, lon2):
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
        return 2 * np.arcsin(np.sqrt(a))

    @staticmethod
    def _haversine_move(latitude: float, longitude: float, bearing: float, distance: float):
        d_by_r = distance
        new_lat = np.arcsin(
            np.sin(latitude) * np.cos(d_by_r) + np.cos(latitude) * np.sin(d_by_r) * np.cos(bearing)
        )
        new_lon = longitude + np.arctan2(
            np.sin(bearing) * np.sin(d_by_r) * np.cos(latitude),
            np.cos(d_by_r) - np.sin(latitude) * np.sin(new_lat),
        )
        return new_lat, new_lon

    def _find_nearest_points_by_distance(
        self,
        latitude,
        longitude,
        max_distance,  # в радианах
    ):
        query_point = np.array([[latitude, longitude]])
        indices = self.tree.query_radius(query_point, r=max_distance)[0]
        return self.points[indices]

    def _move_and_find_next_point(
        self, latitude, longitude, bearing, distance
    ):  # distance in radians
        lat2, lon2 = self._haversine_move(latitude, longitude, bearing, distance)

        query_point = [[lat2, lon2]]
        _, indices = self.tree.query(query_point, k=2)  # Get two closest points
        if indices[0][0] == self._find_nearest_point_index(latitude, longitude):
            return self.points[
                indices[0][1]
            ]  # Return second closest if first is the original point
        return self.points[indices[0][0]]

    @staticmethod
    def _find_nearest_points_index_static(latitude: float, longitude: float, tree: BallTree, k=1):
        query_point = [[latitude, longitude]]
        return tree.query(query_point, k=k, return_distance=False)[0]

    def _find_nearest_point_index(self, latitude, longitude):
        return self._find_nearest_points_index_static(latitude, longitude, self.tree, k=1)[0]

    def _find_nearest_point(self, latitude, longitude):
        return self.points[self._find_nearest_point_index(latitude, longitude)]

    # endregion Математические методы


class NeurosphereCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.neurosphere = None

    @commands.slash_command(
        name="neurosphere",
        description="Launches Neurosphere",
        guild_ids=GUILD_IDS,
    )
    async def launch_neurosphere(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        self.neurosphere = Planet("neurosphere/worlds/planet0.json")
        await inter.followup.send("Нейросфера запущена.")

    @commands.slash_command(name="spectate", description="Spectate character", guild_ids=GUILD_IDS)
    async def spectate_character(self, inter: disnake.ApplicationCommandInteraction):
        if self.neurosphere is None:
            await inter.response.send_message("Нейросфера не запущена.", ephemeral=True)
            return


def setup(bot):
    bot.add_cog(NeurosphereCog(bot))


# seed = 603  # архипелаг
# seed = 5950
# seed = 29
# seed = 3484
# seed = 5757
# seed = 4709
# seed = 7940
# seed = 1489 r=25
# seed = 246
# 6849 крутой мир с двумя континентами
# 6906 два континета острова r=25
