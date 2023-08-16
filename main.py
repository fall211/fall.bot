import asyncio
import subprocess
import time
import requests
from random import sample
import os

import discord
from discord import app_commands
from discord.ext import commands, tasks

from key import key_fallBot, key_tBot, server_id, test_id, test_channel
import forum_scraper as fs


#********** File Paths **********

start_server_path = "/home/steam/start_server.sh"
stop_server_path = "/home/steam/stop_server.sh"
restart_server_path = "/home/steam/restart_server.sh"
make_new_world_path = "/home/steam/fall.bot/make_new_world.sh"




#********** Global Variables **********
allowed_servers = [server_id, test_id]
bot_channel_ids = allowed_servers
test_channels = [test_channel]
is_beta_server = False
cluster_name = "Roots"
game_version = 500000
beta_game_version = 500000

previous_chat_log_count = 0
is_server_running = False




#! Change these before deployment.
current_key = key_fallBot

current_id = server_id if current_key == key_fallBot else test_id
chat_log_channel = 1087449487376666624 if current_key == key_fallBot else 1042213192383877263

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

        fs.update_dict()

        global is_beta_server, game_version, beta_game_version

        await client.change_presence(activity=discord.Activity(name="user commands", type=discord.ActivityType.listening))

        if current_key == key_fallBot:
            
            game_version = fs.get_latest_update_info_from_dict(beta=False)
            beta_game_version = fs.get_latest_update_info_from_dict(beta=True)

            global previous_chat_log_count, cluster_name, is_server_running
            previous_chat_log_count = get_log_file_length(cluster_name, is_beta_server)

            send_chat_log.start()
            is_server_running = True



class PanelMenu(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.cooldown = commands.CooldownMapping.from_cooldown(1,5, commands.BucketType.default)



#* Start Server
    @discord.ui.button(label="Start Server", style=discord.ButtonStyle.success, row=1, custom_id="start")
    async def start_bash(self, interaction: discord.Interaction, button: discord.ui.Button):

        bucket = self.cooldown.get_bucket(interaction.message)
        retry = bucket.update_rate_limit()
        if retry:
            return await interaction.response.send_message("ERROR: Please do not spam commands.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        global is_beta_server, game_version, beta_game_version, cluster_name
        process = subprocess.Popen([start_server_path, cluster_name, str(is_beta_server)])
        msg = await interaction.followup.send("Server startup initated...", ephemeral=True)
        process.wait()
        if is_beta_server:
            beta_game_version = fs.get_latest_update_info_from_dict(beta=True)
            await client.change_presence(activity=discord.Game(name="Beta Don't Starve Together"))
        else:
            game_version = fs.get_latest_update_info_from_dict(beta=False)
            await client.change_presence(activity=discord.Game(name="Don't Starve Together"))
                
        await msg.edit(content="Server will soon be online.")

        global previous_chat_log_count, is_server_running
        previous_chat_log_count = 0
        is_server_running = True
        if send_chat_log.is_running():
            send_chat_log.restart()
        else:
            send_chat_log.start()

#* Stop server
    @discord.ui.button(label="Stop Server", style=discord.ButtonStyle.danger, row=1, custom_id="stop")
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

        await client.change_presence(activity=discord.Activity(name="user commands", type=discord.ActivityType.listening))

        global is_server_running
        is_server_running = False
        send_chat_log.stop()


#* Restart server
    @discord.ui.button(label="Restart Server", style=discord.ButtonStyle.blurple, row=1, custom_id="restart")
    async def restart_bash(self, interaction: discord.Interaction, button: discord.ui.Button):

        bucket = self.cooldown.get_bucket(interaction.message)
        retry = bucket.update_rate_limit()
        if retry:
            return await interaction.response.send_message("ERROR: Please do not spam commands.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        global is_beta_server, game_version, beta_game_version, cluster_name
        process = subprocess.Popen([restart_server_path, cluster_name, str(is_beta_server)])
        msg = await interaction.followup.send("Server restart initiated...", ephemeral=True)
        process.wait()
        if is_beta_server:
            beta_game_version = fs.get_latest_update_info_from_dict(beta=True)
        else:
            game_version = fs.get_latest_update_info_from_dict(beta=False)
        await msg.edit(content="Server will soon be online.")

        global previous_chat_log_count
        previous_chat_log_count = 0

#* Check for DST updates
    @discord.ui.button(label="Check for Updates", style=discord.ButtonStyle.grey, row=2, custom_id="check")
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
    await interaction.response.send_message(view=PanelMenu())

@tree.command(
    name="get_vm_info",
    description="Gets info about the virtual machine.",
    guild=discord.Object(id=current_id),)
async def get_ubuntu_info(interaction: discord.Interaction):
    ip, uptime, cpu, ram, disk = get_vm_info()
    await interaction.response.send_message(f"IP: {ip}\nUptime: {uptime}\nCPU usage: {cpu}\nRAM usage: {ram}\nDisk usage: {disk}", ephemeral=True)

@tree.command(
    name="change_branch",
    description="Changes the branch of the server.",
    guild=discord.Object(id=current_id),)
async def change_branch(interaction: discord.Interaction, branch: str):
    """
    Changes the server branch.
    :param branch: main/beta
    """

    global is_beta_server
    
    if branch == "beta":
        is_beta_server = True
    elif branch == "main":
        is_beta_server = False
    else:
        await interaction.response.send_message("ERROR: Invalid branch.", ephemeral=True)
        return
    await interaction.response.send_message(f"Server branch changed to {'beta' if is_beta_server else 'main'}", ephemeral=True)


@tree.command(
    name="change_cluster",
    description="Changes the cluster name.",
    guild=discord.Object(id=current_id),)
async def change_cluster(interaction: discord.Interaction, cluster: str):
    
    global cluster_name
    cluster_name = cluster
    await interaction.response.send_message(f"Bot now accessing {cluster}.", ephemeral=True)
    return

@tree.command(
    name="new_world",
    description="Creates a new world. Requires a zip of the server files.",
    guild=discord.Object(id=current_id),)
async def new_world(interaction: discord.Interaction, cluster_name: str, branch: str, type: str):
    """
    creates a new world.
    :param cluster_name: the name of the cluster to create a new world for
    :param branch: main/beta
    :param type: main/relaxed
    """
    await interaction.response.defer(ephemeral=True)

    if branch != "main" and branch != "beta":
        await interaction.response.send_message("ERROR: Invalid branch.", ephemeral=True)
        return
    if type != "main" and type != "relaxed":
        await interaction.response.send_message("ERROR: Invalid type.", ephemeral=True)
        return

    # check if the cluster name already exists
    if branch == "main":
        path = f"/home/steam/.klei/DoNotStarveTogether/{cluster_name}"
    else:
        path = f"/home/steam/.klei/DoNotStarveTogetherBetaBranch/{cluster_name}"
    if os.path.exists(path):
        await interaction.response.send_message("ERROR: Cluster with the given name already exists.", ephemeral=True)
        return

    await interaction.followup.send("Please send a zip with the save files.", ephemeral=True)
    # wait for the zip file
    def check(message):
        return message.author == interaction.user and message.attachments != []
    message = await client.wait_for("message", check=check)
    # download the zip file
    url = message.attachments[0].url
    r = requests.get(url, allow_redirects=True)
    open('cluster.zip', 'wb').write(r.content)

    # run the bash script
    process = subprocess.Popen([make_new_world_path, cluster_name, branch, type])
    process.wait()

    await message.delete()
    await interaction.followup.send(f"Created a new world with name {cluster_name}", ephemeral=True)



#***************** General Use Functions *****************
def get_chat_log_path(cluster_name, beta=False):
    if beta:
        return f"/home/steam/.klei/DoNotStarveTogetherBetaBranch/{cluster_name}/Master/server_chat_log.txt"
    else:
        return f"/home/steam/.klei/DoNotStarveTogether/{cluster_name}/Master/server_chat_log.txt"
    
def get_server_log_path(cluster_name, beta=False):
    if beta:
        return f"/home/steam/.klei/DoNotStarveTogetherBetaBranch/{cluster_name}/Master/server_log.txt"
    else:
        return f"/home/steam/.klei/DoNotStarveTogether/{cluster_name}/Master/server_log.txt"

#get key information about the vm
#NOTE: This is built around an ubuntu vm so you might have to edit the text processing before deployment
    #on different machines
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
    fs.update_dict()
    global is_beta_server, game_version, beta_game_version
    latest_version = fs.get_latest_update_info_from_dict(is_beta_server)
    if is_beta_server:
        return latest_version != beta_game_version
    else:
        return latest_version != game_version

def get_log_file_length(cluster_name, is_beta_server):
    path = get_chat_log_path(cluster_name, is_beta_server)
    f = open(path, 'rb')
    len = sum(1 for i in f)
    f.close()
    return len



#***************** Tasks *****************
@tasks.loop(seconds=5)
async def send_chat_log():
    global cluster_name, is_beta_server, chat_log_channel, previous_chat_log_count
    path = get_chat_log_path(cluster_name, is_beta_server)
    count = get_log_file_length(cluster_name, is_beta_server)

    if count > previous_chat_log_count:
        text = ""
        with open(path, "r", errors="ignore") as f:
            # fix the encoding

            lines = f.readlines()
            for i in range(count - previous_chat_log_count):
                line = lines[-(count - previous_chat_log_count - i)]
                line = line[12:]
                if line.find("[Discord]") != -1:
                    continue
                await client.get_channel(chat_log_channel).send(line)
            previous_chat_log_count = count
        f.close()



#********** Events **********
@client.event
async def on_guild_join(guild):
    if guild.id not in allowed_servers:
        await guild.leave()

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if message.channel.id == chat_log_channel:

        if not is_server_running:
            return
        
        full_message_to_announce = f"[Discord] {message.author}: {message.content}"

        screen_cmd = f'screen -S s -X stuff "TheNet:SystemMessage(\'{full_message_to_announce}\')^M"'
        subprocess.run(screen_cmd, shell=True)  # send the message to the screen session




#********** Run **********
client.run(current_key)

# t.bot
# https://discord.com/api/oauth2/authorize?client_id=393195984122806272&permissions=43072&scope=bot%20applications.commands
# fall.bot
# https://discord.com/api/oauth2/authorize?client_id=978382261114241126&permissions=43072&scope=bot%20applications.commands