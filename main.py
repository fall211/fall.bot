import asyncio
import subprocess
import time
import requests

import discord
from discord import app_commands
from discord.ext import commands, tasks

from key import key_fallBot, key_tBot, server_id, test_id, test_channel
import forum_scraper as fs

#********** File Paths **********
test_command_path = "/Users/tuukkav/testbash.sh"
start_server_path = "/home/steam/start_server.sh"
stop_server_path = "/home/steam/stop_server.sh"

screen_log_path = "/home/steam/screenlog.0"
test_log_path = "/Users/tuukkav/Desktop/school_things/ecn102/hw4log.log"



#********** Variables **********
not_running_text = "steam@instance-dst"
allowed_servers = [server_id, test_id]
test_channels = [test_channel]
updates = [] #list of tuples containing version_id, beta, release_id #!change to a file read later
updates = fs.get_past_update_info()



#! Change these before deployment.
current_id = server_id
log_file_path = screen_log_path
current_key = key_fallBot
bot_channel_ids = allowed_servers

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents= discord.Intents.all())
        self.synced = False
        self.added = False

    async def on_ready(self):
        await tree.sync(guild=discord.Object(id=current_id))
        self.synced = True
        print("Logged in as")
        print(self.user.name, self.user.id)

        if not self.added:
            self.add_view(PanelMenu())

        async for guild in client.fetch_guilds():
            if guild.id not in allowed_servers:
                await guild.leave()

        check_server.start()

class PanelMenu(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.cooldown = commands.CooldownMapping.from_cooldown(1,15, commands.BucketType.default)

#***************** Buttons *****************

#* Start Server
    @discord.ui.button(label="Start Server", style=discord.ButtonStyle.success, custom_id="start")
    async def start_bash(self, interaction: discord.Interaction, button: discord.ui.Button):

        bucket = self.cooldown.get_bucket(interaction.message)
        retry = bucket.update_rate_limit()
        if retry:
            return await interaction.response.send_message("ERROR: Please do not spam commands.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        process = subprocess.Popen([start_server_path])
        msg = await interaction.followup.send("Server startup initated...", ephemeral=True)
        process.wait()
        await msg.edit(content="Server will soon be online.")


#* Stop server
    @discord.ui.button(label="Stop Server", style=discord.ButtonStyle.danger, custom_id="stop")
    async def stop_bash(self, interaction: discord.Interaction, button: discord.ui.Button):

        bucket = self.cooldown.get_bucket(interaction.message)
        retry = bucket.update_rate_limit()
        if retry:
            return await interaction.response.send_message("ERROR: Please do not spam commands.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        process = subprocess.Popen([stop_server_path])
        msg = await interaction.followup.send("Server shutdown initiated...", ephemeral=True)
        process.wait()
        await msg.edit(content="Server shutdown completed.")

#* Show server log
    @discord.ui.button(label="Show Server Log" ,style=discord.ButtonStyle.blurple, custom_id="log")
    async def show_log(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.defer(ephemeral=True)
        log_lines = read_last_lines(log_file_path, 15)
        await interaction.followup.send(f"```{log_lines}```", ephemeral=True)

#* Check for DST updates
    @discord.ui.button(label="Check for Updates", style=discord.ButtonStyle.grey, custom_id="check")
    async def check_updates(self, interaction: discord.Interaction, button: discord.ui.Button):
        
        await interaction.response.defer(ephemeral=True, thinking=True)
        if check_for_updates():
            await interaction.followup.send("There are updates available!", ephemeral=True)
        else:
            await interaction.followup.send("No updates available.", ephemeral=True)

#***************** Main *****************
client = MyClient()
tree = app_commands.CommandTree(client)

#***************** Slash Commands *****************
@tree.command(
    name="panel", 
    description="Opens the server control panel.", 
    guild=discord.Object(id=current_id),)
async def panel(interaction: discord.Interaction):
    await interaction.response.send_message("Choose your desired action.", view=PanelMenu())


@tree.command(
    name="log",
    description="Starts realtime view of log file for ~15 minutes.",
    guild=discord.Object(id=current_id),)
async def log(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False)
    enable_logging()
    msg = await interaction.followup.send("Currently logging:\n"+"```" + read_last_lines(log_file_path, 15) + "```")
    end_time = time.time() + 800
    while True:
        await asyncio.sleep(1)
        log_lines = read_last_lines(log_file_path, 15)
        if log_lines != msg.content[3:-3]:
            await msg.edit(content="Currently logging:\n"+"```" + log_lines + "```")
        if not is_logging():
            await msg.edit(content="Logging stopped.\n"+"```" + log_lines + "```")
            await asyncio.sleep(5)
            await msg.delete()
            break
        if time.time() > end_time:
            await msg.edit(content="Logging stopped due to inactivity.\n"+"```" + log_lines + "```")
            await asyncio.sleep(5)
            await msg.delete()
            break

@tree.command(
    name="stoplog",
    description="Stops realtime view of log file.",
    guild=discord.Object(id=current_id),)
async def stoplog(interaction: discord.Interaction):
    disable_logging()
    await interaction.response.send_message("Log view stopped.", ephemeral=True)

@tree.command(
    name="get_vm_info",
    description="Gets info about the virtual machine.",
    guild=discord.Object(id=current_id),)
async def get_ubuntu_info(interaction: discord.Interaction):
    ip, uptime, cpu, ram, disk = get_vm_info()
    await interaction.response.send_message(f"IP: {ip}\nUptime: {uptime}\nCPU usage: {cpu}\nRAM usage: {ram}\nDisk usage: {disk}", ephemeral=True)

@tree.command(
    name="send_to_cli",
    description="Sends a command to the server CLI.",
    guild=discord.Object(id=current_id),)
async def send_to_cli(interaction: discord.Interaction, command: str):
    await interaction.response.defer(ephemeral=True)
    process = subprocess.Popen([command], shell=True, stdout=subprocess.PIPE)
    process.wait()
    output = process.stdout.read().decode('utf-8')
    await interaction.followup.send(f"```{output}```", ephemeral=True)



#***************** General Use Functions *****************
#return last x lines from file as a string
def read_last_lines(file_name, line_count=10):
    with open(file_name) as f:
        lines = f.readlines()
        f.close()
    return "".join(lines[-line_count:])

#find text string in the last line of the log file, return false if not found
def check_log(log_file_path):
    with open(log_file_path) as f:
        lines = f.readlines()
        f.close()
    #if the log file is empty return false
    if len(lines) == 0:
        return False
    return lines[-1].find(not_running_text) != -1

#trim the log file to the last 100 lines
def trim_log(log_file_path):
    with open(log_file_path) as f:
        lines = f.readlines()
        f.close()
    if len(lines) > 100:
        with open(log_file_path, "w") as f:
            f.writelines(lines[-100:])
            f.close()
    return

#get key information about the vm
#NOTE: This is built around an ubuntu vm so you might have to edit the text processing before deployment
    #on different distros
def get_vm_info():
    #get the server's public IP address
    ip = requests.get("https://api.ipify.org").text
    try:
        #get the server's uptime
        uptime = subprocess.check_output(["uptime", "-p"]).decode("utf-8").strip()
        uptime = uptime.removeprefix("up ")
    except:
        uptime = "ERROR: Could not get uptime."
    try:
        #get the server's CPU usage
        cpu = subprocess.check_output(["top", "-bn1"]).decode("utf-8").splitlines()[0].strip()
        cpu = cpu.removeprefix("top - ")
        cpu = cpu.split(",")[-3].strip()
        cpu = cpu.removeprefix("load average: ").strip()
        cpu = round(float(cpu) * 100)
        cpu = f"{cpu}%"
    except:
        cpu = "ERROR: Could not get CPU usage."
    try:
        #get the server's RAM usage
        ram = subprocess.check_output(["free", "-m"]).decode("utf-8").splitlines()[1].strip()
        ram = ram.removeprefix("Mem:").strip().removeprefix("7946").strip()
        ram = ram.split(" ")[0]
        ram = round((float(ram) / 7946) * 100)
        ram = f"{ram}%"
    except:
        ram = "ERROR: Could not get RAM usage."
    try:
        #get the server's disk usage
        disk = subprocess.check_output(["df", "-h"]).decode("utf-8").splitlines()[1].strip()
        disk = disk.removeprefix("/dev/root").strip().removesuffix("/").strip()
        percent = disk.split(" ")[-1]

        disk = f"{percent}"
    except:
        disk = "ERROR: Could not get disk usage."
    
    return ip, uptime, cpu, ram, disk

# check for new updates to dst
def check_for_updates():
    global updates
    if updates != fs.get_past_update_info():
        print("there is a new update waiting to be installed")
        updates = fs.get_past_update_info()
        return True
    print("no new updates")
    return False


def disable_logging():
    global logging
    logging = False

def enable_logging():
    global logging
    logging = True

def is_logging():
    return logging


#***************** Tasks *****************
#automatically start the server if it is not running
@tasks.loop(seconds=600)
async def check_server():
    if check_log(log_file_path):
        print("Server shutdown detected. Starting server...")
        process = subprocess.Popen([start_server_path])
        process.wait()
    else: 
        trim_log(log_file_path)
        print("Server is running, trimming log file.")



#********** Events **********
@client.event
async def on_guild_join(guild):
    if guild.id not in allowed_servers:
        await guild.leave()

@client.event
async def on_message(message):
    if message.author == client.user:
        return


#********** Run **********
client.run(current_key)

# t.bot
# https://discord.com/api/oauth2/authorize?client_id=393195984122806272&permissions=43072&scope=bot%20applications.commands
# fall.bot
# https://discord.com/api/oauth2/authorize?client_id=978382261114241126&permissions=43072&scope=bot%20applications.commands