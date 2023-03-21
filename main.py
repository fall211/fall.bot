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

start_server_path = "/home/steam/start_server.sh"
stop_server_path = "/home/steam/stop_server.sh"
restart_server_path = "/home/steam/restart_server.sh"




#********** Variables **********
not_running_text = "steam@instance-dst"
allowed_servers = [server_id, test_id]
test_channels = [test_channel]
is_beta_server = False
cluster_name = "Wilson"
game_version = 500000
beta_game_version = 500000

previous_chat_log_count = 0




#! Change these before deployment.
current_id = server_id
current_key = key_fallBot
bot_channel_ids = allowed_servers
chat_log_channel = 1087449487376666624

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

        global is_beta_server
        global game_version, beta_game_version
        if is_beta_server:
            await client.change_presence(activity=discord.Game(name="Beta Don't Starve Together"))
        else:
            await client.change_presence(activity=discord.Game(name="Don't Starve Together"))
        
        game_version = fs.get_latest_update_info_from_dict(beta=False)
        beta_game_version = fs.get_latest_update_info_from_dict(beta=True)

        global previous_chat_log_count, cluster_name
        previous_chat_log_count = get_log_file_length(cluster_name, is_beta_server)

        send_chat_log.start()


class PanelMenu(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.cooldown = commands.CooldownMapping.from_cooldown(1,5, commands.BucketType.default)

#***************** Buttons *****************

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
        else:
            game_version = fs.get_latest_update_info_from_dict(beta=False)
        await msg.edit(content="Server will soon be online.")

        global previous_chat_log_count
        previous_chat_log_count = 0

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

        global previous_chat_log_count
        previous_chat_log_count = 0

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
        process.wait(timeout=100)
        if is_beta_server:
            beta_game_version = fs.get_latest_update_info_from_dict(beta=True)
        else:
            game_version = fs.get_latest_update_info_from_dict(beta=False)
        await msg.edit(content="Server will soon be online.")

        global previous_chat_log_count
        previous_chat_log_count = 0

#* Change between beta and live server
    @discord.ui.button(label="Change Server", style=discord.ButtonStyle.gray, row=2, custom_id="change")
    async def change_server(self, interaction: discord.Interaction, button: discord.ui.Button):
        bucket = self.cooldown.get_bucket(interaction.message)
        retry = bucket.update_rate_limit()
        if retry:
            return await interaction.response.send_message("ERROR: Please do not spam commands.", ephemeral=True)
        
        await interaction.response.defer(ephemeral=True)
        global is_beta_server        
        if is_beta_server:
            await interaction.followup.send("Bot is currently accessing the beta branch! Are you sure you want to change to the live server? (yes/no)", ephemeral=True)
        else:
            await interaction.followup.send("Bot is currently accessing the live branch! Are you sure you want to change to the beta server? (yes/no)", ephemeral=True)

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel
        
        try:
            msg = await client.wait_for('message', check=check, timeout=15.0)
        except asyncio.TimeoutError:
            await interaction.followup.send('Timed out waiting for a response.', ephemeral=True)
        else:
            if msg.content.lower() == 'yes' or msg.content.lower() == 'y':
                is_beta_server = not is_beta_server
                if is_beta_server:
                    await interaction.followup.send("Bot now accessing beta server", ephemeral=True)
                    await client.change_presence(activity=discord.Game(name="Beta Don't Starve Together"))
                else:
                    await interaction.followup.send("Bot now accessing live server", ephemeral=True)
                    await client.change_presence(activity=discord.Game(name="Don't Starve Together"))
            else:
                await interaction.followup.send("Server change cancelled.", ephemeral=True)
            
            await msg.delete()
            return

#* Change the cluster name
    @discord.ui.button(label="Change Cluster", style=discord.ButtonStyle.gray, row=2, custom_id="cluster")
    async def change_cluster(self, interaction: discord.Interaction, button: discord.ui.Button):
        bucket = self.cooldown.get_bucket(interaction.message)
        retry = bucket.update_rate_limit()
        if retry:
            return await interaction.response.send_message("ERROR: Please do not spam commands.", ephemeral=True)
        
        global cluster_name
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("Currently accessing cluster: " + cluster_name, ephemeral=True)
        await interaction.followup.send("What is the name of the cluster you want to access? (case sensitive).\n\"cancel\" to cancel.", ephemeral=True)

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

#* Show server log
    @discord.ui.button(label="Show Server Log" ,style=discord.ButtonStyle.gray, row=2, custom_id="log")
    async def show_log(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("This feature is under development.", ephemeral=True)
        # TODO: send log file

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
    await interaction.response.send_message("Choose your desired action.", view=PanelMenu())

@tree.command(
    name="get_vm_info",
    description="Gets info about the virtual machine.",
    guild=discord.Object(id=current_id),)
async def get_ubuntu_info(interaction: discord.Interaction):
    ip, uptime, cpu, ram, disk = get_vm_info()
    await interaction.response.send_message(f"IP: {ip}\nUptime: {uptime}\nCPU usage: {cpu}\nRAM usage: {ram}\nDisk usage: {disk}", ephemeral=True)



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
    fs.update_dict()
    global is_beta_server, game_version, beta_game_version
    latest_version = fs.get_latest_update_info_from_dict(is_beta_server)
    if is_beta_server:
        return latest_version != beta_game_version
    else:
        return latest_version != game_version

def get_log_file_length(cluster_name, is_beta_server):
    path = get_server_log_path(cluster_name, is_beta_server)
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


#********** Run **********
client.run(current_key)

# t.bot
# https://discord.com/api/oauth2/authorize?client_id=393195984122806272&permissions=43072&scope=bot%20applications.commands
# fall.bot
# https://discord.com/api/oauth2/authorize?client_id=978382261114241126&permissions=43072&scope=bot%20applications.commands