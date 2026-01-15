import json
import os
from pathlib import Path
import re
import subprocess

import discord
import requests

from config import DST_BETA_SAVES_DIR, DST_SAVES_DIR
from utils import forum_scraper as fs


# ***************** General Use Functions *****************
def get_chat_log_path(cluster_name, beta=False):
    if beta:
        return DST_BETA_SAVES_DIR / cluster_name / "Master" / "server_chat_lot.txt"
    else:
        return DST_SAVES_DIR / cluster_name / "Master" / "server_chat_lot.txt"


def get_server_log_path(cluster_name, beta=False) -> Path:
    if beta:
        return DST_BETA_SAVES_DIR / cluster_name / "Master" / "server_lot.txt"
    else:
        return DST_SAVES_DIR / cluster_name / "Master" / "server_lot.txt"


def get_vm_info():
    # get the server's public IP address
    ip = requests.get("https://api.ipify.org").text
    return ip


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
    f = open(path, "rb")
    len = sum(1 for i in f)
    f.close()
    return len


def get_cluster_options(is_beta_server: bool):
    path = DST_BETA_SAVES_DIR if is_beta_server else DST_SAVES_DIR
    options = []

    for entry in path.iterdir():
        if not entry.is_dir():
            continue
        if entry.name == "Template":
            continue

        selection = discord.SelectOption(
            label=entry.name,
            value=entry.name
        )
        options.append(selection)

    if options.count == 0:
        failsafe = discord.SelectOption(
            label="No clusters found!",
            value="nullfailsafe"
        )
        options.append(failsafe)

    return options


def dst_announce(msg):
    # add \ before ' in the message to prevent errors
    message = (
        msg.replace('"', "")
        .replace("'", "")
        .replace(";", "")
        .replace("(", "")
        .replace(")", "")
    )
    screen_cmd = f"screen -S s -X stuff \"TheNet:SystemMessage('{message}')^M\""
    subprocess.run(screen_cmd, shell=True)  # send the message to the screen session


def dst_player_list():
    surface_command = "local players = AllPlayers local announceStr = 'Players (Surface): ' for k, v in ipairs(players) do local name = v:GetDisplayName() announceStr = announceStr .. name if k ~= #players then announceStr = announceStr .. ', ' end end if announceStr == 'Players (Surface): ' then announceStr = 'There are no players on the surface.' end TheNet:SystemMessage(announceStr, false)"
    caves_command = "local players = AllPlayers local announceStr = 'Players (Caves): ' for k, v in ipairs(players) do local name = v:GetDisplayName() announceStr = announceStr .. name if k ~= #players then announceStr = announceStr .. ', ' end end if announceStr == 'Players (Caves): ' then announceStr = 'There are no players in the caves.' end TheNet:SystemMessage(announceStr, false)"
    screen_cmd = f'screen -S s -p 0 -X stuff "{surface_command}^M"'
    subprocess.run(screen_cmd, shell=True)
    screen_cmd = f'screen -S c -p 0 -X stuff "{caves_command}^M"'
    subprocess.run(screen_cmd, shell=True)
