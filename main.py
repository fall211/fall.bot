import subprocess, sys, asyncio

import discord
from discord import app_commands
from discord.ext import commands

from key import key_fallBot, key_tBot, server_id, test_id

test_command_path = "/Users/tuukkav/testbash.sh"
start_server_path = "/home/steam/start_server.sh"
stop_server_path = "/home/steam/stop_server.sh"



class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents= discord.Intents.all())
        self.synced = False
        self.added = False

    async def on_ready(self):
        await tree.sync(guild=discord.Object(id=server_id))
        self.synced = True
        print("Logged in as")
        print(self.user.name, self.user.id)

        if not self.added:
            self.add_view(Menu())

class Menu(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.cooldown = commands.CooldownMapping.from_cooldown(1,15, commands.BucketType.default)

#* Test
#    @discord.ui.button(label="run test command", style=discord.ButtonStyle.blurple, custom_id="test")
#    async def run_bash(self, interaction: discord.Interaction, button: discord.ui.Button):
#
#        bucket = self.cooldown.get_bucket(interaction.message)
#        retry = bucket.update_rate_limit()
#        if retry or not interaction.permissions.administrator:
#            return await interaction.response.send_message("Error", ephemeral=True)

#        await interaction.response.defer(ephemeral=True)
#        # await asyncio.sleep(4)
#        msg2 = await interaction.followup.send("1.", ephemeral=True)
#        await asyncio.sleep(1)
#        await msg2.edit(content="2.")


#* Start Server
    @discord.ui.button(label="Start Server", style=discord.ButtonStyle.green, custom_id="start")
    async def start_bash(self, interaction: discord.Interaction, button: discord.ui.Button):

        bucket = self.cooldown.get_bucket(interaction.message)
        retry = bucket.update_rate_limit()
        if retry or not interaction.permissions.administrator:
            return await interaction.response.send_message("ERROR: No permission.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        process = subprocess.Popen([start_server_path])
        msg = await interaction.followup.send("Server has been started.", ephemeral=True)
        process.wait()
        await msg.edit("Server will soon be online.")


#* Stop server
    @discord.ui.button(label="Stop Server", style=discord.ButtonStyle.danger, custom_id="stop")
    async def stop_bash(self, interaction: discord.Interaction, button: discord.ui.Button):

        bucket = self.cooldown.get_bucket(interaction.message)
        retry = bucket.update_rate_limit()
        if retry or not interaction.permissions.administrator:
            return await interaction.response.send_message("ERROR: No permission.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        process = subprocess.Popen([stop_server_path])
        msg = await interaction.followup.send("Server shutdown initiated.", ephemeral=True)
        process.wait()
        await msg.edit("Server shutdown completed.")



client = MyClient()
tree = app_commands.CommandTree(client)

@tree.command(
    name="panel", 
    description="opens the server control panel", 
    guild=discord.Object(id=server_id),)

async def self(interaction: discord.Interaction):
    await interaction.response.send_message("choose your desired action", view=Menu())



# @client.event
# async def on_message(msg):

#     if msg.content == "kys" and msg.author.name == "fall":
#         await msg.channel.send( "ok i die")
#         sys.exit()


client.run(key_fallBot)
