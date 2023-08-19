import asyncio
import subprocess
import time
import requests
from random import sample
import os
from enum import Enum

import discord
from discord import app_commands
from discord.ext import commands, tasks

from key import key_fallBot, key_tBot, server_id, test_id, test_channel
import forum_scraper as fs
import helper_functions as hf


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

# server state
class ServerState(Enum):
    STARTING = 1
    RUNNING = 2
    STOPPING = 3
    STOPPED = 4
    RESTARTING = 5

server_state = ServerState.STOPPED


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
        print("Logged in as: " + self.user.name, self.user.id)

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
        print(str(interaction.user) + " started the server.")
        global is_beta_server, game_version, beta_game_version, cluster_name
        process = subprocess.Popen([start_server_path, cluster_name, str(is_beta_server)])
        msg = await interaction.followup.send("Server startup initated...", ephemeral=True)
        if is_beta_server:
            beta_game_version = fs.get_latest_update_info_from_dict(beta=True)
            await client.change_presence(activity=discord.Game(name="Beta Don't Starve Together"))
        else:
            game_version = fs.get_latest_update_info_from_dict(beta=False)
            await client.change_presence(activity=discord.Game(name="Don't Starve Together"))
                
        await msg.edit(content="Server will soon be online.")

        global previous_chat_log_count, server_state
        await asyncio.sleep(30)
        previous_chat_log_count = 0
        server_state = ServerState.RUNNING
        # add delay before starting this to make sure it doesn't start before the server is ready
        send_chat_log.start()

#* Stop server
    @discord.ui.button(label="Stop Server", style=discord.ButtonStyle.danger, row=1, custom_id="stop")
    async def stop_bash(self, interaction: discord.Interaction, button: discord.ui.Button):

        bucket = self.cooldown.get_bucket(interaction.message)
        retry = bucket.update_rate_limit()
        if retry:
            return await interaction.response.send_message("ERROR: Please do not spam commands.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        print(str(interaction.user) + " stopped the server.")
        global server_state
        server_state = ServerState.STOPPING
        hf.dst_announce("[Discord] Server is shutting down in 5 seconds.")
        await asyncio.sleep(5)

        process = subprocess.Popen([stop_server_path])
        msg = await interaction.followup.send("Server shutdown initiated...", ephemeral=True)
        await msg.edit(content="Server will soon be shutdown.")

        await client.change_presence(activity=discord.Activity(name="user commands", type=discord.ActivityType.listening))

        server_state = ServerState.STOPPED
        send_chat_log.stop()


#* Restart server
    @discord.ui.button(label="Restart Server", style=discord.ButtonStyle.blurple, row=1, custom_id="restart")
    async def restart_bash(self, interaction: discord.Interaction, button: discord.ui.Button):

        bucket = self.cooldown.get_bucket(interaction.message)
        retry = bucket.update_rate_limit()
        if retry:
            return await interaction.response.send_message("ERROR: Please do not spam commands.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        print(str(interaction.user) + " restarted the server.")

        hf.dst_announce("[Discord] Server is restarting in 5 seconds.")
        await asyncio.sleep(5)
        global server_state
        server_state = ServerState.RESTARTING

        global is_beta_server, game_version, beta_game_version, cluster_name
        process = subprocess.Popen([restart_server_path, cluster_name, str(is_beta_server)])
        msg = await interaction.followup.send("Server restart initiated...", ephemeral=True)
        if is_beta_server:
            beta_game_version = fs.get_latest_update_info_from_dict(beta=True)
        else:
            game_version = fs.get_latest_update_info_from_dict(beta=False)
        await msg.edit(content="Server will soon be online.")

        global previous_chat_log_count
        await asyncio.sleep(30)
        previous_chat_log_count = 0
        server_state = ServerState.RUNNING

#* Check for DST updates
    @discord.ui.button(label="Check for Updates", style=discord.ButtonStyle.grey, row=2, custom_id="check")
    async def check_updates(self, interaction: discord.Interaction, button: discord.ui.Button):
        
        await interaction.response.defer(ephemeral=True, thinking=True)
        print(str(interaction.user) + " checked for updates.")
        global is_beta_server, game_version, beta_game_version
        if hf.check_for_updates(is_beta_server, game_version, beta_game_version):
            await interaction.followup.send("There are updates available!", ephemeral=True)
        else:
            await interaction.followup.send("No updates available.", ephemeral=True)

        

#********** Main #**********
client = MyClient()
tree = app_commands.CommandTree(client)

#********** Slash Commands #**********
@tree.command(
    name="panel", 
    description="Opens the server control panel.", 
    guild=discord.Object(id=current_id),)
async def panel(interaction: discord.Interaction):
    print(str(interaction.user) + " opened the panel.")
    await interaction.response.send_message(view=PanelMenu())

@tree.command(
    name="get_vm_info",
    description="Gets info about the virtual machine.",
    guild=discord.Object(id=current_id),)
async def get_ubuntu_info(interaction: discord.Interaction):
    print(str(interaction.user) + " requested vm info.")
    ip, uptime, cpu, ram, disk = hf.get_vm_info()
    await interaction.response.send_message(f"IP: {ip}\nUptime: {uptime}\nCPU usage: {cpu}\nRAM usage: {ram}\nDisk usage: {disk}", ephemeral=True)


@tree.command(
    name="get_cluster_names",
    description="Gets the names of all the clusters.",
    guild=discord.Object(id=current_id),)
async def get_cluster_names(interaction: discord.Interaction):
    print(str(interaction.user) + " requested cluster names.")
    names = hf.get_clusters()
    await interaction.response.send_message(f"{names}", ephemeral=True)


@tree.command(
    name="change_branch",
    description="Changes the branch of the server.",
    guild=discord.Object(id=current_id),)
async def change_branch(interaction: discord.Interaction, branch: str):
    """
    Changes the server branch.
    :param branch: main/beta
    """
    branch = branch.lower()
    print(str(interaction.user) + " changed the branch to " + branch)
    
    global is_beta_server
    is_beta_server = True if branch.startswith("beta") else False

    await interaction.response.send_message(f"Server branch changed to {'beta' if is_beta_server else 'main'}", ephemeral=True)


@tree.command(
    name="change_cluster",
    description="Changes the cluster name.",
    guild=discord.Object(id=current_id),)
async def change_cluster(interaction: discord.Interaction, cluster: str):
    """
    Changes the cluster.
    :param cluster: cluster name, get list with /get_cluster_names
    """
    print(str(interaction.user) + " changed the cluster to " + cluster)
    global cluster_name
    cluster_name = cluster
    await interaction.response.send_message(f"Changed cluster to {cluster}.", ephemeral=True)


@tree.command(
    name="new_world",
    description="Creates a new world. Requires a zip of the server files.",
    guild=discord.Object(id=current_id),)
async def new_world(interaction: discord.Interaction, cluster_name: str, branch: str, difficulty: str):
    """
    creates a new world.
    :param cluster_name: entering an existing cluster name will not overwrite it
    :param branch: enter only main/beta
    :param difficulty: enter only main/relaxed
    """
    await interaction.response.defer(ephemeral=True)
    branch = branch.lower(); difficulty = difficulty.lower()
    print(str(interaction.user) + " attempted to create a new world with name " + cluster_name + " on branch " + branch + " with difficulty " + difficulty)

    if branch != "main" and branch != "beta":
        await interaction.response.send_message("ERROR: Invalid branch.", ephemeral=True)
        return
    if difficulty != "main" and difficulty != "relaxed":
        await interaction.response.send_message("ERROR: Invalid difficulty.", ephemeral=True)
        return

    # check if the cluster name already exists
    path = f"/home/steam/.klei/DoNotStarveTogether/{cluster_name}" if branch == "main" else f"/home/steam/.klei/DoNotStarveTogetherBetaBranch/{cluster_name}"
    if os.path.exists(path):
        await interaction.response.send_message("ERROR: Cluster with the given name already exists.", ephemeral=True)
        return

    await interaction.followup.send("Please send a zip file with save files for the world.", ephemeral=True)
    # wait for the zip file
    def check(message):
        return message.author == interaction.user and message.attachments != []
    message = await client.wait_for("message", check=check)
    # download the zip file
    url = message.attachments[0].url
    r = requests.get(url, allow_redirects=True)
    open('cluster.zip', 'wb').write(r.content)

    # run the bash script
    process = subprocess.Popen([make_new_world_path, cluster_name, branch, difficulty])

    await message.delete()
    await interaction.followup.send(f"Created a new world with name {cluster_name}", ephemeral=True)


@tree.command(
    name="get_player_list",
    description="Gets the list of players on the server.",
    guild=discord.Object(id=current_id),)
async def get_player_list(interaction: discord.Interaction):
    print(str(interaction.user) + " requested the player list.")
    hf.dst_player_list()
    await interaction.response.send_message("Getting Player list.", ephemeral=True)


#********** Loops #**********
@tasks.loop(seconds=5)
async def send_chat_log():
    global cluster_name, is_beta_server, chat_log_channel, previous_chat_log_count
    path = hf.get_chat_log_path(cluster_name, is_beta_server)
    count = hf.get_log_file_length(cluster_name, is_beta_server)


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

        if server_state == ServerState.STOPPED:
            return
        
        full_message_to_announce = f"[Discord] {message.author}: {message.content}"

        hf.dst_announce(full_message_to_announce)





#********** Run **********
client.run(current_key)

# t.bot
# https://discord.com/api/oauth2/authorize?client_id=393195984122806272&permissions=43072&scope=bot%20applications.commands
# fall.bot
# https://discord.com/api/oauth2/authorize?client_id=978382261114241126&permissions=43072&scope=bot%20applications.commands