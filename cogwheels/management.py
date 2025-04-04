import asyncio
import json

import anyio
import disnake
from disnake.ext import commands

from constants import GUILD_IDS, owner_only


class ManagementCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        name="save-channel-names",
        description="сохраняет названия каналов",
        guild_ids=GUILD_IDS,
    )
    @owner_only()
    async def save_channel_names(
        self,
        inter: disnake.ApplicationCommandInteraction,
        save_name: str,
    ):
        channels = [
            {"id": channel.id, "name": channel.name}
            for channel in inter.guild.channels
        ]
        async with await anyio.open_file(
            f"other_files/management/{save_name}.json", "w", encoding="utf-8"
        ) as f:
            await f.write(json.dumps(channels, indent=2, ensure_ascii=False))
        await inter.response.send_message("Успех", ephemeral=True)

    @commands.slash_command(
        name="load-channel-names",
        description="загружает названия каналов",
        guild_ids=GUILD_IDS,
    )
    @owner_only()
    async def load_channel_names(
        self,
        inter: disnake.ApplicationCommandInteraction,
        load_name: str,
    ):
        """Restore channel names from a JSON file."""
        try:
            await inter.response.defer()
            # Read the JSON file
            async with await anyio.open_file(
                f"other_files/management/{load_name}.json",
                "r",
                encoding="utf-8",
            ) as f:
                data = json.loads(await f.read())

            # Update channel names
            updated = 0
            for entry in data:
                channel = inter.guild.get_channel(entry["id"])
                if channel:
                    if channel.name == entry["name"]:
                        continue
                    try:
                        await channel.edit(name=entry["name"])
                        await asyncio.sleep(1)
                        updated += 1
                    except Exception:
                        continue  # Skip if no permission or invalid name

            await inter.followup.send(
                f"✅ Restored {updated}/{len(data)} channel names from `{load_name}.json`!",
                ephemeral=True,
            )
        except FileNotFoundError:
            await inter.followup.send(
                f"❌ File `{load_name}.json` not found!", ephemeral=True
            )
        except Exception as e:
            await inter.followup.send(
                f"❌ Failed to load channels: `{str(e)}`", ephemeral=True
            )


def setup(bot):
    bot.add_cog(ManagementCog(bot))
