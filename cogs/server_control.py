# cogs/server_control.py
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
from utils import helper_functions as hf
import asyncio

class SelectionView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.select_branch = discord.ui.Select(
            placeholder="Select Branch",
            options=[
                discord.SelectOption(label="Main", value="main", emoji="🌲"),
                discord.SelectOption(label="Beta", value="beta", emoji="🔄"),
                discord.SelectOption(label="Cancel", value="Cancel", emoji="❌"),
            ],
            row=0,
            custom_id="branch",
        )

        self.select_branch.callback = self.sel_branch
        self.add_item(self.select_branch)

    async def sel_branch(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if self.select_branch.values[0] == "Cancel":
            self.remove_item(self.select_branch)
            self.stop()
            await interaction.edit_original_response(view=None, content="Cancelled.")
            await asyncio.sleep(5)
            await interaction.delete_original_response()
            return
        print(
            str(interaction.user)
            + " changed the branch to "
            + self.select_branch.values[0]
        )

        self.bot.state["is_beta"] = True if self.select_branch.values[0] == "beta" else False
        self.remove_item(self.select_branch)
        self.create_cluster_selection(self.bot.state["is_beta"])
        self.add_item(self.select_cluster)
        await interaction.edit_original_response(view=self)

    def create_cluster_selection(self, is_beta_server):
        self.select_cluster = discord.ui.Select(
            placeholder="Select Cluster",
            options=hf.get_cluster_options(is_beta_server),
            row=0,
            custom_id="cluster",
        )

        self.select_cluster.callback = self.sel_cluster

    async def sel_cluster(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        print(
            str(interaction.user)
            + " changed the cluster to "
            + self.select_cluster.values[0]
        )
        self.bot.state["current_cluster"] = self.select_cluster.values[0]
        self.remove_item(self.select_cluster)
        self.stop()
        branch = "Beta" if self.bot.state["is_beta"] else "Main"
        await interaction.edit_original_response(
            view=self, content=f"Changed cluster to {self.bot.state["current_cluster"]} on {branch} Branch."
        )
        self.bot.update_state()

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

    @discord.ui.button(
        label="Change Cluster",
        style=discord.ButtonStyle.grey,
        row=2,
        custom_id="change_branch",
        emoji="🔄",
    )
    async def change_branch(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        print(str(interaction.user) + " started a branch/cluster change.")
        text = f"Currently accessing {self.bot.state["current_cluster"]} on the {'Beta' if self.bot.state["is_beta"] else 'Main'} Branch."
        await interaction.response.send_message(
            content=text, view=SelectionView(self.bot), ephemeral=True
        )


class ServerControlCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.add_view(PanelMenu(bot))

    @app_commands.command(name="panel")
    async def panel(self, interaction: discord.Interaction):
        await interaction.response.send_message("Server Control Panel", view=PanelMenu(self.bot))

async def setup(bot):
    await bot.add_cog(ServerControlCog(bot))
