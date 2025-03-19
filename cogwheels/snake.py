import time
from random import choice
import disnake
from disnake.ext import commands
from g4f.client import Client
from constants import GUILD_IDS
import asyncio


MODEL = "o3-mini"


class Snake:
    def __init__(self):
        self.game_over = False
        self.game_message = None
        self.field = [[None for _ in range(9)] for _ in range(9)]
        self.snake_coords = []
        self.add_snake_coords((4, 4))
        self.apple_coords = None
        self.spawn_apple()
        self.direction = 0
        self.iteration = 0
        self.apples_collected = 0
        self.generation_time = 0
        self.client = Client()

    def set_game_message(self, game_message):
        self.game_message = game_message

    def add_snake_coords(self, coords):
        x, y = coords
        self.field[y][x] = "snake"
        self.snake_coords.append(coords)

    def __str__(self):
        emojis = {
            None: ":black_large_square:",
            "snake": ":green_square:",
            "apple": ":apple:",
        }
        output = "\n".join(["".join([emojis[i] for i in line]) for line in self.field])
        return (
            output
            + f"\n-# Яблок собрано {self.apples_collected}\n-# Генерация {self.generation_time}с\n-# {MODEL}"
        )

    def get_vision_gpt(self) -> str:
        head = self.snake_coords[-1]
        apple = self.apple_coords
        output = [
            f"The field is {len(self.field[0])}x{len(self.field)}. (0,0) is the top left point.",
            f"Apple is at {apple}.",
            f"Snake's head is at {head}.",
            f"All of the snake's cells coordinates are: {self.snake_coords}",
            f"The snake's current length is {len(self.snake_coords)}",
        ]
        return "\n".join(output)

    def get_direction_gpt(self):
        if self.direction == 0:
            return "-y"
        elif self.direction == 1:
            return "+x"
        elif self.direction == 2:
            return "+y"
        else:
            return "-x"

    def spawn_apple(self):
        all_coords = set((x, y) for x in range(9) for y in range(9))
        possible_coords = list(all_coords - set(self.snake_coords))
        x, y = choice(possible_coords)
        self.field[y][x] = "apple"
        self.apple_coords = (x, y)

    def get_forward_coords(self, direction=0):  # -1 - направо, 1 - лево
        head_x, head_y = self.snake_coords[-1]
        direction = (direction + self.direction) % 4
        if direction == 0:
            head_y -= 1
        elif direction == 1:
            head_x -= 1
        elif direction == 2:
            head_y += 1
        else:
            head_x += 1

        return head_x, head_y

    def forward(self):
        head_x, head_y = self.get_forward_coords()
        self.move(head_x, head_y)

    def move(self, x, y):
        if (
            not (0 <= x < len(self.field[0]) and 0 <= y < len(self.field))
            or self.field[y][x] == "snake"
        ):
            self.game_over = True
            return

        spawn_apple = False
        if self.field[y][x] == "apple":
            spawn_apple = True
            self.apples_collected += 1
        else:
            tail_x, tail_y = self.snake_coords.pop(0)
            self.field[tail_y][tail_x] = None
        self.add_snake_coords((x, y))
        if spawn_apple:
            self.spawn_apple()

    def left(self):
        self.direction = (self.direction + 1) % 4

    def right(self):
        self.direction = (self.direction - 1) % 4

    async def update_game_message(self):
        await self.game_message.edit(str(self))

    async def execute_gpt_commands(self):
        self.iteration += 1
        prompt = (
            "You're a bot that's designed to play snake game. "
            "Below there's going to be listed all of the information available to you at this moment of time.\n"
            "You have three available commands:\n"
            "-x N- moves snake to -x N times.\n"
            "+x N - moves snake to +x N times.\n"
            "-y N - moves snake to -y N times.\n"
            "+y N - moves snake to +y N times.\n"
            "For example, if you need to get from (2,2) to (5,7), commands can be like this:\n"
            "+x 3\n"
            "+y 5\n"
            "But remember not to go hit yourself while moving.\n"
            "Your goal is to output an array of commands that makes the snake get the apple and not to lose.\n"
            "You will lose if you will hit a wall (try to leave 0-9 coordinates) or hit your part.\n"
            "Points are (x, y).\n"
            "Here's information available to you:\n\n" + self.get_vision_gpt() + "\n\n"
            "You should write each command starting from a new line consecutively and nothing else.\n"
        )
        self.generation_time = time.time()
        response = self.client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": prompt}],
            web_search=False,
        )
        self.generation_time = round(time.time() - self.generation_time, 2)
        text = response.choices[0].message.content
        for line in text.split("\n"):
            if line.startswith("-y"):
                self.direction = 0
            elif line.startswith("-x"):
                self.direction = 1
            elif line.startswith("+y"):
                self.direction = 2
            elif line.startswith("+x"):
                self.direction = 3
            else:
                continue
            for i in range(int(line.split()[-1])):
                self.forward()
                await self.update_game_message()
                await asyncio.sleep(1)
                if self.game_over:
                    return

    async def main_cycle(self):
        while not self.game_over:
            await self.execute_gpt_commands()
        await self.game_message.channel.send("Конец!")


class SnakeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games = dict()

    @commands.slash_command(
        name="snake", description="gpt играет в змейку", guild_ids=GUILD_IDS
    )
    async def snake(self, inter: disnake.ApplicationCommandInteraction):
        print("pon")
        await inter.response.send_message("Начало", ephemeral=True)
        print("pon2")
        game = Snake()
        self.games[inter.channel.id] = game
        message = await inter.channel.send(str(game))
        game.set_game_message(message)
        await game.main_cycle()

    # @commands.Neurospherecog.listener()
    # async def on_message(self,
    #                      message: disnake.message.Message):
    #     channel = message.channel
    #     if channel.id not in self.games:
    #         return
    #     game: Snake = self.games[channel.id]
    #     if not game.game_message:
    #         return
    #     if message.content == "forward":
    #         game.forward()
    #         await game.update_game_message()
    #     elif message.content == "left":
    #         game.left()
    #         await game.update_game_message()
    #     elif message.content == "right":
    #         game.right()
    #         await game.update_game_message()
    #     if game.game_over:
    #         del self.games[channel.id]
    #         await game.game_message.channel.send("Конец!")
    #         return


def setup(bot):
    bot.add_cog(SnakeCog(bot))
