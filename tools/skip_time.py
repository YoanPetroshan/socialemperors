#!/usr/bin/env python3
"""Advance every timer in a village save by N minutes/hours at once.

    python tools/skip_time.py 2h
    python tools/skip_time.py 30m --user 5b8dd545
    python tools/skip_time.py 1d --dry-run

The game client decides when things are ready from stored timestamps (item[4] of every building, plus the
timestamp fields in privateState), so moving all of them back by N seconds is the same as N seconds
having passed. Values <= 0 mean "no timer" and are left alone. The server must be stopped.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import savelib

TIMESTAMP_KEY = re.compile(r"time.?stamp|last.?time|expirable", re.IGNORECASE)

def shift(value, seconds, counter):
    """Recursively moves timestamps (positive numbers) back, keeping 0/-1 markers."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        if value > 0:
            counter[0] += 1
            return max(value - seconds, 1)
        return value
    if isinstance(value, list):
        return [shift(v, seconds, counter) for v in value]
    if isinstance(value, dict):
        return {k: shift(v, seconds, counter) for k, v in value.items()}
    return value

def skip_time(save: dict, seconds: int) -> dict:
    counts = {"buildings": [0], "map fields": [0], "private state": [0]}
    for map in save["maps"]:
        for item in map["items"]:
            if len(item) > 4 and isinstance(item[4], (int, float)) and item[4] > 0:
                item[4] = max(item[4] - seconds, 1)
                counts["buildings"][0] += 1
        for key in list(map.keys()):
            if key != "items" and TIMESTAMP_KEY.search(key):
                map[key] = shift(map[key], seconds, counts["map fields"])
    private = save["privateState"]
    for key in list(private.keys()):
        if TIMESTAMP_KEY.search(key):
            private[key] = shift(private[key], seconds, counts["private state"])
    return {k: v[0] for k, v in counts.items()}

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("duration", help="e.g. 90s, 30m, 2h, 1d, 1h30m")
    parser.add_argument("--user", help="USERID (or its first characters); needed only if there are several saves")
    parser.add_argument("--dry-run", action="store_true", help="show what would change, write nothing")
    args = parser.parse_args()

    try:
        seconds = savelib.parse_duration(args.duration)
    except ValueError as e:
        sys.exit(str(e))
    if seconds <= 0:
        sys.exit("The duration must be positive.")

    savelib.require_server_stopped()
    path = savelib.pick_save(args.user)
    save = savelib.load(path)
    counts = skip_time(save, seconds)
    summary = ", ".join(f"{n} {name}" for name, n in counts.items())
    if args.dry_run:
        print(f"[dry run] would move {summary} back by {seconds}s in {os.path.basename(path)}")
        return
    bak = savelib.backup(path, "skip-time")
    savelib.save_atomic(path, save)
    print(f"Skipped {seconds}s ({args.duration}) in {os.path.basename(path)}: moved {summary}.")
    print(f"Backup: {bak}")

if __name__ == "__main__":
    main()
