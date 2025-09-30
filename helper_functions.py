import requests
import subprocess
import shlex
import os
import forum_scraper as fs
import re
import json

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

def get_chat_root_world_path(cluster_name, beta):
    user_home = os.path.expanduser("~")
    if beta:
        return os.path.join(user_home, ".klei", "DoNotStarveTogetherBetaBranch", cluster_name)
    else:
        return os.path.join(user_home, ".klei", "DoNotStarveTogether", cluster_name)
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


def parse_modinfo(temp_path, id):
    modinfo_path = os.path.join(
        temp_path, "steamapps", "workshop", "content", "322330", id, "modinfo.lua"
    )
    if not os.path.exists(modinfo_path):
        return None

    with open(modinfo_path, 'r', encoding='utf-8') as f:
        content = f.read()

    config_block_match = re.search(
        r'configuration_options\s*=\s*\{(.*?)\}', content, re.DOTALL
    )
    if not config_block_match:
        return None

    config_block = config_block_match.group(1)

    entry_pattern = re.compile(
        r'\{[^}]*?name\s*=\s*["\']?([^,"\'\s]+)["\']?,.*?default\s*=\s*([^,}]+)',
        re.DOTALL,
    )

    options = []
    for match in entry_pattern.finditer(config_block):
        name = match.group(1)
        default = match.group(2).strip()
        if default.lower() == "true":
            default_val = "true"
        elif default.lower() == "false":
            default_val = "false"
        else:
            try:
                int_val = int(default)
                default_val = str(int_val)
            except ValueError:
                default_val = '"' + default.strip('"').strip("'") + '"'
        if name.isidentifier():
            options.append(f"  {name}={default_val},")
        else:
            options.append(f'  ["{name}"]={default_val},')

    output = "configuration_options={\n" + "\n".join(options) + "\n}\n"
    return output


def update_enabled_mods(cluster_name, is_beta_server, mod_id, mod_config, enabled):
    enabledmods_path = os.path.join(
        get_chat_root_world_path(cluster_name, is_beta_server),
        "enabledmods.json"
    )
    mods_dict = {}
    if os.path.exists(enabledmods_path):
        with open(enabledmods_path, 'r', encoding='utf-8') as f:
            try:
                mods_dict = json.load(f)
            except Exception:
                mods_dict = {}

    if mod_id in mods_dict:
        # Only update "enabled" and keep the same config
        mods_dict[mod_id]["enabled"] = enabled
    else:
        # Add new entry (must provide config)
        if mod_config is None:
            mod_config = {}
        mods_dict[mod_id] = {
            "configuration_options": mod_config,
            "enabled": enabled
        }
    # Write as pretty-printed JSON, sorted keys for consistency
    with open(enabledmods_path, 'w', encoding='utf-8') as f:
        json.dump(mods_dict, f, indent=2, sort_keys=True)


def has_mod_config(cluster_name, is_beta_server, mod_id):
    enabledmods_path = os.path.join(
        get_chat_root_world_path(cluster_name, is_beta_server),
        "enabledmods.json"
    )
    if not os.path.exists(enabledmods_path):
        return False

    try:
        with open(enabledmods_path, 'r', encoding='utf-8') as f:
            mods_dict = json.load(f)
    except Exception:
        return False

    if mod_id in mods_dict and mods_dict[mod_id].get("configuration_options") is not None:
        return True
    return False

def format_mods_lua(mods_dict):
    def format_lua_table(d, indent=0):
        spaces = '  ' * indent
        lines = ['{']
        for key, value in d.items():
            if isinstance(key, str) and (not key.isidentifier() or ' ' in key):
                k_str = f'["{key}"]'
            else:
                k_str = str(key)
            if isinstance(value, dict):
                v_str = format_lua_table(value, indent + 1)
            elif isinstance(value, str):
                v_str = f'"{value}"'
            elif isinstance(value, bool):
                v_str = 'true' if value else 'false'
            else:
                v_str = str(value)
            lines.append(f'{spaces}  {k_str}={v_str},')
        lines.append(f'{spaces}}}')
        return '\n'.join(lines)
    
    out_lines = ['return {']
    for mod_id, obj in mods_dict.items():
        lua_id = f"workshop-{mod_id}"
        config_str = format_lua_table(obj)
        out_lines.append(f'  ["{lua_id}"]={config_str},')
    out_lines.append('}')
    return '\n'.join(out_lines)


def create_modoverrides(cluster_name, is_beta_server):
    enabledmods_path = os.path.join(
        get_chat_root_world_path(cluster_name, is_beta_server),
        "enabledmods.json"
    )
    
    if not os.path.exists(enabledmods_path):
        return False

    try:
        with open(enabledmods_path, 'r', encoding='utf-8') as f:
            mods_dict = json.load(f)
    except Exception:
        return False
    
    lua_string = format_mods_lua(mods_dict)
    
    master_modoverrides_path = os.path.join(
        get_chat_root_world_path(cluster_name, is_beta_server),
        "Master",
        "modoverrides.lua"
    )
    try:
        with open(master_modoverrides_path, 'w', encoding='utf-8') as f:
            f.write(lua_string)
    except Exception:
        return False
    
    caves_modoverrides_path = os.path.join(
        get_chat_root_world_path(cluster_name, is_beta_server),
        "Caves",
        "modoverrides.lua"
    )
    try:
        with open(caves_modoverrides_path, 'w', encoding='utf-8') as f:
            f.write(lua_string)
    except Exception:
        return False
