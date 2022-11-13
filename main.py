import sys
import subprocess

import discord
from discord import app_commands
from discord.ext import commands

from key import key_fallBot

start_server_path = "/home/steam/start_server.sh"
stop_server_path = "/home/steam/stop_server.sh"


class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents= discord.Intents.all())
        self.synced = False
        self.added = False

    async def on_ready(self):
        await tree.sync(guild=discord.Object(id=318264635252015106))
        self.synced = True
        print("Logged in as")
        print(self.user.name, self.user.id)

        if not self.added:
            self.add_view(Menu())

class Menu(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.cooldown = commands.CooldownMapping.from_cooldown(1,15, commands.BucketType.default)


#* Start Server
    @discord.ui.button(label="Start Server", style=discord.ButtonStyle.green, custom_id="start")
    async def start_bash(self, interaction: discord.Interaction, button: discord.ui.Button):

        bucket = self.cooldown.get_bucket(interaction.message)
        retry = bucket.update_rate_limit()
        if retry or not interaction.permissions.administrator:
            return await interaction.response.send_message("ERROR: No permission.", ephemeral=True)

        process = subprocess.Popen([start_server_path])
        await interaction.response.send_message("Server has been started.", ephemeral=True)
        process.wait()
        await interaction.response.send_message("Server will soon be online.", ephemeral=True)


#* Stop server
    @discord.ui.button(label="Stop Server", style=discord.ButtonStyle.red, custom_id="stop")
    async def stop_bash(self, interaction: discord.Interaction, button: discord.ui.Button):

        bucket = self.cooldown.get_bucket(interaction.message)
        retry = bucket.update_rate_limit()
        if retry or not interaction.permissions.administrator:
            return await interaction.response.send_message("ERROR: No permission.", ephemeral=True)

        process = subprocess.Popen([stop_server_path])
        await interaction.response.send_message("Server shutdown initiated.", ephemeral=True)
        process.wait()
        await interaction.response.send_message("Server has been shutdown.", ephemeral=True)


client = MyClient()
tree = app_commands.CommandTree(client)

@tree.command(
    name="panel", 
    description="opens the server control panel", 
    guild=discord.Object(id=318264635252015106),)

async def self(interaction: discord.Interaction):
    await interaction.response.send_message("choose your desired action", view=Menu())



# @client.event
# async def on_message(msg):

#     if msg.content == "kys" and msg.author.name == "fall":
#         await msg.channel.send( "ok i die")
#         sys.exit()


client.run(key_fallBot)
