# ============================================================
# Storage – JSON-based config persistence
# ============================================================
import json
import os
import sys


CONFIG_FILE = "btc_bot_config.json"


def _get_config_path() -> str:
    """Get config file path next to the exe/script."""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, CONFIG_FILE)


def load_config() -> dict:
    """Load saved config. Returns empty dict if not found."""
    path = _get_config_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(data: dict):
    """Save config to JSON file."""
    path = _get_config_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Save config error: {e}")
