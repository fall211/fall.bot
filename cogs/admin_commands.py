# cogs/admin_commands.py
import discord
from discord import app_commands
from discord.ext import commands
import os
import subprocess
import requests
import asyncio
from pathlib import Path

class AdminCommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.home_dir = os.path.expanduser("~")
        self.scripts_dir = Path(self.home_dir) / "fall.bot" / "scripts"

    @app_commands.command(name="new_world", description="Creates a new world. Requires a zip of the server files.")
    @app_commands.describe(
        cluster_name="Name of the new cluster",
        branch="main or beta",
        difficulty="main or relaxed"
    )
    async def new_world(self, interaction: discord.Interaction, cluster_name: str, branch: str, difficulty: str):
        await interaction.response.defer(ephemeral=True)

        branch = branch.lower()
        difficulty = difficulty.lower()

        if branch not in ("main", "beta"):
            return await interaction.followup.send("ERROR: Invalid branch. Use 'main' or 'beta'.", ephemeral=True)
        if difficulty not in ("main", "relaxed"):
            return await interaction.followup.send("ERROR: Invalid difficulty. Use 'main' or 'relaxed'.", ephemeral=True)

        conf_dir = "DoNotStarveTogetherBetaBranch" if branch == "beta" else "DoNotStarveTogether"
        cluster_path = Path(self.home_dir) / ".klei" / conf_dir / cluster_name
        if cluster_path.exists():
            return await interaction.followup.send("ERROR: Cluster with that name already exists.", ephemeral=True)

        await interaction.followup.send("Please upload a zip file containing the save files for the new world.", ephemeral=True)

        def check(m):
            return m.author == interaction.user and m.attachments and m.channel.id == interaction.channel.id

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=300)
        except asyncio.TimeoutError:
            return await interaction.followup.send("Timed out waiting for zip file.", ephemeral=True)

        zip_url = msg.attachments[0].url
        zip_path = Path("cluster.zip")
        zip_path.write_bytes(requests.get(zip_url).content)

        script_path = self.scripts_dir / "make_new_world.sh"
        process = subprocess.run([str(script_path), cluster_name, branch, difficulty, str(zip_path)])
        zip_path.unlink(missing_ok=True)
        await msg.delete().catch(lambda: None)

        if process.returncode == 0:
            await interaction.followup.send(f"Successfully created new world: `{cluster_name}` ({branch}/{difficulty})", ephemeral=True)
        else:
            await interaction.followup.send("Failed to create world. Check server logs.", ephemeral=True)

    @app_commands.command(name="backup", description="Backs up the current world/cluster")
    @app_commands.describe(cluster="Cluster name (default: current)", branch="main or beta (default: current)")
    async def backup(self, interaction: discord.Interaction, cluster: str = None, branch: str = None):
        await interaction.response.defer(ephemeral=True)

        cluster = cluster or self.bot.state["current_cluster"]
        branch = (branch or ("beta" if self.bot.state["is_beta"] else "main")).lower()
        if branch.startswith("b"):
            branch = "beta"
        else:
            branch = "main"

        script_path = self.scripts_dir / "backup.sh"
        result = subprocess.run([str(script_path), cluster, branch], capture_output=True, text=True)

        if result.returncode == 0:
            await interaction.followup.send(f"Backup completed for `{branch}/{cluster}`.", ephemeral=True)
        else:
            await interaction.followup.send(f"Backup failed:\n```{result.stderr[-500:]}```", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminCommandsCog(bot))
