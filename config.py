# config.py
import os
from pathlib import Path
from key import *

# Key
KEY = key_tBot

# ------------- Paths -------------
HOME_DIR = os.path.expanduser("~")

# Main dirs
FALL_BOT_DIR = Path(HOME_DIR) / "fall.bot"
SCRIPTS_DIR = FALL_BOT_DIR / "scripts"
INFO_DIR = FALL_BOT_DIR / "info"
TEMP_DIR = FALL_BOT_DIR / "temp"

# Script paths
START_SERVER_SCRIPT = SCRIPTS_DIR / "start_server.sh"
STOP_SERVER_SCRIPT = SCRIPTS_DIR / "stop_server.sh"
RESTART_SERVER_SCRIPT = SCRIPTS_DIR / "restart_server.sh"
MAKE_NEW_WORLD_SCRIPT = SCRIPTS_DIR / "make_new_world.sh"
BACKUP_SCRIPT = SCRIPTS_DIR / "backup.sh"
DOWNLOAD_MOD_SCRIPT = SCRIPTS_DIR / "download_mod.sh"

# DST-related dirs
KLEI_ROOT = Path(HOME_DIR) / ".klei"
DST_DEDICATED_SERVER_DIR = Path(HOME_DIR) / "dontstarvetogether_dedicated_server"
MODS_DIR = DST_DEDICATED_SERVER_DIR / "mods"


CHAT_LOG_CHANNEL_ID = chat_log_channel_id if KEY == key_fallBot else test_channel_id
CURRENT_SERVER_ID = server_id if KEY == key_fallBot else server_id
ALLOWED_SERVERS = [server_id, test_id]
