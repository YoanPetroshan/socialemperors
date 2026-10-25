"""Soul Mixer support (clients 1.1.5 and 1.4.07; 0.9.26b has no Soul Mixer code at all).

What the client does (found by decompiling PopupSoulMixer / BuildingQueueManager / BuildingQueueData):
  * Two units are pushed into the building (existing push_unit command, stored in item[6]).
  * The result unit is chosen *in the client*: every unit with breeding_order > 0 has a "power";
    result power ~ 0.3*weaker + 0.7*stronger + random(0..11), then the first unit with at least that power.
  * "Start mixing" sends push_queue_unit; the client counts sm_training_time seconds. The queue state is
    restored on load from privateState.barracksQueues[<bq id>] = {ts, amount, unit} and the building's
    item[7]["bq"] = <bq id>.
  * "Get unit" sends pop_queue_unit with the tile where the unit appears.
  * Power-ups cost cash (globals.SOUL_MIXER_POWERUPS_LEVELS) and are reported with buy_powerups.

The original server's data for this is lost, so the numbers here are our own: breeding_order is the rank
of a unit by strength, sm_training_time grows with it.
"""
import math
import time

def timestamp_now() -> int:  # same as engine.timestamp_now (engine imports the config, which imports this)
    return int(time.time())

SOUL_MIXER_ID = 1529
CAPACITY = 2
SPEED_UP_COST_PER_HOUR = 1  # Config.COST_SPEED_UP_UNIT_QUEUE in the client

POWERUPS = [  # cash_cost: cash for the n-th power-up; order_increment: how many strength ranks it adds
    {"cash_cost": 5, "order_increment": 5},
    {"cash_cost": 10, "order_increment": 8},
    {"cash_cost": 20, "order_increment": 12},
    {"cash_cost": 40, "order_increment": 18},
]

STRINGS = {  # ids come from the client's Language class (SOUL_MIXER_*)
    1615: ("SOUL_MIXER_SUB_TITLE", "Mix two units into a stronger one"),
    1616: ("SOUL_MIXER_NO_SOUL", "No unit selected"),
    1617: ("SOUL_MIXER_CHOOSE_SOULS", "Choose two units to mix"),
    1618: ("SOUL_MIXER_SELECT_UNIT", "Select unit"),
    1619: ("SOUL_MIXER_POWERUP", "Power up"),
    1620: ("SOUL_MIXER_START_MIXING", "Start mixing"),
    1621: ("SOUL_MIXER_SPEED_UP", "Speed up"),
    1622: ("SOUL_MIXER_REMAINING_TIME", "Remaining time"),
    1623: ("SOUL_MIXER_HELP_1", "Pick two of your units. The mixer combines them into a new, stronger unit."),
    1624: ("SOUL_MIXER_HELP_2", "The result depends on the strength of both units, plus a little luck."),
    1625: ("SOUL_MIXER_HELP_3", "Mixing takes time. Use cash to speed it up."),
    1626: ("SOUL_MIXER_HELP_4", "Power-ups use cash to get a stronger result."),
    1627: ("SOUL_MIXER_WARNING_POWERUPS", "Changing the units will lose your power-ups. Continue?"),
    1628: ("SOUL_MIXER_GET_UNIT", "Get unit"),
    1629: ("SOUL_MIXER_WARNING_CROSS_PROMOTION", "This unit cannot be mixed yet."),
}

def _num(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0

def augment_config(config: dict) -> None:
    """Adds the data the client expects for the Soul Mixer to the (server-side) game config, in place."""
    units = [i for i in config["items"] if i.get("type") == "u" and _num(i.get("attack")) > 0 and _num(i.get("life")) > 0]
    units.sort(key=lambda i: (_num(i["life"]) + 8 * _num(i["attack"]), int(i["id"])))
    for rank, unit in enumerate(units, start=1):
        unit["breeding_order"] = str(rank)
        unit["sm_training_time"] = str(120 + 10 * rank)  # 2 min .. about 2 h for the strongest
    for item in config["items"]:
        if str(item["id"]) == str(SOUL_MIXER_ID):
            item["unit_capacity"] = str(CAPACITY)
    config["globals"]["SOUL_MIXER_POWERUPS_LEVELS"] = POWERUPS
    known = {int(e["id"]) for e in config["localization_strings"] if isinstance(e, dict) and "id" in e}
    for string_id, (name, text) in STRINGS.items():
        if string_id not in known:
            config["localization_strings"].append({"id": string_id, "name": name, "text": text})

# --- commands (only for the Soul Mixer building; other buildings' queues are left as they were) ---

def _find_building(map: dict, building_id, x, y):
    for item in map["items"]:
        if item[0] == building_id and item[1] == x and item[2] == y:
            return item
    return None

def _queues(save: dict) -> dict:
    return save["privateState"].setdefault("barracksQueues", {})

def _training_time(config_items_by_id: dict, unit_id) -> int:
    unit = config_items_by_id.get(int(unit_id), {})
    return int(_num(unit.get("sm_training_time")) or 120)

def push_queue_unit(save: dict, args: list) -> bool:
    x, y, building_id, unit_id, bq = args[0], args[1], args[2], args[3], args[4]
    if int(building_id) != SOUL_MIXER_ID:
        return False
    building = _find_building(save["maps"][0], building_id, x, y)
    if building is None:
        return True
    while len(building) < 8:  # [id, x, y, orientation, ts, level, units, attributes]
        building.append([] if len(building) == 6 else {})
    building[7]["bq"] = str(bq)
    queue = _queues(save).get(str(bq))
    if not queue or queue.get("amount", 0) <= 0:
        _queues(save)[str(bq)] = {"ts": timestamp_now(), "amount": 1, "unit": int(unit_id)}
    else:
        queue["amount"] += 1
    return True

def pop_queue_unit(save: dict, args: list) -> bool:
    bq, x, y, building_id = args[0], args[1], args[2], args[3]
    if int(building_id) != SOUL_MIXER_ID:
        return False
    queue = _queues(save).get(str(bq))
    if not queue:
        return True
    save["maps"][0]["items"].append([queue["unit"], x, y, 0, timestamp_now(), 0])  # the new unit
    queue["amount"] -= 1
    if queue["amount"] <= 0:
        del _queues(save)[str(bq)]
    else:
        queue["ts"] = timestamp_now()
    return True

def unqueue_unit(save: dict, args: list) -> bool:
    bq, building_id = args[0], args[1]
    if int(building_id) != SOUL_MIXER_ID:
        return False
    queue = _queues(save).get(str(bq))
    if queue:
        queue["amount"] -= 1
        if queue["amount"] <= 0:
            del _queues(save)[str(bq)]
    return True

def speed_up_queue(save: dict, args: list, items_by_id: dict) -> bool:
    queue = _queues(save).get(str(args[0]))
    if not queue or not _is_soul_mixer_queue(save, args[0]):
        return False
    seconds = _training_time(items_by_id, queue["unit"])
    remaining = max(0, queue["ts"] + seconds - timestamp_now()) + (queue["amount"] - 1) * seconds
    cost = math.ceil(remaining / 3600) * SPEED_UP_COST_PER_HOUR
    save["playerInfo"]["cash"] = max(save["playerInfo"]["cash"] - cost, 0)
    queue["ts"] = timestamp_now() - 10 ** 6  # long finished, whatever TIME_SCALE is in use
    return True

def buy_powerups(save: dict, args: list) -> bool:
    level = max(0, min(int(args[0]), len(POWERUPS) - 1))
    save["playerInfo"]["cash"] = max(save["playerInfo"]["cash"] - POWERUPS[level]["cash_cost"], 0)
    return True

def _is_soul_mixer_queue(save: dict, bq) -> bool:
    return any(item[0] == SOUL_MIXER_ID and len(item) > 7 and item[7].get("bq") == str(bq)
               for item in save["maps"][0]["items"])
