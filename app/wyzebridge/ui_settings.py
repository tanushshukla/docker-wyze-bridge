import json
from pathlib import Path


DEFAULT_UI_SETTINGS_PATH = Path("/config/ui_settings.json")


def coerce_bool(value: object, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off", ""}:
            return False
    return default


def load_ui_settings(
    path: Path = DEFAULT_UI_SETTINGS_PATH,
    default_live_preview: bool = False,
) -> dict[str, bool]:
    default_settings = {"live_preview": default_live_preview}
    try:
        with path.open("r") as f:
            loaded = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default_settings

    if not isinstance(loaded, dict):
        return default_settings

    return {
        "live_preview": coerce_bool(
            loaded.get("live_preview"),
            default=default_live_preview,
        )
    }


def save_ui_settings(
    settings: dict[str, object],
    path: Path = DEFAULT_UI_SETTINGS_PATH,
    default_live_preview: bool = False,
) -> dict[str, bool]:
    normalized = {
        "live_preview": coerce_bool(
            settings.get("live_preview"),
            default=default_live_preview,
        )
    }
    with path.open("w") as f:
        json.dump(normalized, f)
    return normalized
