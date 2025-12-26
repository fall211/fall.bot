# state.py
import json
import os
from pathlib import Path
from key import key_tBot, key_fallBot

STATE_FILE = Path("data/server_state.json")

DEFAULT_STATE = {
    "current_cluster": "Template",
    "is_beta": False,
    "game_version": 500000,
    "beta_game_version": 500000
}

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError:
            pass
    return DEFAULT_STATE.copy()

def save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))
