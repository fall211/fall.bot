# cogs/server_control.py
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
import asyncio

class PanelMenu(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Start Server", style=discord.ButtonStyle.success, emoji="🟢", custom_id="start_server")
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await self.bot.shard_manager.start_world()
        await interaction.followup.send("Server started.", ephemeral=True)
        # TODO: update presence, start chat log task, etc.

    @discord.ui.button(label="Stop Server", style=discord.ButtonStyle.danger, emoji="🔴", custom_id="stop_server")
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        self.bot.shard_manager.send_announce("[Discord] Server shutting down in 10s")
        await asyncio.sleep(10)
        await self.bot.shard_manager.stop_world()
        await interaction.followup.send("Server stopped.", ephemeral=True)

    @discord.ui.button(label="Restart Server", style=discord.ButtonStyle.blurple, emoji="🔄", custom_id="restart_server")
    async def restart(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await self.bot.shard_manager.restart_world()
        await interaction.followup.send("Restarting server...", ephemeral=True)

    @discord.ui.select(
        placeholder="Select an option",
        options=[
            discord.SelectOption(label="Option 1", value="option_1"),
            discord.SelectOption(label="Option 2", value="option_2"),
            discord.SelectOption(label="Option 3", value="option_3"),
        ]
    )
    async def select(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.send_message(f"You selected {select.values[0]}", ephemeral=True)

class ServerControlCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.add_view(PanelMenu(bot))

    @app_commands.command(name="panel")
    async def panel(self, interaction: discord.Interaction):
        await interaction.response.send_message("Server Control Panel", view=PanelMenu(self.bot))

async def setup(bot):
    await bot.add_cog(ServerControlCog(bot))
