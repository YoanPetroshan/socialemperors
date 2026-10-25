"""Save-editing helpers shared by tools/cheat.py (offline) and the local cheat panel (running server).

All functions work on a loaded save dict (see sessions.py): resources live in save["maps"][0]
(coins = gold, wood, stone, food, xp, level), cash in save["playerInfo"]["cash"], mana/potion in
save["privateState"], and placeable items/units in save["privateState"]["gifts"][item_id] (the storage
inventory the player can place from).
"""

MAX_VALUE = 1_000_000_000  # the Flash client uses 32-bit ints

# name -> (section, key). "gold" and "coins" are the same thing.
RESOURCES = {
    "gold": ("map", "coins"),
    "coins": ("map", "coins"),
    "wood": ("map", "wood"),
    "stone": ("map", "stone"),
    "food": ("map", "food"),
    "xp": ("map", "xp"),
    "cash": ("playerInfo", "cash"),
    "mana": ("privateState", "mana"),
    "potion": ("privateState", "potion"),
}

def _section(save: dict, section: str) -> dict:
    return save["maps"][0] if section == "map" else save[section]

def get_resource(save: dict, name: str) -> int:
    section, key = RESOURCES[name]
    return _section(save, section)[key]

def set_resource(save: dict, name: str, value: int) -> int:
    if name not in RESOURCES:
        raise ValueError(f"Unknown resource '{name}'. Valid: {', '.join(sorted(RESOURCES))}")
    value = max(0, min(int(value), MAX_VALUE))
    section, key = RESOURCES[name]
    _section(save, section)[key] = value
    if name == "xp":
        sync_level_with_xp(save)
    return value

def add_resource(save: dict, name: str, amount: int) -> int:
    if name not in RESOURCES:
        raise ValueError(f"Unknown resource '{name}'. Valid: {', '.join(sorted(RESOURCES))}")
    return set_resource(save, name, get_resource(save, name) + int(amount))

def sync_level_with_xp(save: dict) -> None:
    from get_game_config import get_level_from_xp
    level = get_level_from_xp(save["maps"][0]["xp"])
    save["maps"][0]["level"] = level
    save["playerInfo"]["level"] = level
    save["playerInfo"]["xp"] = save["maps"][0]["xp"]

def max_level(levels: list) -> int:
    return len(levels) - 1

def set_level(save: dict, levels: list, level: int) -> int:
    """Sets the level and the matching XP. `levels` is game_config["levels"]."""
    level = max(0, min(int(level), max_level(levels)))
    xp = int(levels[level]["exp_required"])
    save["maps"][0]["level"] = level
    save["maps"][0]["xp"] = xp
    save["playerInfo"]["level"] = level
    save["playerInfo"]["xp"] = xp
    return level

def give_item(save: dict, item_id: int, count: int = 1) -> int:
    """Puts `count` of an item/unit into the storage inventory. Returns the new count."""
    item_id, count = int(item_id), int(count)
    gifts = save["privateState"]["gifts"]
    if len(gifts) <= item_id:
        gifts.extend([0] * (item_id - len(gifts) + 1))
    gifts[item_id] = max(0, gifts[item_id] + count)
    while gifts and gifts[-1] == 0:  # the game keeps no trailing zeros
        gifts.pop()
    return gifts[item_id] if item_id < len(gifts) else 0

def skip_tutorial(save: dict) -> None:
    save["playerInfo"]["completed_tutorial"] = 1
    save["privateState"]["dragonNestActive"] = 1

def find_items(items: list, query: str, limit: int = 40) -> list:
    """Items whose id equals the query or whose name contains it (case-insensitive)."""
    q = query.strip().lower()
    found = [i for i in items if str(i["id"]) == q or q in str(i.get("name", "")).lower()]
    return found[:limit]

def summary(save: dict) -> dict:
    m = save["maps"][0]
    return {
        "name": save["playerInfo"]["map_names"][save["playerInfo"]["default_map"]],
        "level": m["level"], "xp": m["xp"],
        "gold": m["coins"], "wood": m["wood"], "stone": m["stone"], "food": m["food"],
        "cash": save["playerInfo"]["cash"],
        "mana": save["privateState"]["mana"], "potion": save["privateState"]["potion"],
        "items placed": len(m["items"]), "items in storage": sum(save["privateState"]["gifts"]),
    }
