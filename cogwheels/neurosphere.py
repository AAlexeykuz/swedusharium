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
        # todo добавить current_action персонажу


def generate_pleasant_color():
    hue = random.uniform(0, 360)  # Full hue spectrum
    saturation = random.uniform(0.25, 0.45)  # Avoid very pale or overly intense colors
    brightness = random.uniform(
        0.5, 0.85
    )  # Keep colors from being too dark or too bright
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


class LocationHolder:
    def __init__(self):
        self.locations = dict()
    
    def get_location(coords):
        pass

    def get_accessible_location(coords):
        pass


class Neurosphere:
    def __init__(self, file_path="neurosphere/saves/new.json"):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # ======= Параметры симуляции =======

        self.time = 0
        self.locations = dict()
        self.characters = dict()
        self.life = dict()
        self.items = dict()
        self.structures = dict()

        # ======= Параметры генерации =======

        seed = random.randint(0, 10000)
        random.seed(seed)
        logging.info(f"Seed: {seed}")
        self.radius = data["radius"]
        self.points: np.array = self.generate_sphere_points()
        self.tree = BallTree(self.points, metric="haversine")
        # тектоника:
        self.big_tectonics_number = 7
        self.small_tectonics_number = 7
        self.small_tectonics_delta = (
            0.4,
        )  # расстояние между плитами, где могут генерироваться малые плиты в радианах
        self.small_tectonics_max_distance = (
            0.3,
        )  # максимальный радиус малых плит в радианах
        # self.tectonic_distance_noise_octaves = [10]
        # self.tectonic_distance_noise_coefficients = [2 / np.sqrt(3) * 8]
        self.tectonic_distance_noise_octaves = [3, 10, 20, 30]
        self.tectonic_distance_noise_coefficients = [8, 6, 4, 2]
        self.tectonic_bearing_noise_octaves = [3, 10, 20, 30]
        self.tectonic_bearing_noise_coefficients = [4, 3, 2, 1]
        self.tectonics = dict()
        # высоты:
        self.min_height = -100
        self.max_height = 100
        self.water_percentage = 71
        self.water_level = None
        self.tectonic_conflict_coefficient = 0.15
        self.oceanic_tectonic_conflict_coefficient = 0.05
        self.max_tectonic_speed = 2
        self.oceanic_plate_height_delta = -0.25
        self.continental_plate_height_delta = 0.25
        self.oceanic_plates_ratio = self.water_percentage / 100
        self.height_noise_octaves = [3, 10, 20, 45]
        self.height_noise_coefficients = [1, 0.5, 0.25, 0.125]
        self.mountain_width = 3.5 / self.radius
        self.mountain_percentage = 2
        self.mountain_height = None
        self.height_map = dict()
        # температура:
        self.min_temp = -150
        self.max_temp = 100
        self.min_heat_noise = -0.25
        self.max_heat_noise = 0.25
        self.heat_delta = 0
        self.heat_tilt_angle = 0.0
        self.heat_rotation_angle = 0.0
        self.altitude_heat_k = 0.1
        self.heat_noise_octaves = [2, 4, 8, 16]
        self.heat_noise_coefficients = [4, 3, 2, 1]
        self.heat_map = dict()
        # осадки
        self.min_precipitation = 0
        self.max_precipitation = 100
        self.min_precipitation_noise = -0.6
        self.max_precipitation_noise = 0.6
        self.precipitation_delta = 0.25
        self.precipitation_tilt_angle = 0.0
        self.precipitation_rotation_angle = 0.0
        self.altitude_precipitation_k = 0.1
        self.water_precipitation_increase = 15
        self.precipitation_increase_level = 3
        self.precipitation_noise_octaves = [3, 5, 4, 6]
        self.precipitation_noise_coefficients = [4, 3, 2, 1]
        self.precipitation_map = dict()
        # биомы
        biomes_string = """Polar	Polar	Tundra	Tundra	Taiga	Taiga	Taiga	Taiga	Taiga	Temperate rainforest	Temperate rainforest	Temperate rainforest	Temperate rainforest	Swamp	Swamp	Swamp	Swamp	Tropical rainforest	Tropical rainforest	Tropical rainforest
Polar	Polar	Tundra	Tundra	Taiga	Taiga	Taiga	Taiga	Temperate rainforest	Temperate rainforest	Temperate rainforest	Temperate rainforest	Swamp	Swamp	Swamp	Swamp	Tropical rainforest	Tropical rainforest	Tropical rainforest	Tropical rainforest
Polar	Polar	Tundra	Tundra	Taiga	Taiga	Taiga	Taiga	Seasonal forest	Seasonal forest	Seasonal forest	Seasonal forest	Seasonal forest	Seasonal forest	Seasonal forest	Seasonal forest	Tropical seasonal forest	Tropical seasonal forest	Tropical seasonal forest	Tropical seasonal forest
Polar	Polar	Tundra	Tundra	Taiga	Taiga	Taiga	Taiga	Seasonal forest	Seasonal forest	Seasonal forest	Seasonal forest	Seasonal forest	Seasonal forest	Seasonal forest	Tropical seasonal forest	Tropical seasonal forest	Tropical seasonal forest	Tropical seasonal forest	Tropical seasonal forest
Polar	Polar	Tundra	Tundra	Taiga	Taiga	Taiga	Taiga	Plains	Plains	Plains	Plains	Plains	Plains	Plains	Plains	Savanna	Savanna	Savanna	Savanna
Polar	Polar	Tundra	Tundra	Taiga	Taiga	Taiga	Taiga	Plains	Plains	Plains	Plains	Plains	Plains	Plains	Savanna	Savanna	Savanna	Savanna	Savanna
Polar	Polar	Tundra	Tundra	Taiga	Taiga	Taiga	Taiga	Plains	Plains	Plains	Plains	Plains	Plains	Plains	Savanna	Savanna	Savanna	Savanna	Savanna
Polar	Polar	Tundra	Tundra	Taiga	Taiga	Taiga	Taiga	Plains	Plains	Plains	Plains	Steppe	Steppe	Steppe	Desert	Tropical desert	Tropical desert	Tropical desert	Tropical desert
Polar	Polar	Tundra	Tundra	Taiga	Taiga	Taiga	Taiga	Steppe	Steppe	Steppe	Steppe	Steppe	Desert	Desert	Desert	Tropical desert	Tropical desert	Tropical desert	Tropical desert
Polar	Polar	Tundra	Tundra	Taiga	Taiga	Taiga	Steppe	Steppe	Steppe	Steppe	Steppe	Desert	Desert	Desert	Desert	Tropical desert	Tropical desert	Tropical desert	Tropical desert"""
        self.biomes_table = self.table(biomes_string)[::-1]
        # дебаг
        self.draw_tectonics = False
        # self.load_data(data)
        self.borders = []

    def load_data(self, data):
        if data["generate"]:
            generation = data["generation"]
            self.generate_locations(generation)
        else:
            locations = data["locations"]
            for location in locations:
                point = location["lat"], location["lon"]
                point = self.find_nearest_point(*point)
                self.locations[tuple(point.tolist())] = Location(location)

    def statistics(self):
        ground_temperatures = []
        for point in self.points:
            point_key = tuple(point.tolist())
            height = self.height_map[point_key]
            if height > self.water_level:
                ground_temperatures.append(self.heat_map[point_key])
        logging.info(f"Средняя температура: {np.average(list(self.heat_map.values()))}")
        logging.info(f"Средняя температура на суше: {np.average(ground_temperatures)}")

    # region Методы генерации

    @staticmethod
    def table(biome_string):
        table = [line.split("\t") for line in biome_string.split("\n")]
        return table

    def generate_heat_map(self):
        start_time = time.time()
        # генерируем шум
        noise_map = self.generate_perlin_noise(
            self.heat_noise_octaves, self.heat_noise_coefficients
        )
        noise_map = self.normalize_map_by_min_max(
            noise_map, self.min_heat_noise, self.max_heat_noise
        )
        for point in self.points:
            # вычисление температуры от -1 до 1 по косинусу + смещение от чатагпт
            point_key = tuple(point.tolist())
            lat, lon = point
            x = np.cos(lat) * np.cos(lon)
            y = np.cos(lat) * np.sin(lon)
            z = np.sin(lat)
            y1 = (
                np.sin(self.heat_rotation_angle) * x
                + np.cos(self.heat_rotation_angle) * y
            )
            z1 = z
            z2 = np.sin(self.heat_tilt_angle) * y1 + np.cos(self.heat_tilt_angle) * z1
            effective_lat = np.arcsin(z2)
            self.heat_map[point_key] = np.cos(effective_lat) + self.heat_delta
            # добавляем шум
            self.heat_map[point_key] += noise_map[point_key]
        self.heat_map = self.normalize_map_by_min_max(
            self.heat_map, self.min_temp, self.max_temp
        )
        for point in self.points:
            point_key = tuple(point.tolist())
            height = self.height_map[point_key]
            if height > self.water_level:
                self.heat_map[point_key] -= (
                    height - self.water_level
                ) * self.altitude_heat_k
        self.heat_map = self.normalize_map_by_min_max(
            self.heat_map, self.min_temp, self.max_temp
        )

        logging.info(f"Генерация карты тепла: {time.time() - start_time:.2f}с")

    def generate_precipitation_map(self):
        start_time = time.time()
        # генерируем шум
        noise_map = self.generate_perlin_noise(
            self.precipitation_noise_octaves, self.precipitation_noise_coefficients
        )
        noise_map = self.normalize_map_by_min_max(
            noise_map, self.min_precipitation_noise, self.max_precipitation_noise
        )

        for point in self.points:
            # вычисление осадков от -1 до 1 по косинусу ((4x + пи)/2) в квадрате + смещение от чатагпт
            point_key = tuple(point.tolist())
            lat, lon = point
            x = np.cos(lat) * np.cos(lon)
            y = np.cos(lat) * np.sin(lon)
            z = np.sin(lat)
            y1 = (
                np.sin(self.precipitation_rotation_angle) * x
                + np.cos(self.precipitation_rotation_angle) * y
            )
            z1 = z
            z2 = (
                np.sin(self.precipitation_tilt_angle) * y1
                + np.cos(self.precipitation_tilt_angle) * z1
            )
            effective_lat = np.arcsin(z2)
            self.precipitation_map[point_key] = (
                np.cos((4 * effective_lat + np.pi) / 2) ** 2 + self.precipitation_delta
            )
            # добавляем шум
            self.precipitation_map[point_key] += noise_map[point_key]
        self.precipitation_map = self.normalize_map_by_min_max(
            self.precipitation_map, self.min_precipitation, self.max_precipitation
        )
        # зависимость от высоты
        for point in self.points:
            point_key = tuple(point.tolist())
            height = self.height_map[point_key]
            if (
                self.water_level
                < height
                < self.water_level + self.precipitation_increase_level
            ):
                self.precipitation_map[point_key] += self.water_precipitation_increase
            elif height > self.water_level:
                self.precipitation_map[point_key] += (
                    height - self.water_level
                ) * self.altitude_precipitation_k
        self.precipitation_map = self.normalize_map_by_min_max(
            self.precipitation_map, self.min_precipitation, self.max_precipitation
        )

        logging.info(f"Генерация карты осадков: {time.time() - start_time:.2f}с")

    def generate_heights(self):
        start_time = time.time()

        tectonics_number: int = self.big_tectonics_number + self.small_tectonics_number

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

        # octaves = [2, 8, 16, 24]
        # coefficients = [1, 0.5, 0.25, 0.125]
        # octaves = [3, 5, 10, 20]
        # coefficients = [1, 0.5, 0.25, 0.125]
        for point_key in self.tectonics:
            index = self.tectonics[point_key]
            x, y, z = self.spherical_to_cartesian(*point_key) + tectonic_shifts[index]
            noise_value = 0
            for octave, k in zip(
                self.height_noise_octaves, self.height_noise_coefficients
            ):
                noise_value += k * noise.pnoise3(x, y, z, octaves=octave)
            self.height_map[point_key] = noise_value

        numbers = list(range(tectonics_number))
        random.shuffle(numbers)
        ratio = round(len(numbers) * self.oceanic_plates_ratio)
        oceanic_plates = numbers[:ratio]

        tectonic_movement = [
            (random.random() * 2 * np.pi, random.random() * self.max_tectonic_speed)
            for _ in range(tectonics_number)
        ]

        self.height_map = self.normalize_map_by_min_max(self.height_map, 0, 1)
        for point in self.points:
            point_key = tuple(point.tolist())
            tectonic_index = self.tectonics[point_key]
            if tectonic_index in oceanic_plates:
                self.height_map[point_key] += self.oceanic_plate_height_delta
            else:
                self.height_map[point_key] += self.continental_plate_height_delta
            nearest_points = self.find_nearest_points_by_distance(
                *point, self.mountain_width
            )
            conflict_height_delta = 0
            conflict_points_count = 0
            for point2 in nearest_points:
                x1, y1 = point
                x2, y2 = point2
                if (x1, y1) == (x2, y2):
                    continue
                point_key_2 = tuple(point2.tolist())
                tectonic_index_2 = self.tectonics[point_key_2]
                if tectonic_index == tectonic_index_2:
                    continue
                # вычисляем конфликт векторов AB и CD
                point_a = point_key
                vector1 = tectonic_movement[tectonic_index]
                point_b = self.haversine_move(*point_a, *vector1)
                point_c = point_key_2
                vector2 = tectonic_movement[tectonic_index_2]
                point_d = self.haversine_move(*point_c, *vector2)
                conflict = self.calculate_vector_conflict(
                    point_a, point_b, point_c, point_d
                )
                if (
                    tectonic_index in oceanic_plates
                    and tectonic_index_2 in oceanic_plates
                ):
                    k = self.oceanic_tectonic_conflict_coefficient
                else:
                    k = self.tectonic_conflict_coefficient
                conflict_height_delta += conflict / (2 * self.max_tectonic_speed) * k
                conflict_points_count += 1
            if (
                conflict_height_delta != 0
            ):  # if height_delta != 0 then conflict_points_count > 0 guaranteed
                self.height_map[point_key] += conflict_height_delta

        if self.draw_tectonics:
            for point in self.points:
                point_key = tuple(point.tolist())
                tectonic_index = self.tectonics[point_key]
                nearest_points = self.find_nearest_points_by_distance(
                    *point, 1.1 / self.radius
                )
                for point2 in nearest_points:
                    x1, y1 = point
                    x2, y2 = point2
                    if (x1, y1) == (x2, y2):
                        continue
                    point_key_2 = tuple(point2.tolist())
                    tectonic_index_2 = self.tectonics[point_key_2]
                    if tectonic_index == tectonic_index_2:
                        continue
                    self.borders.append(point_key)

        self.height_map = self.normalize_map_by_min_max(
            self.height_map, self.min_height, self.max_height
        )
        self.water_level = np.percentile(
            np.array(list(self.height_map.values())), self.water_percentage
        )
        self.mountain_height = np.percentile(
            np.array(list(self.height_map.values())), 100 - self.mountain_percentage
        )

        logging.info(f"Генерация карты высот: {time.time() - start_time:.2f}с")

    def generate_tectonics(self):
        start_time = time.time()

        # Создаём словарь, в котором на каждую точку будет храниться точка после обработки шума
        noise_point_keys = dict()
        noise_map_distance = self.generate_perlin_noise(
            self.tectonic_distance_noise_octaves,
            self.tectonic_distance_noise_coefficients,
        )
        noise_map_bearing = self.generate_perlin_noise(
            self.tectonic_bearing_noise_octaves,
            self.tectonic_bearing_noise_coefficients,
        )
        for point in self.points:
            point_key = tuple(point.tolist())
            noise_distance = noise_map_distance[point_key] / self.radius
            noise_bearing = noise_map_bearing[point_key]
            noise_point_keys[point_key] = self.haversine_move(
                *point, noise_bearing, noise_distance
            )

        # Вычисляем равноудалённые точки для больших плит
        random_points = np.array(
            random.choices(self.points, k=self.big_tectonics_number)
        )
        big_tectonics_points = self.relaxate_points(random_points)
        big_tectonics_tree = BallTree(big_tectonics_points, metric="haversine")
        # Подготавливаем список точек, которые не будут использованы
        small_plate_generation_points = []

        for point in self.points:
            point_key = tuple(point.tolist())
            query_point = [noise_point_keys[point_key]]
            # находим dist - расстояния от точки с шумом до двух ближайших плит и index - номер ближайшей плиты
            dist, indices = big_tectonics_tree.query(query_point, k=2)
            dist, indices = dist[0], indices[0]
            index = indices[0]
            # если разница между расстояниями до плит слишком маленькая, то оставляем на потом для генерации малых
            distance_delta = abs(dist[0] - dist[1])
            if distance_delta < self.small_tectonics_delta:
                small_plate_generation_points.append(point)
            else:
                self.tectonics[point_key] = index

        small_tectonics_points = np.array(
            random.choices(small_plate_generation_points, k=self.small_tectonics_number)
        )
        small_tectonics_tree = BallTree(small_tectonics_points, metric="haversine")

        for point in small_plate_generation_points:
            point_key = tuple(point.tolist())
            query_point = [noise_point_keys[point_key]]
            dist, indices = small_tectonics_tree.query(query_point, k=1)
            dist, indices = dist[0], indices[0]
            dist, index = dist[0], indices[0] + self.big_tectonics_number
            # если расстояние слишком большое, чтобы поместиться в малую плиту, ищем ближайшую большую
            if dist > self.small_tectonics_max_distance:
                index = big_tectonics_tree.query(
                    query_point, k=1, return_distance=False
                )[0][0]
            self.tectonics[point_key] = index
        logging.info(f"Генерация тектонических плит: {time.time() - start_time:.2f}с")

    @staticmethod
    def generate_perlin_noise_static(
        points, octaves: list[float], coefficients: list[float], positive=False
    ):
        noise_map = {}

        for point in points:
            lat, lon = point
            x, y, z = Neurosphere.spherical_to_cartesian(lat, lon)

            noise_value = 0

            for octave, k in zip(octaves, coefficients):
                if positive:
                    noise_value += k * (
                        noise.pnoise3(x, y, z, octaves=octave) + np.sqrt(3) / 2
                    )
                else:
                    noise_value += k * noise.pnoise3(x, y, z, octaves=octave)

            point_key = tuple(point.tolist())
            noise_map[point_key] = noise_value

        return noise_map

    def generate_perlin_noise(
        self, octaves: list[float], coefficients: list[float], positive=False
    ):
        return self.generate_perlin_noise_static(
            self.points, octaves, coefficients, positive
        )

    def generate_colors_by_map(self, point_map):
        colors = dict()
        point_map = self.normalize_map_by_min_max(point_map, 0, 1)
        for point in self.points:
            point_key = tuple(point.tolist())
            c = round((point_map[point_key] * 255))
            colors[point_key] = (c, c, c)
        return colors

    def generate_colors_by_height_map(self, height_map):
        colors = dict()
        height_map = self.normalize_map_by_min_max(height_map, 0, 1)
        threshold = np.percentile(
            np.array(list(height_map.values())), self.water_percentage
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
        colors = dict()
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
            "seasonal forest": (100, 80, 70),
            "temperate rainforest": (120, 90, 80),
            "swamp": (100, 60, 60),
            "steppe": (70, 65, 80),
            "tropical desert": (37, 80, 90),
            "tropical seasonal forest": (110, 85, 75),
            "tropical rainforest": (140, 95, 60),
            "glacier": (190, 15, 85),
            "mountain": (0, 0, 75),
            "snowy mountain": (0, 0, 95),
        }
        biome_colors = {
            None: (255, 255, 255),
        }
        colors = dict()
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

    def generate_locations(self, *_):
        for point in self.points:
            point_key = tuple(point.tolist())
            location = Location()
            height = self.height_map[point_key]
            temperature = self.heat_map[point_key]
            precipitation = self.precipitation_map[point_key]
            biome = self.generate_biome(height, temperature, precipitation)
            location.set_biome(biome)
            self.locations[point_key] = location

        # main_characters = data["main_characters"]
        # for character in main_characters:
        #     self.main_characters[character["id"]] = Character(character)
        #     if data["generate"]:
        #         point = character["lat"], character["lon"]
        #         point = self.find_nearest_point(*point)
        #         self.locations[tuple(point.tolist())].add_character_id(character["id"])

    def generate_biome(self, height, temperature, precipitation):
        #
        if height < self.water_level:
            if temperature < -60:
                return "Glacier"
            else:
                return "Marine"
        elif height > self.mountain_height:
            if temperature < -60:
                return "Snowy mountain"
            else:
                return "Mountain"
        horizontal_index = int((temperature + 100) // 10)
        if horizontal_index >= 20:
            horizontal_index = 19
        elif horizontal_index < 0:
            horizontal_index = 0
        vertical_index = int(precipitation // 10)
        if vertical_index >= 10:
            vertical_index = 9
        elif vertical_index < 0:
            vertical_index = 0
        return self.biomes_table[vertical_index][horizontal_index]

    # endregion Методы генерации

    # region Математические методы

    @staticmethod
    def get_value_by_interval(key, bounds, values):
        indices = np.searchsorted(bounds, key, side="right") - 1
        return values[indices]

    @staticmethod
    def calculate_vector_conflict(a, b, c, d):
        d_ab = Neurosphere.haversine_distance(a[0], a[1], b[0], b[1])
        d_ac = Neurosphere.haversine_distance(a[0], a[1], c[0], c[1])
        d_bc = Neurosphere.haversine_distance(b[0], b[1], c[0], c[1])

        denom_a = np.sin(d_ac) * np.sin(d_ab)
        if abs(denom_a) < 1e-10:
            angle_a = 0.0
        else:
            val_a = (np.cos(d_bc) - np.cos(d_ac) * np.cos(d_ab)) / denom_a
            val_a = max(min(val_a, 1), -1)
            angle_a = np.acos(val_a)

        d_cd = Neurosphere.haversine_distance(c[0], c[1], d[0], d[1])
        d_ad = Neurosphere.haversine_distance(a[0], a[1], d[0], d[1])

        denom_c = np.sin(d_ac) * np.sin(d_cd)
        if abs(denom_c) < 1e-10:
            angle_c = 0.0
        else:
            val_c = (np.cos(d_ad) - np.cos(d_ac) * np.cos(d_cd)) / denom_c
            val_c = max(min(val_c, 1), -1)
            angle_c = np.acos(val_c)

        return np.cos(angle_a) * d_ab + np.cos(angle_c) * d_cd

    @staticmethod
    def normalize_map_by_min_max(point_map, min_value: float, max_value: float):
        k = max_value - min_value
        d = (min_value + max_value) / k
        return Neurosphere.normalize_map(point_map, k, d)

    @staticmethod
    def normalize_map(point_map, k: float = 0, d: float = 0):
        new_point_map = dict()
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
    def spherical_to_cartesian(lat, lon):
        """Convert spherical coordinates (lat, lon in radians) to Cartesian (x, y, z)."""
        x = np.cos(lat) * np.cos(lon)
        y = np.cos(lat) * np.sin(lon)
        z = np.sin(lat)
        return np.array([x, y, z])

    @staticmethod
    def cartesian_to_spherical(vec):
        """Convert a normalized Cartesian vector (x, y, z) to spherical (lat, lon in radians)."""
        x, y, z = vec
        lat = np.arcsin(z)
        lon = np.arctan2(y, x)
        return lat, lon

    @staticmethod
    def relaxate_points(points, iterations=100, step_size=0.01, min_dist=1e-6):
        n = points.shape[0]
        # Convert all points to Cartesian coordinates
        coords = np.array(
            [Neurosphere.spherical_to_cartesian(lat, lon) for lat, lon in points]
        )

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

        new_points = np.array([Neurosphere.cartesian_to_spherical(v) for v in coords])
        return new_points

    @staticmethod
    def haversine_distance(lat1, lon1, lat2, lon2):
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
        c = 2 * np.arcsin(np.sqrt(a))
        return c

    @staticmethod
    def haversine_move(latitude, longitude, bearing, distance):
        d_by_r = distance
        new_lat = np.arcsin(
            np.sin(latitude) * np.cos(d_by_r)
            + np.cos(latitude) * np.sin(d_by_r) * np.cos(bearing)
        )
        new_lon = longitude + np.arctan2(
            np.sin(bearing) * np.sin(d_by_r) * np.cos(latitude),
            np.cos(d_by_r) - np.sin(latitude) * np.sin(new_lat),
        )
        return new_lat, new_lon

    def generate_sphere_points(self):
        """Генерирует n точек (вычисляется по площади сферы) на сфере и возвращает массив из широты и долготы"""
        n = round(4 * np.pi * self.radius**2)
        indices = np.arange(n, dtype=np.float32) + 0.5
        phi = np.arccos(1 - 2 * indices / n)
        theta = (np.pi * (1 + 5**0.5)) * indices
        latitude = np.pi / 2 - phi
        longitude = theta % (2 * np.pi)

        return np.column_stack((latitude, longitude))

    def find_nearest_points_by_distance(
        self, latitude, longitude, max_distance  # в радианах
    ):
        query_point = np.array([[latitude, longitude]])
        indices = self.tree.query_radius(query_point, r=max_distance)[0]
        return self.points[indices]

    def move_and_find_next_point(
        self, latitude, longitude, bearing, distance
    ):  # distance in radians
        lat2, lon2 = self.haversine_move(latitude, longitude, bearing, distance)

        query_point = [[lat2, lon2]]
        dist, indices = self.tree.query(query_point, k=2)  # Get two closest points
        if indices[0][0] == self.find_nearest_point_index(latitude, longitude):
            return self.points[
                indices[0][1]
            ]  # Return second closest if first is the original point
        else:
            return self.points[indices[0][0]]

    @staticmethod
    def find_nearest_points_index_static(latitude, longitude, tree: BallTree, k=1):
        query_point = [[latitude, longitude]]
        indices = tree.query(query_point, k=k, return_distance=False)[0]
        return indices

    def find_nearest_point_index(self, latitude, longitude):
        return self.find_nearest_points_index_static(
            latitude, longitude, self.tree, k=1
        )[0]

    def find_nearest_point(self, latitude, longitude):
        return self.points[self.find_nearest_point_index(latitude, longitude)]

    # endregion Математические методы


class NeurosphereCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.neurosphere = None

    @commands.slash_command(
        name="neurosphere", description="Launches Neurosphere", guild_ids=GUILD_IDS
    )
    async def launch_neurosphere(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        self.neurosphere = Neurosphere()
        await inter.followup.send("Нейросфера запущена.")

    @commands.slash_command(
        name="spectate", description="Spectate character", guild_ids=GUILD_IDS
    )
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
