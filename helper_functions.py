import requests
import subprocess
import shlex
import os
import forum_scraper as fs

import discord


#***************** General Use Functions *****************
def get_chat_log_path(cluster_name, beta=False):
    user_home = os.path.expanduser("~")
    if beta:
        return os.path.join(user_home, ".klei", "DoNotStarveTogetherBetaBranch", cluster_name, "Master", "server_chat_log.txt")
    else:
        return os.path.join(user_home, ".klei", "DoNotStarveTogether", cluster_name, "Master", "server_chat_log.txt")

def get_server_log_path(cluster_name, beta=False):
    user_home = os.path.expanduser("~")
    if beta:
        return os.path.join(user_home, ".klei", "DoNotStarveTogetherBetaBranch", cluster_name, "Master", "server_log.txt")
    else:
        return os.path.join(user_home, ".klei", "DoNotStarveTogether", cluster_name, "Master", "server_log.txt")

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
def check_for_updates(is_beta_server, game_version, beta_game_version):
    fs.update_dict()
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


def get_cluster_options(is_beta_server):
    user_home = os.path.expanduser("~")
    path_live = os.path.join(user_home, ".klei", "DoNotStarveTogether")
    path_beta = os.path.join(user_home, ".klei", "DoNotStarveTogetherBetaBranch")

    path = path_beta if is_beta_server else path_live


    names = os.listdir(path)

    options = []
    for name in names:
        if name == "Template":
            continue
        selection = discord.SelectOption(label=name, value=name)
        options.append(selection)

    return options

def dst_announce(msg):
    # add \ before ' in the message to prevent errors
    message = msg.replace('"', '').replace("'", "").replace(";", "").replace("(", "").replace(")", "")
    screen_cmd = f'screen -S s -X stuff "TheNet:SystemMessage(\'{message}\')^M"'
    subprocess.run(screen_cmd, shell=True)  # send the message to the screen session

def dst_player_list():
    surface_command = "local players = AllPlayers local announceStr = 'Players (Surface): ' for k, v in ipairs(players) do local name = v:GetDisplayName() announceStr = announceStr .. name if k ~= #players then announceStr = announceStr .. ', ' end end if announceStr == 'Players (Surface): ' then announceStr = 'There are no players on the surface.' end TheNet:SystemMessage(announceStr, false)"
    caves_command = "local players = AllPlayers local announceStr = 'Players (Caves): ' for k, v in ipairs(players) do local name = v:GetDisplayName() announceStr = announceStr .. name if k ~= #players then announceStr = announceStr .. ', ' end end if announceStr == 'Players (Caves): ' then announceStr = 'There are no players in the caves.' end TheNet:SystemMessage(announceStr, false)"
    screen_cmd = f'screen -S s -p 0 -X stuff "{surface_command}^M"'
    subprocess.run(screen_cmd, shell=True)
    screen_cmd = f'screen -S c -p 0 -X stuff "{caves_command}^M"'
    subprocess.run(screen_cmd, shell=True)