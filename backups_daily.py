import os
import shutil
import threading
import time

from bundle import SAVES_DIR, BASE_DIR

DAILY_DIR = os.path.join(BASE_DIR, "backups", "daily")
KEEP_DAYS = 7

def daily_backup() -> None:
    """Copies saves/ to backups/daily/YYYY-MM-DD/ once a day and keeps the newest KEEP_DAYS days."""
    if not os.path.isdir(SAVES_DIR):
        return
    today = os.path.join(DAILY_DIR, time.strftime("%Y-%m-%d"))
    if not os.path.exists(today):
        os.makedirs(today)
        for file in os.listdir(SAVES_DIR):
            if file.endswith(".save.json"):
                shutil.copy2(os.path.join(SAVES_DIR, file), today)
        print(f" [+] Daily backup of saves -> {today}")
    days = sorted(d for d in os.listdir(DAILY_DIR) if os.path.isdir(os.path.join(DAILY_DIR, d)))
    for old in days[:-KEEP_DAYS]:
        shutil.rmtree(os.path.join(DAILY_DIR, old))
        print(f" [+] Removed old backup {old}")

def start_daily_backups() -> None:
    """Backs up now, then re-checks every hour (a new day triggers a new backup)."""
    def loop():
        while True:
            try:
                daily_backup()
            except OSError as e:
                print(f" [!] Daily backup failed: {e}")
            time.sleep(3600)
    threading.Thread(target=loop, daemon=True).start()
