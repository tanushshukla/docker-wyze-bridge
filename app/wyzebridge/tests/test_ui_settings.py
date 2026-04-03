from pathlib import Path

from wyzebridge.ui_settings import coerce_bool, load_ui_settings, save_ui_settings


def test_coerce_bool_handles_common_string_values():
    assert coerce_bool("true") is True
    assert coerce_bool("ON") is True
    assert coerce_bool("false", default=True) is False
    assert coerce_bool("0", default=True) is False


def test_load_ui_settings_uses_default_when_file_missing(tmp_path: Path):
    settings = load_ui_settings(
        path=tmp_path / "missing.json",
        default_live_preview=True,
    )

    assert settings == {"live_preview": True}


def test_save_and_load_ui_settings_round_trip(tmp_path: Path):
    settings_path = tmp_path / "ui_settings.json"

    saved = save_ui_settings(
        {"live_preview": "false"},
        path=settings_path,
        default_live_preview=True,
    )
    loaded = load_ui_settings(
        path=settings_path,
        default_live_preview=True,
    )

    assert saved == {"live_preview": False}
    assert loaded == {"live_preview": False}
