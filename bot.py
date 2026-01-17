# bot.py
import discord
from discord.ext import commands
from config import *
from state import load_state, save_state
from shards import ShardManager
from pathlib import Path


class FallBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=discord.Intents.all(), help_command=None)
        self.state = load_state()
        self.shard_manager = ShardManager(self)

    async def setup_hook(self):
        pass

    async def on_ready(self):
        print(f"Logged in as {self.user}")
        # Add persistent views, leave wrong guilds, etc.
        save_state(self.state)

        async for guild in self.fetch_guilds():
            if guild.id not in ALLOWED_SERVERS:
                await guild.leave()

        await self.load_extension("cogs.server_control")
        await self.load_extension("cogs.admin_commands")
        await self.load_extension("cogs.chat_relay")
        print("cog setup done")

        await self.tree.sync(guild=discord.Object(id=CURRENT_SERVER_ID))

        await self.change_presence(
            activity=discord.Activity(
                name="user commands", type=discord.ActivityType.listening
            )
        )

    def update_state(self):
        save_state(self.state)

bot = FallBot()
bot.current_key = KEY
bot.run(bot.current_key)
