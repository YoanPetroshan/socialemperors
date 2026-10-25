#!/usr/bin/env python3
"""Edit a village save (offline). Backs the save up before every change and refuses to run while the
server is up (it would overwrite the edit).

    python tools/cheat.py show
    python tools/cheat.py add gold 100000
    python tools/cheat.py set cash 500
    python tools/cheat.py rich                    # 1 000 000 of every resource, 1000 cash
    python tools/cheat.py level max               # or: level 40
    python tools/cheat.py items dragon            # search items/units by name or id
    python tools/cheat.py give 74 5               # 5x item/unit id 74 into the storage inventory
    python tools/cheat.py skip-tutorial

Resources: gold (=coins), wood, stone, food, xp, cash, mana, potion.
"""
import argparse
import contextlib
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import savelib
import cheats

def game_config():
    os.chdir(savelib.ROOT)  # the config loader uses paths relative to the project root
    with contextlib.redirect_stdout(io.StringIO()):
        from get_game_config import get_game_config
        return get_game_config()

def print_summary(save):
    for key, value in cheats.summary(save).items():
        print(f"  {key:>16}: {value}")

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--user", help="USERID (or its first characters); needed only if there are several saves")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("show", help="print the save's resources and level")
    for name in ("add", "set"):
        p = sub.add_parser(name, help=f"{name} a resource")
        p.add_argument("resource", choices=sorted(cheats.RESOURCES))
        p.add_argument("amount", type=int)
    sub.add_parser("rich", help="1 000 000 of every resource and 1000 cash")
    p = sub.add_parser("level", help="set level (and matching XP)")
    p.add_argument("level", help="a number or 'max'")
    p = sub.add_parser("items", help="search items/units by name or id")
    p.add_argument("query")
    p = sub.add_parser("give", help="put items/units into the storage inventory")
    p.add_argument("item_id", type=int)
    p.add_argument("count", type=int, nargs="?", default=1)
    sub.add_parser("skip-tutorial", help="mark the tutorial as completed")
    args = parser.parse_args()

    if args.cmd == "items":  # read-only, works with the server running
        for item in cheats.find_items(game_config()["items"], args.query):
            print(f"  {item['id']:>5}  {item['name']:<28} type={item.get('type')}  min_level={item.get('min_level')}")
        return

    if args.cmd != "show":
        savelib.require_server_stopped()
    path = savelib.pick_save(args.user)
    save = savelib.load(path)

    if args.cmd == "show":
        print(os.path.basename(path))
        print_summary(save)
        return

    cfg = game_config()
    if args.cmd == "add":
        print(f"{args.resource}: -> {cheats.add_resource(save, args.resource, args.amount)}")
    elif args.cmd == "set":
        print(f"{args.resource}: -> {cheats.set_resource(save, args.resource, args.amount)}")
    elif args.cmd == "rich":
        for res in ("gold", "wood", "stone", "food"):
            cheats.set_resource(save, res, 1_000_000)
        cheats.set_resource(save, "cash", 1000)
    elif args.cmd == "level":
        target = cheats.max_level(cfg["levels"]) if args.level == "max" else int(args.level)
        print(f"level: -> {cheats.set_level(save, cfg['levels'], target)}")
    elif args.cmd == "give":
        item = cheats.find_items(cfg["items"], str(args.item_id))
        if not item:
            sys.exit(f"No item with id {args.item_id}. Search with: tools/cheat.py items <name>")
        total = cheats.give_item(save, args.item_id, args.count)
        print(f"{item[0]['name']} (id {args.item_id}): {total} in storage")
    elif args.cmd == "skip-tutorial":
        cheats.skip_tutorial(save)

    bak = savelib.backup(path, args.cmd)
    savelib.save_atomic(path, save)
    print(f"Saved. Backup: {bak}")
    print_summary(save)

if __name__ == "__main__":
    main()
