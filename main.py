import asyncio
import subprocess
import time
import requests
from random import sample
import os
from enum import Enum
import re
import emoji

import discord
from discord import app_commands
from discord.ext import commands, tasks

from key import key_fallBot, key_tBot, server_id, test_id, test_channel
import forum_scraper as fs
import helper_functions as hf


#********** File Paths **********

home_dir = os.path.expanduser("~")
scripts_dir = os.path.join(home_dir, "fall.bot", "scripts")
info_dir = os.path.join(home_dir, "fall.bot", "info")
temp_dir = os.path.join(home_dir, "fall.bot", "temp")

start_server_path = os.path.join(scripts_dir, "start_server.sh")
stop_server_path = os.path.join(scripts_dir, "stop_server.sh")
restart_server_path = os.path.join(scripts_dir, "restart_server.sh")
make_new_world_path = os.path.join(scripts_dir, "make_new_world.sh")
backup_path = os.path.join(scripts_dir, "backup.sh")

download_mod_path = os.path.join(scripts_dir, "download_mod.sh")





#********** Global Variables **********
allowed_servers = [server_id, test_id]
bot_channel_ids = allowed_servers
test_channels = [test_channel]
is_beta_server = False
cluster_name = "Template"
game_version = 500000
beta_game_version = 500000

previous_chat_log_count = 0
just_started = False

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

class SelectionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.select_branch = discord.ui.Select(placeholder="Select Branch", options=[
            discord.SelectOption(label="Main", value="main", emoji="🌲"),
            discord.SelectOption(label="Beta", value="beta", emoji="🔄"),
            discord.SelectOption(label="Cancel", value="Cancel", emoji="❌")], row=0, custom_id="branch")
        
        self.select_branch.callback = self.sel_branch
        self.add_item(self.select_branch)


    async def sel_branch(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if self.select_branch.values[0] == "Cancel":
            self.remove_item(self.select_branch)
            self.stop()
            await interaction.edit_original_response(view=self, content="Cancelled.")
            await asyncio.sleep(5)
            await interaction.delete_original_response()
            return
        print(str(interaction.user) + " changed the branch to " + self.select_branch.values[0])
        global is_beta_server
        is_beta_server = True if self.select_branch.values[0] == "beta" else False
        self.remove_item(self.select_branch)
        self.create_cluster_selection(is_beta_server)
        self.add_item(self.select_cluster)
        await interaction.edit_original_response(view=self)        


    def create_cluster_selection(self, is_beta_server):
        self.select_cluster = discord.ui.Select(placeholder="Select Cluster", options=
            hf.get_cluster_options(is_beta_server), row=0, custom_id="cluster")

        self.select_cluster.callback = self.sel_cluster


    async def sel_cluster(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        print(str(interaction.user) + " changed the cluster to " + self.select_cluster.values[0])
        global cluster_name
        cluster_name = self.select_cluster.values[0]
        self.remove_item(self.select_cluster)
        self.stop()
        branch = "Beta" if is_beta_server else "Main"
        await interaction.edit_original_response(view=self, content=f"Changed cluster to {cluster_name} on {branch} Branch.")




class PanelMenu(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.cooldown = commands.CooldownMapping.from_cooldown(1,5, commands.BucketType.default)


#* Start Server
    @discord.ui.button(label="Start Server", style=discord.ButtonStyle.success, row=1, custom_id="start", emoji="🟢")
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

        await asyncio.sleep(30)
        
        global previous_chat_log_count, server_state, just_started
        previous_chat_log_count = 0
        just_started = True
        server_state = ServerState.RUNNING
        # add delay before starting this to make sure it doesn't start before the server is ready
        send_chat_log.start()
        await msg.delete()

#* Stop server
    @discord.ui.button(label="Stop Server", style=discord.ButtonStyle.danger, row=1, custom_id="stop", emoji="🔴")
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
        await asyncio.sleep(5)
        await msg.delete()


#* Restart server
    @discord.ui.button(label="Restart Server", style=discord.ButtonStyle.blurple, row=1, custom_id="restart", emoji="🔄")
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

        await asyncio.sleep(30)
        
        global previous_chat_log_count, just_started
        previous_chat_log_count = 0
        just_started = True
        server_state = ServerState.RUNNING
        await msg.delete()

#* Check for DST updates
    @discord.ui.button(label="Check for Updates", style=discord.ButtonStyle.grey, row=2, custom_id="check", emoji="🔍")
    async def check_updates(self, interaction: discord.Interaction, button: discord.ui.Button):
        
        await interaction.response.defer(ephemeral=True, thinking=True)
        print(str(interaction.user) + " checked for updates.")
        global is_beta_server, game_version, beta_game_version
        if hf.check_for_updates(is_beta_server, game_version, beta_game_version):
            await interaction.followup.send("There are updates available!", ephemeral=True)
        else:
            await interaction.followup.send("No updates available.", ephemeral=True)

    @discord.ui.button(label="Change Cluster", style=discord.ButtonStyle.grey, row=2, custom_id="change_branch", emoji="🔄")
    async def change_branch(self, interaction: discord.Interaction, button: discord.ui.Button):
        print(str(interaction.user) + " started a branch/cluster change.")
        global is_beta_server, cluster_name
        text = f"Currently accessing {cluster_name} on the {'Beta' if is_beta_server else 'Main'} Branch."
        await interaction.response.send_message(content=text, view=SelectionView(), ephemeral=True)
    

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
    home_dir = os.path.expanduser("~")
    path = os.path.join(home_dir, ".klei", "DoNotStarveTogether", cluster_name) if branch == "main" else os.path.join(home_dir, ".klei", "DoNotStarveTogetherBetaBranch", cluster_name)
    
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
    await asyncio.sleep(5)
    await interaction.delete_original_response()


@tree.command(
    name="get_player_list",
    description="Gets the list of players on the server.",
    guild=discord.Object(id=current_id),)
async def get_player_list(interaction: discord.Interaction):
    print(str(interaction.user) + " requested the player list.")
    hf.dst_player_list()
    await interaction.response.send_message("Sent Player list to chat log.", ephemeral=True)
    await asyncio.sleep(5)
    await interaction.delete_original_response()

@tree.command(
    name="backup",
    description="Backs up the server.",
    guild=discord.Object(id=current_id),)
async def backup(interaction: discord.Interaction, cluster: str , branch: str):
    """
    Backs up the server.
    :param cluster: cluster name
    :param branch: main/beta
    """
    branch = branch.lower()
    if branch.startswith("b"):
        branch = "beta"
    else:
        branch = "main"
    print(str(interaction.user) + f" backed up {branch}/{cluster}.")
    process = subprocess.Popen([backup_path, cluster, branch])
    await interaction.response.send_message(f"Backed up {branch}/{cluster}.", ephemeral=True)
    await asyncio.sleep(5)
    await interaction.delete_original_response()

@tree.command(
    name="relink_chatlog",
    description="Relinks the chat log.",
    guild=discord.Object(id=current_id),)
async def relink_chatlog(interaction: discord.Interaction):
    global just_started, previous_chat_log_count, cluster_name, is_beta_server
    just_started = False
    previous_chat_log_count = hf.get_log_file_length(cluster_name, is_beta_server)
    
    send_chat_log.restart()
    await interaction.response.send_message("Relinked the chat log.", ephemeral=True)
    await asyncio.sleep(5)
    await interaction.delete_original_response()

@tree.command(
    name="enable_mod",
    description="Enables a mod on the server.",
    guild=discord.Object(id=current_id),)
async def enable_mod(interaction: discord.Interaction, mod_id: str):
    global cluster_name, is_beta_server
    # /enable_mod <id>
    # - adds mod id to mods/dedicated_server_mod_setup.lua
    path = os.path.join(home_dir, "dontstarvetogether_dedicated_server", "mods")
    with open(os.path.join(path, "dedicated_server_mods_setup.lua"), "a") as f:
        f.write(f'\nServerModSetup("{mod_id}")\n')
    f.close()
    # - downloads mod with steamcmd to temp folder
    if (not hf.has_mod_config(cluster_name, is_beta_server, mod_id)):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(f"Downloading mod: {mod_id}. This may take a while...", ephemeral=True)
        process = subprocess.Popen([download_mod_path, mod_id, temp_dir])
        process.wait()
    # - parses modinfo.lua for default config
        mod_config = hf.parse_modinfo(temp_dir, mod_id)
    # - saves mod id + config to world_enabledmods.txt
        hf.update_enabled_mods(cluster_name, is_beta_server, mod_id, mod_config, True)
        await interaction.followup.send(f"Mod: {mod_id} enabled on the server.", ephemeral=True)
    else:
        hf.update_enabled_mods(cluster_name, is_beta_server, mod_id, None, True)
        await interaction.response.send_message(f"Mod: {mod_id} already enabled on the server.", ephemeral=True)
        return
    # - recreates modoverride.lua from world_enabledmods.txt
    hf.create_modoverrides(cluster_name, is_beta_server)
    await interaction.followup.send(f"Mods overrides updated.", ephemeral=True)

    
@tree.command(
    name="disable_mod",
    description="Disables a mod on the server.",
    guild=discord.Object(id=current_id),)
async def disable_mod(interaction: discord.Interaction, mod_id: str):
    global cluster_name, is_beta_server
    # /disable_mod <id>
    # - removes mod id + config from world_enabledmods.txt]
    if (hf.has_mod_config(cluster_name, is_beta_server, mod_id)):
        hf.update_enabled_mods(cluster_name, is_beta_server, mod_id, None, False)
        await interaction.response.send_message(f"Mod: {mod_id} disabled on the server.", ephemeral=True)
    else:
        #no mod enabled already
        await interaction.response.send_message(f"ERR: Mod: {mod_id} not found on the server.", ephemeral=True)
        return
    # - recreates modoverride.lua from world_enabledmo
    hf.create_modoverrides(cluster_name, is_beta_server)
    await interaction.followup.send(f"Mods overrides updated.", ephemeral=True)
    
@tree.command(
    name="rewrite_modoverrides",
    description="Rewrites the modoverrides.",
    guild=discord.Object(id=current_id),)
async def rewrite_modoverrides(interaction: discord.Interaction):
    global cluster_name, is_beta_server

    hf.create_modoverrides(cluster_name, is_beta_server)
    await interaction.followup.send(f"Mods overrides updated.", ephemeral=True)
    
#********** Loops #**********
@tasks.loop(seconds=5)
async def send_chat_log():
    global cluster_name, is_beta_server, chat_log_channel, previous_chat_log_count
    path = hf.get_chat_log_path(cluster_name, is_beta_server)
    count = hf.get_log_file_length(cluster_name, is_beta_server)

    global just_started
    if just_started:
        if previous_chat_log_count - count > 25:
            return # still opening the old file
        just_started = False

    if count > previous_chat_log_count:
        if count - previous_chat_log_count > 100:
            return # too many messages
        text = ""
        with open(path, "r", errors="ignore") as f:
            # fix the encoding

            lines = f.readlines()
            for i in range(count - previous_chat_log_count):
                line = lines[-(count - previous_chat_log_count - i)]
                line = line[12:]
                if line.startswith("[System Message] @"):
                    continue
                if line.startswith("[Whisper]"):
                    continue
                if line.startswith("[Say]"):
                    line = line[20:]
                
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
            
        msg = emoji.demojize(message.content)
        
        full_message_to_announce = f"@{message.author}: {msg}"

        hf.dst_announce(full_message_to_announce)





#********** Run **********
client.run(current_key)

# t.bot
# https://discord.com/api/oauth2/authorize?client_id=393195984122806272&permissions=43072&scope=bot%20applications.commands
# fall.bot
# https://discord.com/api/oauth2/authorize?client_id=978382261114241126&permissions=43072&scope=bot%20applications.commands
