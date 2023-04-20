import asyncio
import subprocess
import time
import requests
from random import sample

import discord
from discord import app_commands
from discord.ext import commands, tasks

from key import key_fallBot, key_tBot, server_id, test_id, test_channel
import forum_scraper as fs


#********** File Paths **********

start_server_path = "/home/steam/start_server.sh"
stop_server_path = "/home/steam/stop_server.sh"
restart_server_path = "/home/steam/restart_server.sh"




#********** Global Variables **********
allowed_servers = [server_id, test_id]
bot_channel_ids = allowed_servers
test_channels = [test_channel]
is_beta_server = False
cluster_name = "Wilson"
game_version = 500000
beta_game_version = 500000

previous_chat_log_count = 0
is_server_running = False

target = "fall"
ccc_commands = {
    "Increase Player Size": f"f_increaseScale(\'{target}\')",
    "Reset Player Size": f"f_resetScale(\'{target}\')",
    "Spawn a Random Mob": f"f_spawnRandomMob(\'{target}\')",
}


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

            if previous_chat_log_count > 0:
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

class CCCMenu(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=15)

        sampled_commands = sample(list(ccc_commands), 3)

        for command in sampled_commands:
            button = discord.ui.Button(label=f"{command}", style=discord.ButtonStyle.grey, custom_id=f"{command}")
            button.callback = lambda _, btn = button: self.on_button_click(_, btn)
            self.add_item(button)
        
    async def on_button_click(self, interaction: discord.Interaction, button: discord.ui.Button):

        ccc = button.custom_id
        command = ccc_commands[ccc]
        print(f"Running command: {command}")
        screen_cmd = f'screen -S s -X stuff "{command}^M"'
        subprocess.run(screen_cmd, shell=True)  # runs the command in the screen session

        self.stop()
        



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
async def change_branch(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    global is_beta_server, is_server_running
    if is_server_running:
        await interaction.followup.send("Server must be offline to change branch.", ephemeral=True)
        return
    
    await interaction.followup.send(f"Current branch is {'beta' if is_beta_server else 'live'}\nAre you sure you want to change the branch? (y/n)", ephemeral=True)
    
    def check(m):
        return m.author == interaction.user and m.channel == interaction.channel
    
    try:
        msg = await client.wait_for('message', check=check, timeout=15.0)
    except asyncio.TimeoutError:
        await interaction.followup.send('Timed out waiting for a response.', ephemeral=True)
        return
    if msg.content.lower() == "n":
        await interaction.followup.send("Branch change cancelled.", ephemeral=True)
        await msg.delete()
        return
    await msg.delete()
    is_beta_server = not is_beta_server
    await interaction.followup.send(f"Server branch changed to {'beta' if is_beta_server else 'live'}", ephemeral=True)

    game_name = "Beta Don't Starve Together" if is_beta_server else "Don't Starve Together"
    await client.change_presence(activity=discord.Game(name=f"{game_name}"))

@tree.command(
    name="change_cluster",
    description="Changes the cluster name.",
    guild=discord.Object(id=current_id),)
async def change_cluster(interaction: discord.Interaction):
    
    global cluster_name, is_server_running
    if is_server_running:
        await interaction.response.send_message("Server must be offline to change cluster.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    await interaction.followup.send(f"Currently accessing cluster: {cluster_name}\nWhat is the name of the cluster you want to access? (case sensitive).\n\"cancel\" to cancel.", ephemeral=True)

    def check(m):
        return m.author == interaction.user and m.channel == interaction.channel
    
    try:
        msg = await client.wait_for('message', check=check, timeout=15.0)
    except asyncio.TimeoutError:
        await interaction.followup.send('Timed out waiting for a response.', ephemeral=True)
    else:
        if msg.content.lower() == "cancel":
            await interaction.followup.send("Cluster change cancelled.", ephemeral=True)
            await msg.delete()
            return
        cluster_name = msg.content
        await interaction.followup.send(f"Bot now accessing cluster {cluster_name}", ephemeral=True)
        await msg.delete()
        return

@tree.command(
    name="ccc",
    description="opens the CCC discord-sided menu",
    guild=discord.Object(id=current_id),)
async def ccc(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False)
    global is_server_running
    if not is_server_running:
        await interaction.followup.send("Server is not running.", ephemeral=True)
        return
    view = CCCMenu()
    message = await interaction.followup.send(f"Quick! Pick a consequence for {target}!", view=view)
    await view.wait()
    await message.delete()

@tree.command(
    name="toggle_shenanigans",
    description="Starts/stops shenanigans.",
    guild=discord.Object(id=current_id),)
async def toggle_ccc_task(interaction: discord.Interaction):

    global is_server_running
    if not is_server_running:

        if send_ccc_prompt.is_running():
            send_ccc_prompt.stop()
            await interaction.response.send_message("Shenanigans stopped.", ephemeral=False)
            return

        await interaction.response.send_message("Server is not running.", ephemeral=True)
    elif not send_ccc_prompt.is_running():
        send_ccc_prompt.start()
        await interaction.response.send_message(f"Shenanigans started. Current target is {target}.", ephemeral=False)
        await client.get_channel(interaction.channel_id).send("Use /change_target to change the target.")
    else:
        send_ccc_prompt.stop()
        await interaction.response.send_message("Shenanigans stopped.", ephemeral=False)

@tree.command(
    name="change_target",
    description="Changes the target of shenanigans.",
    guild=discord.Object(id=current_id),)
async def change_target_parameter(interaction: discord.Interaction, player: str):
    global target
    target = player
    await interaction.response.send_message(f"Shenanigans now targeting {target}", ephemeral=False)


@tree.command(
    name="list_players",
    description="Lists all players on the server.",
    guild=discord.Object(id=current_id),)
async def list_players(interaction: discord.Interaction):
    global is_server_running
    if not is_server_running:
        await interaction.response.send_message("Server is not running.", ephemeral=True)
        return
    await interaction.response.send_message("Getting player list...", ephemeral=True)
    command = "f_announcePlayers()"
    screen_cmd = f'screen -S s -X stuff "{command}^M"'
    subprocess.run(screen_cmd, shell=True)  # runs the command in the screen session


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
        with open(path, "r") as f:
            lines = f.readlines()
            for i in range(count - previous_chat_log_count):
                line = lines[-(count - previous_chat_log_count - i)]
                line = line[12:]
                if line.find("] [Discord]") != -1:
                    continue
                await client.get_channel(chat_log_channel).send(line)
        previous_chat_log_count = count
        f.close()

@tasks.loop(seconds=300)
async def send_ccc_prompt():
    if not is_server_running:
        send_ccc_prompt.stop()
        return
    
    view = CCCMenu()
    message = await client.get_channel(chat_log_channel).send(f"Quick! Pick a consequence for {target}!", view=view)
    await view.wait()
    await message.delete()

#********** Events **********
@client.event
async def on_guild_join(guild):
    if guild.id not in allowed_servers:
        await guild.leave()

@client.event
async def on_message(message):
    if message.author == client.user:
        if message.content.find("Shenanigans") == -1:
            return
    
    if message.channel.id == chat_log_channel:

        if not is_server_running:
            return
        
        full_message_to_announce = ""
        if message.author == client.user:
            full_message_to_announce = message.content
        else:
            full_message_to_announce = f"[Discord] {message.author}: {message.content}"

        screen_cmd = f'screen -S s -X stuff "c_announce(\'{full_message_to_announce}\')^M"'
        subprocess.run(screen_cmd, shell=True)  # send the message to the screen session




#********** Run **********
client.run(current_key)

# t.bot
# https://discord.com/api/oauth2/authorize?client_id=393195984122806272&permissions=43072&scope=bot%20applications.commands
# fall.bot
# https://discord.com/api/oauth2/authorize?client_id=978382261114241126&permissions=43072&scope=bot%20applications.commands