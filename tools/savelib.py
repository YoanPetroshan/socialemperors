"""Shared helpers for the save-editing tools (skip_time.py, cheat.py).

Saves live in saves/<USERID>.save.json. The server keeps every save in memory and rewrites the file
after each command, so the tools refuse to run while the server is up.
"""
import json
import os
import shutil
import socket
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVES_DIR = os.path.join(ROOT, "saves")
BACKUPS_DIR = os.path.join(ROOT, "backups")
SERVER_HOST, SERVER_PORT = "127.0.0.1", 5050
KEEP_MANUAL_BACKUPS = 30

def server_running() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((SERVER_HOST, SERVER_PORT)) == 0

def require_server_stopped() -> None:
    if server_running():
        sys.exit(f"The server is running on {SERVER_HOST}:{SERVER_PORT}. Stop it first (Ctrl+C in its terminal, or ./stop.sh), "
                 "otherwise it will overwrite the changes.")

def list_saves() -> list:
    if not os.path.isdir(SAVES_DIR):
        return []
    return sorted(f for f in os.listdir(SAVES_DIR) if f.endswith(".save.json"))

def pick_save(user: str = None) -> str:
    """Returns the path of the save selected by USERID (or a prefix of it); the only save if none is given."""
    saves = list_saves()
    if not saves:
        sys.exit(f"No saves found in {SAVES_DIR}.")
    if user:
        matches = [f for f in saves if f.startswith(user)]
        if len(matches) != 1:
            sys.exit(f"--user '{user}' matches {len(matches)} saves: {', '.join(saves)}")
        return os.path.join(SAVES_DIR, matches[0])
    if len(saves) > 1:
        sys.exit("Several saves exist, pick one with --user:\n  " + "\n  ".join(saves))
    return os.path.join(SAVES_DIR, saves[0])

def load(path: str) -> dict:
    with open(path) as f:
        return json.load(f)

def backup(path: str, reason: str) -> str:
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    dest = os.path.join(BACKUPS_DIR, f"{os.path.basename(path)}.{stamp}.{reason}.bak")
    n = 1
    while os.path.exists(dest):  # several edits within one second must not overwrite each other
        n += 1
        dest = os.path.join(BACKUPS_DIR, f"{os.path.basename(path)}.{stamp}.{reason}-{n}.bak")
    shutil.copy2(path, dest)
    manual = sorted(f for f in os.listdir(BACKUPS_DIR) if f.endswith(".bak"))
    for old in manual[:-KEEP_MANUAL_BACKUPS]:
        os.remove(os.path.join(BACKUPS_DIR, old))
    return dest

def save_atomic(path: str, data: dict) -> None:
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=4)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise

def parse_duration(text: str) -> int:
    """'90s', '30m', '2h', '1d', '1h30m' or a plain number of seconds -> seconds."""
    units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    text = text.strip().lower()
    if text.isdigit():
        return int(text)
    total, number = 0, ""
    for ch in text:
        if ch.isdigit() or ch == ".":
            number += ch
        elif ch in units and number:
            total += float(number) * units[ch]
            number = ""
        else:
            raise ValueError(f"Bad duration '{text}' (examples: 90s, 30m, 2h, 1d, 1h30m)")
    if number:
        raise ValueError(f"Bad duration '{text}' (missing unit)")
    return int(total)
