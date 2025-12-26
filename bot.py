# bot.py
import discord
from discord.ext import commands
from config import *
from state import load_state, save_state
from shards import ShardManager
from pathlib import Path


class FallBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all(), help_command=None)
        self.state = load_state()
        self.shard_manager = ShardManager(self.state, Path(HOME_DIR) / ".klei")

    async def setup_hook(self):
        await self.load_extension("cogs.server_control")
        await self.load_extension("cogs.admin_commands")
        await self.load_extension("cogs.chat_relay")

    async def on_ready(self):
        print(f"Logged in as {self.user}")
        # Add persistent views, leave wrong guilds, etc.
        save_state(self.state)
        
        await bot.sync(guild=discord.Object(id=CURRENT_SERVER_ID))
        self.synced = True

        async for guild in bot.fetch_guilds():
            if guild.id not in ALLOWED_SERVERS:
                await guild.leave()

        await bot.change_presence(
            activity=discord.Activity(
                name="user commands", type=discord.ActivityType.listening
            )
        )

bot = FallBot()
bot.current_key = KEY
bot.run(bot.current_key)
