import json
import os

TIME_SCALE_FILE = "time_scale.json"

def get_time_scale() -> float:
    """Game speed multiplier: >1 faster, <1 slower. TIME_SCALE env var wins over time_scale.json; default 1.0."""
    raw = os.environ.get("TIME_SCALE")
    if raw is None and os.path.exists(TIME_SCALE_FILE):
        try:
            raw = json.load(open(TIME_SCALE_FILE)).get("time_scale")
        except (ValueError, OSError):
            print(f" [!] Could not read {TIME_SCALE_FILE}, using 1.0")
    try:
        scale = float(raw) if raw is not None else 1.0
    except ValueError:
        print(f" [!] Invalid TIME_SCALE '{raw}', using 1.0")
        return 1.0
    if scale <= 0:
        print(f" [!] TIME_SCALE must be > 0 (got {scale}), using 1.0")
        return 1.0
    return scale
